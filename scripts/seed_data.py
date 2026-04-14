"""
Seed script: populates the LLMOps database with realistic demo data.

Usage:
    # With docker-compose running:
    docker-compose exec backend python -m scripts.seed_data

    # Or directly (with DATABASE_URL set):
    cd backend && python -m scripts.seed_data
"""

import asyncio
import random
import re
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.middleware.auth import hash_password
from app.models import Base
from app.models.application import Application
from app.models.cost import BudgetAlert, LLMRequestLog, RoutingRule
from app.models.deployment import Deployment
from app.models.enums import DeploymentStatus, EvalRunStatus, ExperimentStatus
from app.models.evaluation import EvalDataset, EvalDatasetItem, EvalResult, EvalRun
from app.models.experiment import Experiment, ExperimentResult, ExperimentVariant
from app.models.prompt import PromptTemplate, PromptVersion
from app.models.user import User

NOW = datetime.now(timezone.utc)
random.seed(42)  # Reproducible demo data

# ---------------------------------------------------------------------------
# Prompt content — realistic multi-version evolution
# ---------------------------------------------------------------------------

PROMPT_CONTENTS = {
    "Customer Support Bot": [
        (
            "You are a helpful customer support agent for {{company_name}}.\n"
            "Answer the customer's question: {{question}}\n"
            "Be polite and concise."
        ),
        (
            "You are a helpful customer support agent for {{company_name}}.\n"
            "The customer asks: {{question}}\n\n"
            "Guidelines:\n- Be polite and empathetic\n- Keep responses under 3 sentences\n- If unsure, escalate"
        ),
        (
            "You are a senior customer support agent for {{company_name}}.\n\n"
            "Customer query: {{question}}\n"
            "Customer tier: {{tier}}\n\n"
            "Guidelines:\n- Be polite, empathetic, and professional\n"
            "- For premium customers, offer proactive solutions\n"
            "- Keep responses under 3 sentences\n"
            "- If unsure, escalate to a human agent\n"
            "- Never share internal policies"
        ),
        (
            "You are a senior customer support agent for {{company_name}}.\n\n"
            "Customer query: {{question}}\n"
            "Customer tier: {{tier}}\n"
            "Previous interactions: {{history}}\n\n"
            "Guidelines:\n- Be polite, empathetic, and professional\n"
            "- For premium customers, offer proactive solutions\n"
            "- Reference previous interactions when relevant\n"
            "- Keep responses under 3 sentences\n"
            "- If unsure, escalate to a human agent\n"
            "- Never share internal policies or pricing logic"
        ),
    ],
    "Code Review Assistant": [
        (
            "Review this code and provide feedback:\n```{{language}}\n{{code}}\n```"
        ),
        (
            "You are an expert code reviewer. Review this {{language}} code:\n\n"
            "```{{language}}\n{{code}}\n```\n\n"
            "Focus on: bugs, performance, readability."
        ),
        (
            "You are an expert senior engineer performing a code review.\n\n"
            "Language: {{language}}\n"
            "Context: {{context}}\n\n"
            "```{{language}}\n{{code}}\n```\n\n"
            "Provide feedback on:\n1. Correctness and potential bugs\n"
            "2. Performance implications\n3. Code readability and style\n"
            "4. Security concerns\n\nFormat as a bulleted list."
        ),
    ],
    "Content Summarizer": [
        (
            "Summarize the following text:\n\n{{text}}"
        ),
        (
            "Summarize the following text in {{max_sentences}} sentences or fewer.\n"
            "Target audience: {{audience}}\n\n{{text}}"
        ),
        (
            "You are a professional content summarizer.\n\n"
            "Target audience: {{audience}}\n"
            "Max length: {{max_sentences}} sentences\n"
            "Style: {{style}}\n\n"
            "Source text:\n{{text}}\n\n"
            "Requirements:\n- Preserve key facts and figures\n"
            "- Maintain the original tone\n- Include actionable takeaways"
        ),
    ],
    "SQL Query Generator": [
        (
            "Generate a SQL query for: {{question}}\n\nSchema: {{schema}}"
        ),
        (
            "You are a database expert. Generate an optimized SQL query.\n\n"
            "Database: {{db_type}}\n"
            "Schema:\n{{schema}}\n\n"
            "Question: {{question}}\n\n"
            "Return only the SQL query, no explanation."
        ),
        (
            "You are a senior database engineer.\n\n"
            "Database: {{db_type}}\n"
            "Schema:\n{{schema}}\n\n"
            "Question: {{question}}\n"
            "Performance requirements: {{perf_requirements}}\n\n"
            "Generate an optimized SQL query. Include:\n"
            "1. The query\n2. Index recommendations\n"
            "3. Estimated complexity\n\n"
            "Use CTEs for readability. Avoid SELECT *."
        ),
    ],
}

