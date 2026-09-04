from fastapi import APIRouter

from backend.app.api.v1.routes import (
    analytics,
    audit,
    business_public,
    dashboard,
    health,
    matching,
    review,
    status,
)

router = APIRouter()

router.include_router(health.router, tags=["Health"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
router.include_router(business_public.router, prefix="/business", tags=["Business"])
router.include_router(review.router, prefix="/reviews", tags=["Review"])
router.include_router(matching.router, prefix="/matching", tags=["Matching"])
router.include_router(status.router, prefix="/status", tags=["Status"])
router.include_router(audit.router, prefix="/audit", tags=["Audit"])
