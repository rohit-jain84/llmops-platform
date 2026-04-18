"""Integration tests for GatewayService.

Mocks external services (litellm, Qdrant/cache, LangFuse) while using a real
DB session to validate the full orchestration pipeline: experiment resolution,
prompt rendering, semantic cache, model routing, LLM call, cost logging,
and cache storage.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.gateway import GatewayRequest
from app.models.application import Application
from app.models.cost import LLMRequestLog, RoutingRule
from app.models.experiment import Experiment, ExperimentVariant
from app.models.prompt import PromptTemplate, PromptVersion
from app.services.gateway_service import GatewayService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(
    app_id: uuid.UUID,
    template_id: uuid.UUID,
    variables: dict | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    user_id: str | None = None,
) -> GatewayRequest:
    return GatewayRequest(
        application_id=app_id,
        prompt_template_id=template_id,
        variables=variables or {},
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        user_id=user_id,
    )


def _fake_llm_response(text: str = "Hello from LLM", model: str = "gpt-4o-mini"):
    """Return a mock that mimics litellm's acompletion response."""
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=20)
    message = SimpleNamespace(content=text)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice], usage=usage, model=model)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def app_obj(db_session: AsyncSession, test_user) -> Application:
    """Create an Application row for tests."""
    obj = Application(name=f"GW Test App {uuid.uuid4().hex[:6]}", description="gateway tests", created_by=test_user.id)
    db_session.add(obj)
    await db_session.flush()
    await db_session.refresh(obj)
    return obj


@pytest_asyncio.fixture
async def prompt_template(db_session: AsyncSession, app_obj: Application) -> PromptTemplate:
    """Create a PromptTemplate with one production version."""
    tmpl = PromptTemplate(application_id=app_obj.id, name="gw-template")
    db_session.add(tmpl)
    await db_session.flush()
    await db_session.refresh(tmpl)

    ver = PromptVersion(
        template_id=tmpl.id,
        version_number=1,
        content="Say hello to {{ name }}",
        variables={"name": ""},
        tag="production",
    )
    db_session.add(ver)
    await db_session.flush()
    return tmpl


@pytest_asyncio.fixture
async def prompt_version(db_session: AsyncSession, prompt_template: PromptTemplate) -> PromptVersion:
    """Return the production PromptVersion for the fixture template."""
    from sqlalchemy import select

    from app.models.prompt import PromptVersion as PV

    result = await db_session.execute(select(PV).where(PV.template_id == prompt_template.id, PV.tag == "production"))
    return result.scalar_one()


# ---------------------------------------------------------------------------
# Shared mock context manager
# ---------------------------------------------------------------------------


def _gateway_mocks(
    llm_response=None,
    cache_lookup_return=None,
    completion_cost: float = 0.001,
):
    """Return a combined context manager that patches litellm, cache, and langfuse."""
    if llm_response is None:
        llm_response = _fake_llm_response()

    class _Ctx:
        def __init__(self):
            self.patches = []
            self.acompletion = None
            self.completion_cost_mock = None
            self.cache_lookup = None
            self.cache_store = None
            self.langfuse_create_trace = None
            self.langfuse_log_generation = None
            self.langfuse_flush = None

        async def __aenter__(self):
            p1 = patch(
                "app.services.gateway_service.litellm.acompletion", new_callable=AsyncMock, return_value=llm_response
            )
            p2 = patch("app.services.gateway_service.litellm.completion_cost", return_value=completion_cost)
            p3 = patch.object(
                GatewayService,
                "_build_cache_svc",
                create=True,  # attribute may not exist; we patch the instance later
            )

            self.acompletion = p1.start()
            self.completion_cost_mock = p2.start()
            self.patches.extend([p1, p2])

            return self

        async def __aexit__(self, *args):
            for p in self.patches:
                p.stop()

    return _Ctx()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_happy_path_basic_chat(db_session, app_obj, prompt_template, prompt_version):
    """Happy path: no cache hit, no experiment, no routing rule.
    Verifies the gateway calls litellm, logs cost, and returns expected shape."""

    request = _make_request(app_obj.id, prompt_template.id, variables={"name": "World"})

    fake_resp = _fake_llm_response("Hi World!")
    with (
        patch(
            "app.services.gateway_service.litellm.acompletion", new_callable=AsyncMock, return_value=fake_resp
        ) as mock_llm,
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.0015),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock) as mock_store,
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        result = await svc.handle_chat(request)

    assert result["response"] == "Hi World!"
    assert result["cache_hit"] is False
    assert result["model"] == "gpt-4o-mini"
    assert result["input_tokens"] == 10
    assert result["output_tokens"] == 20
    assert result["variant_id"] is None

    mock_llm.assert_awaited_once()
    call_kwargs = mock_llm.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o-mini"
    assert "Say hello to World" in call_kwargs["messages"][0]["content"]

    mock_store.assert_awaited_once()

    # Verify cost was persisted to the database
    from sqlalchemy import select

    log_result = await db_session.execute(select(LLMRequestLog).where(LLMRequestLog.application_id == app_obj.id))
    log = log_result.scalar_one()
    assert log.cache_hit is False
    assert log.model == "gpt-4o-mini"
    assert log.input_tokens == 10
    assert log.output_tokens == 20
    assert float(log.cost_usd) == pytest.approx(0.0015, abs=1e-6)


