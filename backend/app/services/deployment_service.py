import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deployment import Deployment
from app.models.enums import DeploymentStatus
from app.models.prompt import PromptVersion
from app.schemas.deployment import DeploymentCreate


class DeploymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_deployment(self, data: DeploymentCreate, user_id: uuid.UUID) -> Deployment:
        # Get prompt version to find application_id
        result = await self.db.execute(
            select(PromptVersion).where(PromptVersion.id == data.prompt_version_id)
        )
        version = result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="Prompt version not found")

        # Get template for application_id
        from app.models.prompt import PromptTemplate
        template_result = await self.db.execute(
            select(PromptTemplate).where(PromptTemplate.id == version.template_id)
        )
        template = template_result.scalar_one()

        # Get current production version
        current_prod = await self.db.execute(
            select(PromptVersion).where(
                PromptVersion.template_id == version.template_id,
                PromptVersion.tag == "production",
            )
        )
        current = current_prod.scalar_one_or_none()

        deployment = Deployment(
            application_id=template.application_id,
            prompt_version_id=data.prompt_version_id,
            status=DeploymentStatus.PENDING_EVAL,
            canary_pct=data.canary_pct,
            previous_version_id=current.id if current else None,
            deployed_by=user_id,
        )
        self.db.add(deployment)
        await self.db.flush()
        await self.db.refresh(deployment)
        return deployment

    async def promote(self, deployment_id: uuid.UUID) -> Deployment:
        result = await self.db.execute(
            select(Deployment).where(Deployment.id == deployment_id)
        )
        deployment = result.scalar_one_or_none()
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")

        if deployment.status not in (DeploymentStatus.CANARY, DeploymentStatus.EVAL_PASSED):
            raise HTTPException(status_code=400, detail=f"Cannot promote deployment in status: {deployment.status}")

        # Progressive canary: 10 -> 25 -> 50 -> 100
        stages = [10, 25, 50, 100]
        current_idx = -1
        for i, s in enumerate(stages):
            if deployment.canary_pct <= s:
                current_idx = i
                break

        if current_idx < len(stages) - 1:
            deployment.canary_pct = stages[current_idx + 1]
            deployment.status = DeploymentStatus.CANARY
        else:
            deployment.canary_pct = 100
            deployment.status = DeploymentStatus.ROLLED_OUT
            # Tag prompt version as production
            version_result = await self.db.execute(
                select(PromptVersion).where(PromptVersion.id == deployment.prompt_version_id)
            )
            version = version_result.scalar_one()

            # Remove production tag from other versions
            existing = await self.db.execute(
                select(PromptVersion).where(
                    PromptVersion.template_id == version.template_id,
                    PromptVersion.tag == "production",
                )
            )
            for v in existing.scalars().all():
                v.tag = None
            version.tag = "production"

        await self.db.flush()
        await self.db.refresh(deployment)
        return deployment

    async def rollback(self, deployment_id: uuid.UUID) -> Deployment:
        result = await self.db.execute(
            select(Deployment).where(Deployment.id == deployment_id)
        )
        deployment = result.scalar_one_or_none()
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")

        deployment.status = DeploymentStatus.ROLLED_BACK
        deployment.canary_pct = 0

        # Restore previous version as production if it exists
        if deployment.previous_version_id:
            prev_result = await self.db.execute(
                select(PromptVersion).where(PromptVersion.id == deployment.previous_version_id)
            )
            prev = prev_result.scalar_one_or_none()
            if prev:
                prev.tag = "production"

        await self.db.flush()
        await self.db.refresh(deployment)
        return deployment
