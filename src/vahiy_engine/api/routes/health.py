"""GET /health endpoint."""

from fastapi import APIRouter

from vahiy_engine.api.schemas.health import HealthResponse
from vahiy_engine.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    return HealthResponse(status="ok", version=settings.app_version)