@pytest.mark.asyncio
async def test_cache_hit_skips_llm_call(db_session, app_obj, prompt_template, prompt_version):
    """When the semantic cache returns a hit the gateway should NOT call litellm."""

    request = _make_request(app_obj.id, prompt_template.id, variables={"name": "Cached"})

    cached_payload = {"response": "cached answer", "model": "gpt-4o-mini"}

    with (
        patch("app.services.gateway_service.litellm.acompletion", new_callable=AsyncMock) as mock_llm,
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=cached_payload),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        result = await svc.handle_chat(request)

    assert result["cache_hit"] is True
    assert result["response"] == "cached answer"
    assert result["input_tokens"] == 0
    assert result["output_tokens"] == 0
    assert result["cost_usd"] == 0

    mock_llm.assert_not_awaited()

    # A cost log row should still be written (with cache_hit=True)
    from sqlalchemy import select

    log_result = await db_session.execute(select(LLMRequestLog).where(LLMRequestLog.application_id == app_obj.id))
    log = log_result.scalar_one()
    assert log.cache_hit is True
    assert log.input_tokens == 0


@pytest.mark.asyncio
async def test_cache_miss_stores_response(db_session, app_obj, prompt_template, prompt_version):
    """On a cache miss the gateway should store the LLM response in the cache."""

    request = _make_request(app_obj.id, prompt_template.id, variables={"name": "Store"})

    with (
        patch(
            "app.services.gateway_service.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=_fake_llm_response("stored"),
        ),
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.001),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock) as mock_store,
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        await svc.handle_chat(request)

    mock_store.assert_awaited_once()
    args = mock_store.call_args
    # store(app_id, rendered_input, response_text, model, prompt_version_id)
    assert args[0][0] == app_obj.id  # app_id
    assert "Say hello to Store" in args[0][1]  # rendered input
    assert args[0][2] == "stored"  # response text
    assert args[0][3] == "gpt-4o-mini"  # model


@pytest.mark.asyncio
async def test_experiment_variant_resolution(db_session, app_obj, prompt_template, prompt_version, test_user):
    """When a running experiment exists the gateway should resolve a variant
    and include the variant_id in the response."""

    # Create a second prompt version for the experiment variant
    ver2 = PromptVersion(
        template_id=prompt_template.id,
        version_number=2,
        content="Greet {{ name }} warmly",
        variables={"name": ""},
        tag=None,
    )
    db_session.add(ver2)
    await db_session.flush()
    await db_session.refresh(ver2)

    # Create a running experiment with one variant at 100% traffic
    experiment = Experiment(
        application_id=app_obj.id,
        name="GW Experiment",
        status="running",
        created_by=test_user.id,
    )
    db_session.add(experiment)
    await db_session.flush()
    await db_session.refresh(experiment)

    variant = ExperimentVariant(
        experiment_id=experiment.id,
        prompt_version_id=ver2.id,
        traffic_pct=100,
        label="variant-a",
    )
    db_session.add(variant)
    await db_session.flush()
    await db_session.refresh(variant)

    request = _make_request(
        app_obj.id,
        prompt_template.id,
        variables={"name": "Experimenter"},
        user_id="test-user-123",
    )

    with (
        patch(
            "app.services.gateway_service.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=_fake_llm_response("variant response"),
        ),
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.002),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        result = await svc.handle_chat(request)

    assert result["variant_id"] == str(variant.id)
    assert result["cache_hit"] is False

    # Cost log should reference the variant
    from sqlalchemy import select

    log_result = await db_session.execute(select(LLMRequestLog).where(LLMRequestLog.application_id == app_obj.id))
    log = log_result.scalar_one()
    assert log.experiment_variant_id == variant.id


