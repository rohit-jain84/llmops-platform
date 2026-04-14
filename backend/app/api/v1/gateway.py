import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.gateway_service import GatewayService

router = APIRouter()


class GatewayRequest(BaseModel):
    application_id: uuid.UUID
    prompt_template_id: uuid.UUID
    variables: dict = {}
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    user_id: str | None = None


class GatewayResponse(BaseModel):
    response: str
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    cache_hit: bool
    trace_id: str | None = None
    variant_id: str | None = None


@router.post("/chat", response_model=GatewayResponse)
async def gateway_chat(
    request: GatewayRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = GatewayService(db)
    return await svc.handle_chat(request)