COMMIT_MESSAGES = [
    "Initial prompt template",
    "Add guidelines and tone instructions",
    "Add variable support and edge case handling",
    "Refine based on eval feedback, add context awareness",
]

MODELS = ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"]

EVAL_ITEMS = {
    "Customer Support Bot": [
        {"input_vars": {"company_name": "Acme Corp", "question": "Where is my order #12345?", "tier": "premium", "history": "none"}, "expected_output": "I'd be happy to help you track your order."},
        {"input_vars": {"company_name": "Acme Corp", "question": "I want a refund", "tier": "standard", "history": "none"}, "expected_output": "I understand your frustration. Let me look into your refund options."},
        {"input_vars": {"company_name": "Acme Corp", "question": "How do I reset my password?", "tier": "premium", "history": "called twice before"}, "expected_output": "You can reset your password from the account settings page."},
        {"input_vars": {"company_name": "Acme Corp", "question": "Your product broke after 2 days", "tier": "standard", "history": "none"}, "expected_output": "I'm sorry to hear that. Let's get this resolved for you."},
        {"input_vars": {"company_name": "Acme Corp", "question": "Can I upgrade my plan?", "tier": "premium", "history": "upgraded once"}, "expected_output": "Absolutely! Here are the available upgrade options."},
    ],
    "Code Review Assistant": [
        {"input_vars": {"language": "python", "code": "def add(a, b): return a + b", "context": "utility function"}, "expected_output": "Consider adding type hints and docstring."},
        {"input_vars": {"language": "javascript", "code": "const data = eval(userInput)", "context": "API handler"}, "expected_output": "Critical: never use eval() with user input."},
        {"input_vars": {"language": "python", "code": "for i in range(len(lst)): print(lst[i])", "context": "data processing"}, "expected_output": "Use direct iteration: for item in lst."},
        {"input_vars": {"language": "python", "code": "import os; os.system(cmd)", "context": "deploy script"}, "expected_output": "Use subprocess.run() instead of os.system()."},
    ],
    "Content Summarizer": [
        {"input_vars": {"text": "AI has transformed multiple industries through automation...", "audience": "executives", "max_sentences": "3", "style": "formal"}, "expected_output": "AI is reshaping industries through automation and data-driven insights."},
        {"input_vars": {"text": "Quarterly revenue grew by 15% year-over-year...", "audience": "investors", "max_sentences": "2", "style": "concise"}, "expected_output": "Revenue increased 15% YoY with strong margin expansion."},
        {"input_vars": {"text": "New research shows exercise improves cognitive function...", "audience": "general public", "max_sentences": "3", "style": "accessible"}, "expected_output": "Exercise boosts brain health and memory."},
    ],
    "SQL Query Generator": [
        {"input_vars": {"question": "Top 10 customers by revenue", "schema": "customers(id, name), orders(id, customer_id, total)", "db_type": "PostgreSQL", "perf_requirements": "< 100ms"}, "expected_output": "SELECT c.name, SUM(o.total) FROM customers c JOIN orders o..."},
        {"input_vars": {"question": "Monthly active users", "schema": "users(id), sessions(id, user_id, created_at)", "db_type": "PostgreSQL", "perf_requirements": "< 500ms"}, "expected_output": "SELECT DATE_TRUNC('month', created_at), COUNT(DISTINCT user_id)..."},
        {"input_vars": {"question": "Products never ordered", "schema": "products(id, name), order_items(product_id)", "db_type": "PostgreSQL", "perf_requirements": "none"}, "expected_output": "SELECT p.* FROM products p LEFT JOIN order_items oi ON ..."},
    ],
}


def _ts(days_ago: int, hours: int = 0) -> datetime:
    return NOW - timedelta(days=days_ago, hours=hours)