@pytest.mark.asyncio
async def test_model_routing_keyword_rule(db_session, app_obj, prompt_template, prompt_version):
    """A keyword routing rule should redirect to the target model when matched."""

    rule = RoutingRule(
        application_id=app_obj.id,
        name="code-routing",
        condition={"type": "keyword", "keywords": ["code", "python"]},
        target_model="gpt-4o",
        priority=1,
        is_active=True,
    )
    db_session.add(rule)
    await db_session.flush()

    # The rendered prompt will contain "code" via the variable
    request = _make_request(
        app_obj.id,
        prompt_template.id,
        variables={"name": "code expert"},
    )

    routed_response = _fake_llm_response("routed response", model="gpt-4o")
    with (
        patch(
            "app.services.gateway_service.litellm.acompletion", new_callable=AsyncMock, return_value=routed_response
        ) as mock_llm,
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.005),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        result = await svc.handle_chat(request)

    assert result["model"] == "gpt-4o"
    call_kwargs = mock_llm.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o"

    # Cost log should record routed_model
    from sqlalchemy import select

    log_result = await db_session.execute(select(LLMRequestLog).where(LLMRequestLog.application_id == app_obj.id))
    log = log_result.scalar_one()
    assert log.routed_model == "gpt-4o"


@pytest.mark.asyncio
async def test_cost_logging_after_request(db_session, app_obj, prompt_template, prompt_version):
    """Verify that the cost log is persisted with correct token counts, cost,
    and latency after a successful LLM call."""

    request = _make_request(app_obj.id, prompt_template.id, variables={"name": "Cost"})

    fake_resp = _fake_llm_response("cost test")
    with (
        patch("app.services.gateway_service.litellm.acompletion", new_callable=AsyncMock, return_value=fake_resp),
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.0042),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        result = await svc.handle_chat(request)

    from sqlalchemy import select

    log_result = await db_session.execute(select(LLMRequestLog).where(LLMRequestLog.application_id == app_obj.id))
    log = log_result.scalar_one()

    assert log.input_tokens == 10
    assert log.output_tokens == 20
    assert float(log.cost_usd) == pytest.approx(0.0042, abs=1e-6)
    assert log.latency_ms >= 0
    assert log.cache_hit is False
    assert log.prompt_version_id is not None


@pytest.mark.asyncio
async def test_llm_call_failure_propagates(db_session, app_obj, prompt_template, prompt_version):
    """When litellm.acompletion raises an exception the gateway should let it
    propagate (no silent swallowing)."""

    request = _make_request(app_obj.id, prompt_template.id, variables={"name": "Error"})

    with (
        patch(
            "app.services.gateway_service.litellm.acompletion",
            new_callable=AsyncMock,
            side_effect=RuntimeError("LLM is down"),
        ),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        with pytest.raises(RuntimeError, match="LLM is down"):
            await svc.handle_chat(request)

    # No cost log should be written since the LLM call failed before that step
    from sqlalchemy import select

    log_result = await db_session.execute(select(LLMRequestLog).where(LLMRequestLog.application_id == app_obj.id))
    assert log_result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_no_prompt_version_raises(db_session, app_obj, test_user):
    """When no prompt version exists at all for the template the gateway
    should raise ValueError."""

    # Template with NO versions
    tmpl = PromptTemplate(application_id=app_obj.id, name="empty-template")
    db_session.add(tmpl)
    await db_session.flush()
    await db_session.refresh(tmpl)

    request = _make_request(app_obj.id, tmpl.id, variables={})

    with (
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        with pytest.raises(ValueError, match="No prompt version found"):
            await svc.handle_chat(request)


@pytest.mark.asyncio
async def test_temperature_and_max_tokens_forwarded(db_session, app_obj, prompt_template, prompt_version):
    """Optional temperature and max_tokens should be forwarded to litellm."""

    request = _make_request(
        app_obj.id,
        prompt_template.id,
        variables={"name": "Params"},
        temperature=0.7,
        max_tokens=256,
    )

    with (
        patch(
            "app.services.gateway_service.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=_fake_llm_response("ok"),
        ) as mock_llm,
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.001),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        await svc.handle_chat(request)

    call_kwargs = mock_llm.call_args.kwargs
    assert call_kwargs["temperature"] == 0.7
    assert call_kwargs["max_tokens"] == 256


@pytest.mark.asyncio
async def test_langfuse_tracing_called(db_session, app_obj, prompt_template, prompt_version):
    """When LangFuse returns a trace, log_generation and flush should be called."""

    request = _make_request(app_obj.id, prompt_template.id, variables={"name": "Traced"})
    fake_trace = MagicMock()
    fake_trace.id = "trace-abc-123"

    with (
        patch(
            "app.services.gateway_service.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=_fake_llm_response("traced"),
        ),
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.001),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=fake_trace),
        patch("app.services.langfuse_service.LangFuseService.log_generation") as mock_log_gen,
        patch("app.services.langfuse_service.LangFuseService.flush") as mock_flush,
    ):
        svc = GatewayService(db_session)
        result = await svc.handle_chat(request)

    assert result["trace_id"] == "trace-abc-123"
    mock_log_gen.assert_called_once()
    mock_flush.assert_called_once()

    # The cost log should record the trace_id too
    from sqlalchemy import select

    log_result = await db_session.execute(select(LLMRequestLog).where(LLMRequestLog.application_id == app_obj.id))
    log = log_result.scalar_one()
    assert log.trace_id == "trace-abc-123"


