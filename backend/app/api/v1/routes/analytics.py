# ============================================================
# FILE: backend/app/api/v1/routes/analytics.py
# ============================================================

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.business_entity import BusinessEntity
from backend.app.db.models.activity_event import ActivityEvent
from backend.app.db.enums import EntityStatusEnum
from backend.app.schemas import (
    AnalyticsSummaryResponse,
    DistrictRow,
    TrendPoint,
)

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def summary(db: Session = Depends(get_db)):
    counts = dict(
        db.query(BusinessEntity.status, func.count(BusinessEntity.id))
        .group_by(BusinessEntity.status)
        .all()
    )

    def c(s):
        return int(counts.get(s, 0) or 0)

    return AnalyticsSummaryResponse(
        total_businesses=sum(int(v or 0) for v in counts.values()),
        active=c(EntityStatusEnum.ACTIVE),
        dormant=c(EntityStatusEnum.DORMANT),
        closed=c(EntityStatusEnum.CLOSED),
        unknown=c(EntityStatusEnum.UNKNOWN),
    )


@router.get("/trends", response_model=list[TrendPoint])
def monthly_trends(db: Session = Depends(get_db)):
    rows = (
        db.query(ActivityEvent.event_type, ActivityEvent.created_at)
        .order_by(ActivityEvent.created_at.asc())
        .all()
    )

    monthly: dict[str, int] = {}
    for _etype, created_at in rows:
        if created_at is None:
            continue
        key = created_at.strftime("%Y-%m")
        monthly[key] = monthly.get(key, 0) + 1

    return [TrendPoint(month=k, events=v) for k, v in sorted(monthly.items())]


@router.get("/districts", response_model=list[DistrictRow])
def districts(db: Session = Depends(get_db)):
    rows = (
        db.query(
            BusinessEntity.district,
            BusinessEntity.status,
            func.count(BusinessEntity.id),
        )
        .group_by(BusinessEntity.district, BusinessEntity.status)
        .all()
    )

    agg: dict[str, dict] = {}
    for district, status, n in rows:
        name = district or "Unknown"
        bucket = agg.setdefault(
            name,
            {"total": 0, "active": 0, "dormant": 0, "closed": 0, "unknown": 0},
        )
        n = int(n or 0)
        bucket["total"] += n
        key = status.value if hasattr(status, "value") else str(status)
        if key in bucket:
            bucket[key] += n

    out = [
        DistrictRow(
            district=name,
            total=b["total"],
            active=b["active"],
            dormant=b["dormant"],
            closed=b["closed"],
            unknown=b["unknown"],
        )
        for name, b in agg.items()
    ]
    out.sort(key=lambda r: r.total, reverse=True)
    return out