async def seed() -> None:
    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        print("Seeding database with demo data...\n")

        # ---- Users ----
        admin = User(id=uuid.uuid4(), email="admin@llmops.dev", hashed_password=hash_password("admin123"), role="admin")
        engineer = User(id=uuid.uuid4(), email="engineer@llmops.dev", hashed_password=hash_password("engineer123"), role="engineer")
        reviewer = User(id=uuid.uuid4(), email="reviewer@llmops.dev", hashed_password=hash_password("reviewer123"), role="reviewer")
        users = [admin, engineer, reviewer]
        for u in users:
            db.add(u)
        await db.flush()
        print(f"  [+] {len(users)} users")

        # ---- Applications ----
        app_configs = [
            ("Customer Support Platform", "AI-powered customer support with multi-tier routing"),
            ("Developer Tools Suite", "Code review, generation, and documentation assistant"),
            ("Content Operations", "Summarization, translation, and content generation pipeline"),
            ("Data Analytics Assistant", "Natural language to SQL and data visualization"),
        ]
        apps = []
        for i, (name, desc) in enumerate(app_configs):
            app = Application(id=uuid.uuid4(), name=name, description=desc, created_by=admin.id, created_at=_ts(30 - i))
            db.add(app)
            apps.append(app)
        await db.flush()
        print(f"  [+] {len(apps)} applications")

        # ---- Prompt Templates & Versions ----
        prompt_names = list(PROMPT_CONTENTS.keys())
        # Each app gets one prompt template
        all_templates: list[PromptTemplate] = []
        all_versions: dict[uuid.UUID, list[PromptVersion]] = {}

        for app_idx, pname in enumerate(prompt_names):
            template = PromptTemplate(
                id=uuid.uuid4(),
                application_id=apps[app_idx].id,
                name=pname,
                description=f"Production {pname.lower()} prompt template",
                created_at=_ts(28),
            )
            db.add(template)
            all_templates.append(template)

            contents = PROMPT_CONTENTS[pname]
            versions: list[PromptVersion] = []
            for v_idx, content in enumerate(contents):
                vars_found = re.findall(r"\{\{\s*(\w+)\s*\}\}", content)
                variables = {v: f"string - {v.replace('_', ' ')}" for v in vars_found}

                tag = None
                if v_idx == len(contents) - 1:
                    tag = "production"
                elif v_idx == len(contents) - 2:
                    tag = "staging"

                version = PromptVersion(
                    id=uuid.uuid4(),
                    template_id=template.id,
                    version_number=v_idx + 1,
                    content=content,
                    variables=variables,
                    model_config_json={"model": MODELS[v_idx % len(MODELS)], "temperature": 0.7, "max_tokens": 1024},
                    tag=tag,
                    commit_message=COMMIT_MESSAGES[v_idx] if v_idx < len(COMMIT_MESSAGES) else f"v{v_idx + 1} improvements",
                    created_by=engineer.id,
                    created_at=_ts(28 - v_idx * 5),
                )
                db.add(version)
                versions.append(version)

            all_versions[template.id] = versions

        await db.flush()
        total_versions = sum(len(v) for v in all_versions.values())
        print(f"  [+] {len(all_templates)} prompt templates with {total_versions} versions")

        # ---- Eval Datasets & Items ----
        all_datasets: list[EvalDataset] = []
        dataset_items_map: dict[uuid.UUID, list[EvalDatasetItem]] = {}  # dataset_id -> items

        for template in all_templates:
            items_data = EVAL_ITEMS.get(template.name, [])
            if not items_data:
                continue

            dataset = EvalDataset(
                id=uuid.uuid4(),
                application_id=template.application_id,
                name=f"{template.name} Golden Dataset",
                dataset_type="golden",
                description=f"Curated test cases for {template.name}",
                created_at=_ts(25),
            )
            db.add(dataset)
            all_datasets.append(dataset)

            ds_items: list[EvalDatasetItem] = []
            for item_data in items_data:
                item = EvalDatasetItem(
                    id=uuid.uuid4(),
                    dataset_id=dataset.id,
                    input_vars=item_data["input_vars"],
                    expected_output=item_data.get("expected_output"),
                    created_at=_ts(25),
                )
                db.add(item)
                ds_items.append(item)
            dataset_items_map[dataset.id] = ds_items

        await db.flush()
        print(f"  [+] {len(all_datasets)} eval datasets with {sum(len(v) for v in dataset_items_map.values())} items")

        # ---- Eval Runs with Results ----
        all_eval_runs: list[EvalRun] = []

        for template in all_templates:
            versions = all_versions[template.id]
            dataset = next((d for d in all_datasets if d.name.startswith(template.name)), None)
            if not dataset:
                continue

            ds_items = dataset_items_map.get(dataset.id, [])

            # Create eval runs for last 2 versions (to support regression comparison)
            for v in versions[-2:]:
                base_score = 3.2 + (v.version_number * 0.3)
                agg_scores = {
                    "relevance": round(min(base_score + random.uniform(-0.2, 0.3), 5.0), 2),
                    "coherence": round(min(base_score + random.uniform(-0.1, 0.4), 5.0), 2),
                    "helpfulness": round(min(base_score + random.uniform(-0.3, 0.2), 5.0), 2),
                    "safety": round(min(base_score + random.uniform(0.0, 0.5), 5.0), 2),
                }

                run = EvalRun(
                    id=uuid.uuid4(),
                    prompt_version_id=v.id,
                    dataset_id=dataset.id,
                    status=EvalRunStatus.COMPLETED,
                    trigger="manual",
                    aggregate_scores=agg_scores,
                    created_by=engineer.id,
                    created_at=_ts(20 - v.version_number * 2),
                    completed_at=_ts(20 - v.version_number * 2) + timedelta(minutes=3),
                )
                db.add(run)
                all_eval_runs.append(run)

                for di in ds_items:
                    result = EvalResult(
                        id=uuid.uuid4(),
                        eval_run_id=run.id,
                        dataset_item_id=di.id,
                        llm_response=f"[Demo] Response for {template.name} v{v.version_number}",
                        scores={k: round(s + random.uniform(-0.5, 0.5), 2) for k, s in agg_scores.items()},
                        latency_ms=random.randint(200, 1500),
                        token_usage={"input": random.randint(100, 500), "output": random.randint(50, 300)},
                        cost_usd=Decimal(str(round(random.uniform(0.001, 0.05), 4))),
                        created_at=run.created_at,
                    )
                    db.add(result)

        await db.flush()
        print(f"  [+] {len(all_eval_runs)} eval runs with results")

        # ---- Experiments ----
        experiments: list[Experiment] = []

        for t_idx, template in enumerate(all_templates[:2]):
            versions = all_versions[template.id]
            if len(versions) < 2:
                continue

            v_a, v_b = versions[-2], versions[-1]
            is_completed = t_idx == 0

            exp = Experiment(
                id=uuid.uuid4(),
                application_id=template.application_id,
                name=f"{template.name}: v{v_a.version_number} vs v{v_b.version_number}",
                status=ExperimentStatus.COMPLETED if is_completed else ExperimentStatus.RUNNING,
                started_at=_ts(10),
                ended_at=_ts(3) if is_completed else None,
                created_by=engineer.id,
                created_at=_ts(12),
            )
            db.add(exp)
            experiments.append(exp)
            await db.flush()

            var_a = ExperimentVariant(id=uuid.uuid4(), experiment_id=exp.id, prompt_version_id=v_a.id, traffic_pct=50, label="Control")
            var_b = ExperimentVariant(id=uuid.uuid4(), experiment_id=exp.id, prompt_version_id=v_b.id, traffic_pct=50, label="Challenger")
            db.add(var_a)
            db.add(var_b)
            await db.flush()

            res_a = ExperimentResult(
                id=uuid.uuid4(), experiment_id=exp.id, variant_id=var_a.id,
                request_count=random.randint(500, 1200),
                metrics={"avg_score": round(random.uniform(3.5, 4.0), 2), "avg_latency_ms": random.randint(400, 800)},
                p_value=0.03 if is_completed else None,
                is_winner=False if is_completed else None,
            )
            res_b = ExperimentResult(
                id=uuid.uuid4(), experiment_id=exp.id, variant_id=var_b.id,
                request_count=random.randint(500, 1200),
                metrics={"avg_score": round(random.uniform(4.0, 4.8), 2), "avg_latency_ms": random.randint(300, 600)},
                p_value=0.03 if is_completed else None,
                is_winner=True if is_completed else None,
            )
            db.add(res_a)
            db.add(res_b)

        await db.flush()
        print(f"  [+] {len(experiments)} experiments with variants and results")

        # ---- Deployments ----
        deployments: list[Deployment] = []

        for t_idx, template in enumerate(all_templates):
            versions = all_versions[template.id]
            prod_version = next((v for v in versions if v.tag == "production"), versions[-1])

            dep = Deployment(
                id=uuid.uuid4(),
                application_id=template.application_id,
                prompt_version_id=prod_version.id,
                status=DeploymentStatus.ROLLED_OUT,
                canary_pct=100,
                eval_run_id=all_eval_runs[min(t_idx * 2, len(all_eval_runs) - 1)].id,
                previous_version_id=versions[-2].id if len(versions) >= 2 else None,
                deployed_by=admin.id,
                created_at=_ts(5),
            )
            db.add(dep)
            deployments.append(dep)

        # Add one active canary deployment
        if all_templates and len(all_versions[all_templates[0].id]) >= 2:
            canary_dep = Deployment(
                id=uuid.uuid4(),
                application_id=all_templates[0].application_id,
                prompt_version_id=all_versions[all_templates[0].id][-1].id,
                status=DeploymentStatus.CANARY,
                canary_pct=25,
                previous_version_id=all_versions[all_templates[0].id][-2].id,
                deployed_by=engineer.id,
                created_at=_ts(1),
            )
            db.add(canary_dep)
            deployments.append(canary_dep)

        await db.flush()
        print(f"  [+] {len(deployments)} deployments (including 1 active canary)")

        # ---- LLM Request Logs (30 days of traffic) ----
        log_count = 0
        for day in range(30):
            num_requests = random.randint(50, 200) if day % 7 < 5 else random.randint(10, 50)
            for _ in range(num_requests):
                app = random.choice(apps)
                model = random.choice(MODELS)
                input_tokens = random.randint(50, 800)
                output_tokens = random.randint(20, 400)
                cost_per_1k = {"gpt-4o": 0.005, "gpt-4o-mini": 0.00015, "claude-sonnet-4-20250514": 0.003, "claude-haiku-4-5-20251001": 0.00025}
                cost = (input_tokens + output_tokens) * cost_per_1k.get(model, 0.001) / 1000

                log = LLMRequestLog(
                    id=uuid.uuid4(),
                    application_id=app.id,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=Decimal(str(round(cost, 6))),
                    latency_ms=random.randint(150, 3000),
                    cache_hit=random.random() < 0.25,
                    routed_model=model if random.random() < 0.3 else None,
                    created_at=_ts(day, random.randint(0, 23)),
                )
                db.add(log)
                log_count += 1

        await db.flush()
        print(f"  [+] {log_count} LLM request logs (30 days of traffic)")

        # ---- Budget Alerts ----
        for app in apps:
            alert = BudgetAlert(
                id=uuid.uuid4(),
                application_id=app.id,
                budget_usd=Decimal("500.00"),
                period="monthly",
                alert_pct=[80, 100],
                is_active=True,
                created_by=admin.id,
                created_at=_ts(25),
            )
            db.add(alert)
        await db.flush()
        print(f"  [+] {len(apps)} budget alerts")

        # ---- Routing Rules ----
        rule_configs = [
            {"name": "Cost-optimize short queries", "condition": {"max_tokens_lt": 100}, "target": "gpt-4o-mini", "fallback": "gpt-4o"},
            {"name": "Premium tier uses GPT-4o", "condition": {"tier_eq": "premium"}, "target": "gpt-4o", "fallback": "gpt-4o-mini"},
            {"name": "Code tasks use Claude", "condition": {"keyword_contains": "code"}, "target": "claude-sonnet-4-20250514", "fallback": "gpt-4o"},
        ]
        for i, rc in enumerate(rule_configs):
            rule = RoutingRule(
                id=uuid.uuid4(),
                application_id=apps[0].id,
                name=rc["name"],
                condition=rc["condition"],
                target_model=rc["target"],
                fallback_model=rc["fallback"],
                priority=(i + 1) * 10,
                is_active=True,
                created_at=_ts(20),
            )
            db.add(rule)
        await db.flush()
        print(f"  [+] {len(rule_configs)} routing rules")

        await db.commit()

    await engine.dispose()

    print("\n" + "=" * 50)
    print("Seed data created successfully!")
    print("=" * 50)
    print("\nDemo credentials:")
    print("  admin@llmops.dev    / admin123     (admin)")
    print("  engineer@llmops.dev / engineer123  (engineer)")
    print("  reviewer@llmops.dev / reviewer123  (reviewer)")
    print("\nData summary:")
    print("  4 applications with prompt templates")
    print("  14 prompt versions across 4 templates")
    print("  4 golden eval datasets with test items")
    print("  8 completed eval runs with per-item results")
    print("  2 A/B experiments (1 completed, 1 running)")
    print("  5 deployments (including 1 active canary)")
    print(f"  ~{log_count} request logs with cost data")
    print("  4 budget alerts, 3 routing rules")


if __name__ == "__main__":
    asyncio.run(seed())