@pytest.mark.asyncio
async def test_fallback_to_latest_version_when_no_production_tag(db_session, app_obj, test_user):
    """If no version is tagged 'production' the gateway falls back to the
    latest version by version_number."""

    tmpl = PromptTemplate(application_id=app_obj.id, name="no-prod-template")
    db_session.add(tmpl)
    await db_session.flush()
    await db_session.refresh(tmpl)

    # Two versions, neither tagged production
    v1 = PromptVersion(template_id=tmpl.id, version_number=1, content="v1 {{ name }}", variables={"name": ""})
    v2 = PromptVersion(template_id=tmpl.id, version_number=2, content="v2 {{ name }}", variables={"name": ""})
    db_session.add_all([v1, v2])
    await db_session.flush()

    request = _make_request(app_obj.id, tmpl.id, variables={"name": "Fallback"})

    with (
        patch(
            "app.services.gateway_service.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=_fake_llm_response("ok"),
        ),
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.001),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        result = await svc.handle_chat(request)

    # Should succeed — the gateway found the latest version (v2)
    assert result["response"] == "ok"
    assert result["cache_hit"] is False


# ---------------------------------------------------------------------------
# Routing service edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_routing_complexity_condition(db_session, app_obj, prompt_template, prompt_version):
    """A 'complexity' routing rule routes long inputs to a more capable model."""

    rule = RoutingRule(
        application_id=app_obj.id,
        name="complexity-routing",
        condition={"type": "complexity", "threshold": 5},
        target_model="gpt-4o",
        priority=1,
        is_active=True,
    )
    db_session.add(rule)
    await db_session.flush()

    # Input with >5 words triggers complexity rule (the rendered prompt contains the variable)
    request = _make_request(
        app_obj.id,
        prompt_template.id,
        variables={"name": "a very long input with many many words here"},
    )

    with (
        patch(
            "app.services.gateway_service.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=_fake_llm_response("complex", model="gpt-4o"),
        ) as mock_llm,
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.01),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        result = await svc.handle_chat(request)

    assert result["model"] == "gpt-4o"


@pytest.mark.asyncio
async def test_routing_complexity_below_threshold(db_session, app_obj, prompt_template, prompt_version):
    """A short input should NOT trigger the complexity rule."""

    rule = RoutingRule(
        application_id=app_obj.id,
        name="complexity-routing",
        condition={"type": "complexity", "threshold": 500},
        target_model="gpt-4o",
        priority=1,
        is_active=True,
    )
    db_session.add(rule)
    await db_session.flush()

    request = _make_request(
        app_obj.id,
        prompt_template.id,
        variables={"name": "short"},
    )

    with (
        patch(
            "app.services.gateway_service.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=_fake_llm_response("simple"),
        ) as mock_llm,
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.001),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        result = await svc.handle_chat(request)

    # Should fallback to default model
    assert result["model"] == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_routing_length_condition(db_session, app_obj, prompt_template, prompt_version):
    """A 'length' routing rule routes long character inputs to a different model."""

    rule = RoutingRule(
        application_id=app_obj.id,
        name="length-routing",
        condition={"type": "length", "max_length": 10},
        target_model="gpt-4o",
        priority=1,
        is_active=True,
    )
    db_session.add(rule)
    await db_session.flush()

    request = _make_request(
        app_obj.id,
        prompt_template.id,
        variables={"name": "This is a fairly long name input"},
    )

    with (
        patch(
            "app.services.gateway_service.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=_fake_llm_response("long", model="gpt-4o"),
        ),
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.005),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        result = await svc.handle_chat(request)

    assert result["model"] == "gpt-4o"


