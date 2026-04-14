import difflib
import re
import uuid

import jinja2
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt import PromptTemplate, PromptVersion
from app.schemas.prompt import PromptDiffDetailedResponse, PromptDiffResponse, PromptRenderResponse, PromptVersionCreate, PromptVersionResponse


class PromptService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_version(
        self, template_id: uuid.UUID, data: PromptVersionCreate, user_id: uuid.UUID
    ) -> PromptVersion:
        # Get next version number
        result = await self.db.execute(
            select(func.coalesce(func.max(PromptVersion.version_number), 0))
            .where(PromptVersion.template_id == template_id)
        )
        next_version = result.scalar() + 1

        # Extract variables from template content
        variables = data.variables or self._extract_variables(data.content)

        version = PromptVersion(
            template_id=template_id,
            version_number=next_version,
            content=data.content,
            variables=variables,
            model_config_json=data.model_config_data,
            tag=data.tag,
            commit_message=data.commit_message,
            created_by=user_id,
        )
        self.db.add(version)
        await self.db.flush()
        await self.db.refresh(version)
        return version

    async def tag_version(self, template_id: uuid.UUID, version_number: int, tag: str) -> PromptVersion:
        # If tagging as production, remove production tag from other versions
        if tag == "production":
            result = await self.db.execute(
                select(PromptVersion).where(
                    PromptVersion.template_id == template_id,
                    PromptVersion.tag == "production",
                )
            )
            for v in result.scalars().all():
                v.tag = None

        result = await self.db.execute(
            select(PromptVersion).where(
                PromptVersion.template_id == template_id,
                PromptVersion.version_number == version_number,
            )
        )
        version = result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        version.tag = tag
        await self.db.flush()
        await self.db.refresh(version)
        return version

    async def rollback_to_version(
        self, template_id: uuid.UUID, version_number: int, user_id: uuid.UUID
    ) -> PromptVersion:
        result = await self.db.execute(
            select(PromptVersion).where(
                PromptVersion.template_id == template_id,
                PromptVersion.version_number == version_number,
            )
        )
        old_version = result.scalar_one_or_none()
        if not old_version:
            raise HTTPException(status_code=404, detail="Version not found")

        # Create a new version with the old content
        return await self.create_version(
            template_id,
            PromptVersionCreate(
                content=old_version.content,
                variables=old_version.variables,
                model_config_data=old_version.model_config_json,
                commit_message=f"Rollback to version {version_number}",
            ),
            user_id,
        )

    async def diff_versions(
        self, template_id: uuid.UUID, v1: int, v2: int
    ) -> PromptDiffResponse:
        result1 = await self.db.execute(
            select(PromptVersion).where(
                PromptVersion.template_id == template_id,
                PromptVersion.version_number == v1,
            )
        )
        result2 = await self.db.execute(
            select(PromptVersion).where(
                PromptVersion.template_id == template_id,
                PromptVersion.version_number == v2,
            )
        )
        ver1 = result1.scalar_one_or_none()
        ver2 = result2.scalar_one_or_none()
        if not ver1 or not ver2:
            raise HTTPException(status_code=404, detail="One or both versions not found")

        return PromptDiffResponse(
            v1=v1, v2=v2, v1_content=ver1.content, v2_content=ver2.content
        )

    async def diff_versions_detailed(
        self, template_id: uuid.UUID, v1: int, v2: int
    ) -> PromptDiffDetailedResponse:
        result1 = await self.db.execute(
            select(PromptVersion).where(
                PromptVersion.template_id == template_id,
                PromptVersion.version_number == v1,
            )
        )
        result2 = await self.db.execute(
            select(PromptVersion).where(
                PromptVersion.template_id == template_id,
                PromptVersion.version_number == v2,
            )
        )
        ver1 = result1.scalar_one_or_none()
        ver2 = result2.scalar_one_or_none()
        if not ver1 or not ver2:
            raise HTTPException(status_code=404, detail="One or both versions not found")

        # Compute line-level diff stats
        lines1 = ver1.content.splitlines()
        lines2 = ver2.content.splitlines()
        diff = list(difflib.unified_diff(lines1, lines2, lineterm=""))

        lines_added = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
        lines_removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))

        # Count changed lines via SequenceMatcher
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        lines_changed = 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "replace":
                lines_changed += max(i2 - i1, j2 - j1)

        # Variable diff
        v1_vars = set(self._extract_variables(ver1.content).keys())
        v2_vars = set(self._extract_variables(ver2.content).keys())

        return PromptDiffDetailedResponse(
            v1=v1,
            v2=v2,
            v1_content=ver1.content,
            v2_content=ver2.content,
            v1_tag=ver1.tag,
            v2_tag=ver2.tag,
            v1_commit_message=ver1.commit_message,
            v2_commit_message=ver2.commit_message,
            v1_created_at=ver1.created_at,
            v2_created_at=ver2.created_at,
            v1_variables=sorted(v1_vars),
            v2_variables=sorted(v2_vars),
            variables_added=sorted(v2_vars - v1_vars),
            variables_removed=sorted(v1_vars - v2_vars),
            lines_added=lines_added,
            lines_removed=lines_removed,
            lines_changed=lines_changed,
        )

    async def render(
        self, template_id: uuid.UUID, variables: dict, version_number: int | None = None
    ) -> PromptRenderResponse:
        if version_number:
            result = await self.db.execute(
                select(PromptVersion).where(
                    PromptVersion.template_id == template_id,
                    PromptVersion.version_number == version_number,
                )
            )
        else:
            # Get production version or latest
            result = await self.db.execute(
                select(PromptVersion)
                .where(PromptVersion.template_id == template_id)
                .order_by(PromptVersion.version_number.desc())
                .limit(1)
            )
        version = result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="No version found")

        env = jinja2.Environment(undefined=jinja2.StrictUndefined)
        template = env.from_string(version.content)
        rendered = template.render(**variables)

        return PromptRenderResponse(rendered=rendered, version_number=version.version_number)

    @staticmethod
    def _extract_variables(content: str) -> dict:
        pattern = r"\{\{\s*(\w+)\s*\}\}"
        var_names = list(set(re.findall(pattern, content)))
        return {name: "" for name in var_names}
