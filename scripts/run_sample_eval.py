"""Run a sample evaluation against the seeded data.

Run: python scripts/run_sample_eval.py
"""
import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.evaluation import EvalDataset, EvalRun
from app.models.prompt import PromptVersion
from app.workers.eval_tasks import _run_eval_suite_async


async def run():
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        # Get production prompt version
        result = await db.execute(
            select(PromptVersion).where(PromptVersion.tag == "production").limit(1)
        )
        version = result.scalar_one_or_none()
        if not version:
            print("No production prompt version found. Run seed_data.py first.")
            return

        # Get golden dataset
        result = await db.execute(
            select(EvalDataset).where(EvalDataset.dataset_type == "golden").limit(1)
        )
        dataset = result.scalar_one_or_none()
        if not dataset:
            print("No golden dataset found. Run seed_data.py first.")
            return

        # Create eval run
        run = EvalRun(
            prompt_version_id=version.id,
            dataset_id=dataset.id,
            trigger="manual",
            status="pending",
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

        print(f"Created eval run: {run.id}")
        print(f"Prompt version: v{version.version_number} ({version.tag})")
        print(f"Dataset: {dataset.name}")
        print("Running evaluation...")

    # Run eval
    await _run_eval_suite_async(str(run.id))

    # Check results
    async with session_factory() as db:
        result = await db.execute(select(EvalRun).where(EvalRun.id == run.id))
        run = result.scalar_one()
        print(f"\nEval completed with status: {run.status}")
        if run.aggregate_scores:
            print("Aggregate scores:")
            for metric, score in run.aggregate_scores.items():
                print(f"  {metric}: {score}")


if __name__ == "__main__":
    asyncio.run(run())