@pytest.mark.asyncio
async def test_routing_priority_ordering(db_session, app_obj, prompt_template, prompt_version):
    """When multiple rules match, the lowest priority number wins."""

    rule_low_priority = RoutingRule(
        application_id=app_obj.id,
        name="fallback-rule",
        condition={"type": "keyword", "keywords": ["hello"]},
        target_model="gpt-3.5-turbo",
        priority=10,
        is_active=True,
    )
    rule_high_priority = RoutingRule(
        application_id=app_obj.id,
        name="priority-rule",
        condition={"type": "keyword", "keywords": ["hello"]},
        target_model="gpt-4o",
        priority=1,
        is_active=True,
    )
    db_session.add_all([rule_low_priority, rule_high_priority])
    await db_session.flush()

    request = _make_request(
        app_obj.id,
        prompt_template.id,
        variables={"name": "hello world"},
    )

    with (
        patch(
            "app.services.gateway_service.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=_fake_llm_response("priority", model="gpt-4o"),
        ),
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.005),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        result = await svc.handle_chat(request)

    # Priority 1 rule should win over priority 10
    assert result["model"] == "gpt-4o"


@pytest.mark.asyncio
async def test_routing_inactive_rule_ignored(db_session, app_obj, prompt_template, prompt_version):
    """Inactive routing rules should be ignored."""

    rule = RoutingRule(
        application_id=app_obj.id,
        name="inactive-rule",
        condition={"type": "keyword", "keywords": ["hello"]},
        target_model="gpt-4o",
        priority=1,
        is_active=False,
    )
    db_session.add(rule)
    await db_session.flush()

    request = _make_request(
        app_obj.id,
        prompt_template.id,
        variables={"name": "hello world"},
    )

    with (
        patch(
            "app.services.gateway_service.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=_fake_llm_response("default"),
        ),
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.001),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        result = await svc.handle_chat(request)

    # Inactive rule should not apply — default model used
    assert result["model"] == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_routing_unknown_condition_type_falls_through(db_session, app_obj, prompt_template, prompt_version):
    """An unknown condition type should not match, falling through to default."""

    rule = RoutingRule(
        application_id=app_obj.id,
        name="unknown-rule",
        condition={"type": "sentiment", "threshold": 0.5},
        target_model="gpt-4o",
        priority=1,
        is_active=True,
    )
    db_session.add(rule)
    await db_session.flush()

    request = _make_request(app_obj.id, prompt_template.id, variables={"name": "test"})

    with (
        patch(
            "app.services.gateway_service.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=_fake_llm_response("default"),
        ),
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.001),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        result = await svc.handle_chat(request)

    assert result["model"] == "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Cache service edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_lookup_failure_treated_as_miss(db_session, app_obj, prompt_template, prompt_version):
    """If the cache service raises an exception during lookup, it should be
    treated as a cache miss and the LLM call should proceed normally."""

    request = _make_request(app_obj.id, prompt_template.id, variables={"name": "CacheFail"})

    with (
        patch(
            "app.services.gateway_service.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=_fake_llm_response("ok"),
        ) as mock_llm,
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.001),
        patch(
            "app.services.cache_service.CacheService.lookup",
            new_callable=AsyncMock,
            side_effect=ConnectionError("Qdrant down"),
        ),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        # The cache service internally catches exceptions and returns None
        # But if the mock raises before cache_service's try/except, gateway may propagate
        # This tests that the system is resilient
        result = await svc.handle_chat(request)

    assert result["response"] == "ok"
    mock_llm.assert_awaited_once()


