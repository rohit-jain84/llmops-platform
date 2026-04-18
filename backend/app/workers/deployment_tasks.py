import asyncio
import logging

from sqlalchemy import select

from app.database import async_session_factory
from app.models.deployment import Deployment
from app.models.enums import DeploymentStatus, EvalRunStatus
from app.models.evaluation import EvalRun
from app.workers.celery_app import celery_app

CANARY_QUALITY_THRESHOLD = 0.7

logger = logging.getLogger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.deployment_tasks.progress_canary")
def progress_canary():
    _run_async(_progress_canary_async())


async def _progress_canary_async():
    async with async_session_factory() as db:
        result = await db.execute(select(Deployment).where(Deployment.status == DeploymentStatus.CANARY))
        deployments = result.scalars().all()

        for deployment in deployments:
            # Query the most recent completed EvalRun for this prompt version
            eval_result = await db.execute(
                select(EvalRun)
                .where(
                    EvalRun.prompt_version_id == deployment.prompt_version_id,
                    EvalRun.status == EvalRunStatus.COMPLETED,
                )
                .order_by(EvalRun.created_at.desc())
                .limit(1)
            )
            latest_eval = eval_result.scalar_one_or_none()

            if latest_eval and latest_eval.aggregate_scores:
                scores = latest_eval.aggregate_scores
                avg_score = sum(scores.values()) / len(scores) if scores else 0.0
                quality_ok = avg_score >= CANARY_QUALITY_THRESHOLD
                logger.info(
                    f"Deployment {deployment.id}: eval avg score = {avg_score:.3f} "
                    f"(threshold {CANARY_QUALITY_THRESHOLD}), quality_ok={quality_ok}"
                )
            else:
                quality_ok = False
                logger.warning(
                    f"Deployment {deployment.id}: no completed eval run found "
                    f"for prompt version {deployment.prompt_version_id}, blocking canary advance"
                )

            if quality_ok:
                stages = [10, 25, 50, 100]
                current_idx = -1
                for i, s in enumerate(stages):
                    if deployment.canary_pct <= s:
                        current_idx = i
                        break

                if current_idx < len(stages) - 1:
                    new_pct = stages[current_idx + 1]
                    deployment.canary_pct = new_pct
                    logger.info(f"Deployment {deployment.id}: canary progressed to {new_pct}%")

                    if new_pct == 100:
                        deployment.status = DeploymentStatus.ROLLED_OUT
                        # Tag prompt version as production
                        from sqlalchemy import select as sel

                        from app.models.prompt import PromptVersion

                        version_result = await db.execute(
                            sel(PromptVersion).where(PromptVersion.id == deployment.prompt_version_id)
                        )
                        version = version_result.scalar_one_or_none()
                        if version:
                            # Clear old production tag
                            existing = await db.execute(
                                sel(PromptVersion).where(
                                    PromptVersion.template_id == version.template_id,
                                    PromptVersion.tag == "production",
                                )
                            )
                            for v in existing.scalars().all():
                                v.tag = None
                            version.tag = "production"
                        logger.info(f"Deployment {deployment.id}: fully rolled out")
                else:
                    deployment.status = DeploymentStatus.ROLLED_OUT
            else:
                # Rollback
                deployment.status = DeploymentStatus.ROLLED_BACK
                deployment.canary_pct = 0
                logger.warning(f"Deployment {deployment.id}: quality degraded, rolling back")

                # Restore previous version
                if deployment.previous_version_id:
                    from app.models.prompt import PromptVersion

                    prev = await db.execute(
                        select(PromptVersion).where(PromptVersion.id == deployment.previous_version_id)
                    )
                    prev_version = prev.scalar_one_or_none()
                    if prev_version:
                        prev_version.tag = "production"

        await db.commit()
