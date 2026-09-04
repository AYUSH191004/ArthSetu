from fastapi import APIRouter

from backend.app.core.config import settings
from backend.app.db.session import check_db_connection

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check():
    db_ok = check_db_connection()

    return {
        "status": "ok" if db_ok else "degraded",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "database": "connected" if db_ok else "unreachable",
    }
