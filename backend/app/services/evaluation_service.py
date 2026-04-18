import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EvalRunStatus, HumanEvalAssignmentStatus, HumanEvalCampaignStatus
from app.models.evaluation import (
    EvalResult,
    EvalRun,
    HumanEvalAssignment,
    HumanEvalCampaign,
)
from app.schemas.evaluation import (
    EvalRunCreate,
    HumanEvalCampaignCreate,
    HumanEvalRatingSubmit,
)


class EvaluationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def trigger_eval_run(self, data: EvalRunCreate, user_id: uuid.UUID) -> EvalRun:
        run = EvalRun(
            prompt_version_id=data.prompt_version_id,
            dataset_id=data.dataset_id,
            trigger=data.trigger,
            status=EvalRunStatus.PENDING,
            created_by=user_id,
        )
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)

        # Dispatch Celery task
        from app.workers.eval_tasks import run_eval_suite

        run_eval_suite.delay(str(run.id))

        return run

    async def create_human_eval_campaign(self, data: HumanEvalCampaignCreate, user_id: uuid.UUID) -> HumanEvalCampaign:
        campaign = HumanEvalCampaign(
            eval_run_id=data.eval_run_id,
            name=data.name,
            dimensions=data.dimensions,
            status=HumanEvalCampaignStatus.ACTIVE,
            created_by=user_id,
        )
        self.db.add(campaign)
        await self.db.flush()

        # Get eval results for this run and create assignments
        results = await self.db.execute(select(EvalResult).where(EvalResult.eval_run_id == data.eval_run_id))
        eval_results = results.scalars().all()

        for eval_result in eval_results:
            for evaluator_id in data.evaluator_ids:
                assignment = HumanEvalAssignment(
                    campaign_id=campaign.id,
                    evaluator_id=evaluator_id,
                    eval_result_id=eval_result.id,
                )
                self.db.add(assignment)

        await self.db.flush()
        await self.db.refresh(campaign)
        return campaign

    async def submit_rating(
        self, assignment_id: uuid.UUID, data: HumanEvalRatingSubmit, user_id: uuid.UUID
    ) -> HumanEvalAssignment:
        result = await self.db.execute(select(HumanEvalAssignment).where(HumanEvalAssignment.id == assignment_id))
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        if assignment.evaluator_id != user_id:
            raise HTTPException(status_code=403, detail="Not your assignment")

        assignment.ratings = data.ratings
        assignment.notes = data.notes
        assignment.status = HumanEvalAssignmentStatus.COMPLETED
        assignment.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(assignment)
        return assignment
