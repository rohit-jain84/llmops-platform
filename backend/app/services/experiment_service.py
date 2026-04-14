import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from scipy import stats
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import ExperimentStatus
from app.models.experiment import Experiment, ExperimentResult, ExperimentVariant
from app.models.prompt import PromptVersion
from app.schemas.experiment import ExperimentCreate


class ExperimentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_experiment(self, data: ExperimentCreate, user_id: uuid.UUID) -> Experiment:
        # Validate traffic percentages sum to 100
        total_traffic = sum(v.traffic_pct for v in data.variants)
        if total_traffic != 100:
            raise HTTPException(status_code=400, detail=f"Traffic percentages must sum to 100, got {total_traffic}")

        experiment = Experiment(
            application_id=data.application_id,
            name=data.name,
            created_by=user_id,
        )
        self.db.add(experiment)
        await self.db.flush()

        for v in data.variants:
            variant = ExperimentVariant(
                experiment_id=experiment.id,
                prompt_version_id=v.prompt_version_id,
                traffic_pct=v.traffic_pct,
                label=v.label,
            )
            self.db.add(variant)

            # Create result tracker
            result = ExperimentResult(
                experiment_id=experiment.id,
                variant_id=variant.id,
            )
            self.db.add(result)

        await self.db.flush()
        # Reload with variants
        result = await self.db.execute(
            select(Experiment)
            .options(selectinload(Experiment.variants))
            .where(Experiment.id == experiment.id)
        )
        return result.scalar_one()

    async def start_experiment(self, experiment_id: uuid.UUID) -> Experiment:
        result = await self.db.execute(
            select(Experiment)
            .options(selectinload(Experiment.variants))
            .where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        if experiment.status != ExperimentStatus.DRAFT:
            raise HTTPException(status_code=400, detail="Experiment must be in draft status to start")

        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.now(timezone.utc)
        await self.db.flush()
        return experiment

    async def stop_experiment(self, experiment_id: uuid.UUID) -> Experiment:
        result = await self.db.execute(
            select(Experiment)
            .options(selectinload(Experiment.variants))
            .where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")

        experiment.status = ExperimentStatus.COMPLETED
        experiment.ended_at = datetime.now(timezone.utc)
        await self.db.flush()
        return experiment

    async def get_results(self, experiment_id: uuid.UUID) -> list[ExperimentResult]:
        result = await self.db.execute(
            select(ExperimentResult).where(ExperimentResult.experiment_id == experiment_id)
        )
        return list(result.scalars().all())

    async def record_eval_score(
        self, experiment_id: uuid.UUID, variant_id: uuid.UUID, score: float
    ) -> ExperimentResult:
        """Append an evaluation score to a variant's metrics for significance testing."""
        result = await self.db.execute(
            select(ExperimentResult).where(
                ExperimentResult.experiment_id == experiment_id,
                ExperimentResult.variant_id == variant_id,
            )
        )
        exp_result = result.scalar_one_or_none()
        if not exp_result:
            raise HTTPException(status_code=404, detail="Experiment result not found for variant")

        metrics = exp_result.metrics or {}
        scores = metrics.get("scores", [])
        scores.append(score)
        metrics["scores"] = scores
        exp_result.metrics = metrics
        exp_result.request_count = len(scores)

        # Force SQLAlchemy to detect JSONB mutation
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(exp_result, "metrics")

        await self.db.flush()
        return exp_result

    async def compute_significance(self, experiment_id: uuid.UUID, significance_level: float = 0.05) -> list[ExperimentResult]:
        """Compute statistical significance between experiment variants using Welch's t-test.

        Uses a one-tailed test: we only care whether the best variant is
        *better* than the runner-up, not just different.  A variant is marked
        as winner when:
          1. It has the highest mean score, AND
          2. The one-tailed p-value vs. the next-best variant is below ``significance_level``.

        For 3+ variants, applies Bonferroni correction to control the
        family-wise error rate.
        """
        results = await self.get_results(experiment_id)
        if len(results) < 2:
            return results

        # Extract per-variant score lists from metrics JSONB
        variant_scores: dict[uuid.UUID, list[float]] = {}
        for r in results:
            scores = (r.metrics or {}).get("scores", [])
            variant_scores[r.variant_id] = [float(s) for s in scores] if scores else []

        # Rank variants by mean score (descending)
        scored_results = [
            (r, variant_scores.get(r.variant_id, []))
            for r in results
        ]
        scored_results.sort(
            key=lambda pair: (sum(pair[1]) / len(pair[1])) if pair[1] else 0.0,
            reverse=True,
        )

        best_result, best_scores = scored_results[0]
        runner_up_result, runner_up_scores = scored_results[1]

        # Reset all results
        for r in results:
            r.is_winner = False
            r.p_value = None

        # Compute one-tailed p-value between top two variants using Welch's t-test
        if len(best_scores) >= 2 and len(runner_up_scores) >= 2:
            best_mean = sum(best_scores) / len(best_scores)
            runner_up_mean = sum(runner_up_scores) / len(runner_up_scores)

            t_stat, two_tailed_p = stats.ttest_ind(
                best_scores, runner_up_scores, equal_var=False
            )
            two_tailed_p = float(two_tailed_p)

            # One-tailed: we only care if best > runner-up
            if best_mean > runner_up_mean:
                p_value = two_tailed_p / 2.0
            else:
                p_value = 1.0 - (two_tailed_p / 2.0)
        else:
            p_value = 1.0  # Not enough data for significance

        best_result.p_value = p_value
        runner_up_result.p_value = p_value

        # Bonferroni correction for multiple comparisons (k variants → k-1 comparisons)
        num_comparisons = len(results) - 1
        adjusted_level = significance_level / num_comparisons if num_comparisons > 1 else significance_level

        if p_value < adjusted_level:
            best_result.is_winner = True

        await self.db.flush()
        return results

    async def promote_winner(self, experiment_id: uuid.UUID) -> Experiment:
        result = await self.db.execute(
            select(Experiment)
            .options(selectinload(Experiment.variants))
            .where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")

        # Find winning variant
        results = await self.get_results(experiment_id)
        winner = None
        for r in results:
            if r.is_winner:
                winner = r
                break

        if not winner:
            raise HTTPException(status_code=400, detail="No winner determined yet")

        # Tag the winning prompt version as production
        variant_result = await self.db.execute(
            select(ExperimentVariant).where(ExperimentVariant.id == winner.variant_id)
        )
        variant = variant_result.scalar_one()
        version_result = await self.db.execute(
            select(PromptVersion).where(PromptVersion.id == variant.prompt_version_id)
        )
        version = version_result.scalar_one()

        # Remove production tag from other versions of same template
        existing = await self.db.execute(
            select(PromptVersion).where(
                PromptVersion.template_id == version.template_id,
                PromptVersion.tag == "production",
            )
        )
        for v in existing.scalars().all():
            v.tag = None

        version.tag = "production"
        experiment.status = ExperimentStatus.COMPLETED
        experiment.ended_at = datetime.now(timezone.utc)
        await self.db.flush()

        return experiment

    async def resolve_variant(self, app_id: uuid.UUID, user_identifier: str | None = None) -> ExperimentVariant | None:
        """Resolve which experiment variant to use for a request."""
        result = await self.db.execute(
            select(Experiment)
            .options(selectinload(Experiment.variants))
            .where(Experiment.application_id == app_id, Experiment.status == ExperimentStatus.RUNNING)
            .limit(1)
        )
        experiment = result.scalar_one_or_none()
        if not experiment or not experiment.variants:
            return None

        # Simple deterministic traffic split based on user_identifier hash
        import hashlib
        hash_input = (user_identifier or str(uuid.uuid4())).encode()
        hash_val = int(hashlib.md5(hash_input).hexdigest(), 16) % 100

        cumulative = 0
        for variant in experiment.variants:
            cumulative += variant.traffic_pct
            if hash_val < cumulative:
                return variant

        return experiment.variants[-1]
