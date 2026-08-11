import logging

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies.database import DbSession
from app.schemas.health import DatabaseHealthResponse, HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=HealthResponse,
    summary="Application health check",
    description="Returns a simple status to confirm the API is running.",
)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/db",
    response_model=DatabaseHealthResponse,
    summary="Database health check",
    description="Verifies connectivity to PostgreSQL by executing a trivial query.",
)
def database_health(db: DbSession) -> DatabaseHealthResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Database health check failed")
        return DatabaseHealthResponse(status="error", database="unavailable")
    return DatabaseHealthResponse(status="ok", database="ok")