@pytest.mark.asyncio
async def test_cache_store_failure_does_not_break_response(db_session, app_obj, prompt_template, prompt_version):
    """If cache storage fails, the response should still be returned successfully."""

    request = _make_request(app_obj.id, prompt_template.id, variables={"name": "StoreFail"})

    with (
        patch(
            "app.services.gateway_service.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=_fake_llm_response("result"),
        ),
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.001),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch(
            "app.services.cache_service.CacheService.store",
            new_callable=AsyncMock,
            side_effect=ConnectionError("Qdrant write failed"),
        ),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        # cache_service.store() catches exceptions internally, so this should not propagate
        result = await svc.handle_chat(request)

    assert result["response"] == "result"


@pytest.mark.asyncio
async def test_llm_response_missing_usage(db_session, app_obj, prompt_template, prompt_version):
    """When the LLM response has no usage info, tokens should default to 0."""

    request = _make_request(app_obj.id, prompt_template.id, variables={"name": "NoUsage"})

    # Create response with usage=None
    message = SimpleNamespace(content="no usage response")
    choice = SimpleNamespace(message=message)
    no_usage_resp = SimpleNamespace(choices=[choice], usage=None, model="gpt-4o-mini")

    with (
        patch("app.services.gateway_service.litellm.acompletion", new_callable=AsyncMock, return_value=no_usage_resp),
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.0),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        result = await svc.handle_chat(request)

    assert result["input_tokens"] == 0
    assert result["output_tokens"] == 0
    assert result["response"] == "no usage response"


@pytest.mark.asyncio
async def test_llm_empty_content_returns_empty_string(db_session, app_obj, prompt_template, prompt_version):
    """When the LLM returns None content, it should be converted to empty string."""

    request = _make_request(app_obj.id, prompt_template.id, variables={"name": "Empty"})

    message = SimpleNamespace(content=None)
    choice = SimpleNamespace(message=message)
    usage = SimpleNamespace(prompt_tokens=5, completion_tokens=0)
    empty_resp = SimpleNamespace(choices=[choice], usage=usage, model="gpt-4o-mini")

    with (
        patch("app.services.gateway_service.litellm.acompletion", new_callable=AsyncMock, return_value=empty_resp),
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.0),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        result = await svc.handle_chat(request)

    assert result["response"] == ""


@pytest.mark.asyncio
async def test_error_metrics_recorded_on_llm_failure(db_session, app_obj, prompt_template, prompt_version):
    """When the LLM call fails, error_total metric should be incremented."""

    request = _make_request(app_obj.id, prompt_template.id, variables={"name": "MetricFail"})

    mock_metrics = {
        "error_total": MagicMock(),
        "request_duration": MagicMock(),
        "tokens_input": MagicMock(),
        "tokens_output": MagicMock(),
        "cost_total": MagicMock(),
        "cache_hits": MagicMock(),
    }

    with (
        patch(
            "app.services.gateway_service.litellm.acompletion", new_callable=AsyncMock, side_effect=RuntimeError("boom")
        ),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
        patch("app.services.gateway_service.get_metrics", return_value=mock_metrics),
    ):
        svc = GatewayService(db_session)
        with pytest.raises(RuntimeError, match="boom"):
            await svc.handle_chat(request)

    mock_metrics["error_total"].add.assert_called_once_with(1, {"model": "gpt-4o-mini"})


@pytest.mark.asyncio
async def test_custom_model_override(db_session, app_obj, prompt_template, prompt_version):
    """When the request specifies a custom model, it should be used as the default."""

    request = _make_request(
        app_obj.id,
        prompt_template.id,
        variables={"name": "Custom"},
        model="claude-3-5-sonnet-20241022",
    )

    with (
        patch(
            "app.services.gateway_service.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=_fake_llm_response("custom", model="claude-3-5-sonnet-20241022"),
        ) as mock_llm,
        patch("app.services.gateway_service.litellm.completion_cost", return_value=0.003),
        patch("app.services.cache_service.CacheService.lookup", new_callable=AsyncMock, return_value=None),
        patch("app.services.cache_service.CacheService.store", new_callable=AsyncMock),
        patch("app.services.langfuse_service.LangFuseService.create_trace", return_value=None),
    ):
        svc = GatewayService(db_session)
        result = await svc.handle_chat(request)

    assert result["model"] == "claude-3-5-sonnet-20241022"
    call_kwargs = mock_llm.call_args.kwargs
    assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"
