# ============================================================
# FILE: backend/app/services/matching_config_service.py
# DB-backed matching weights + reviewer-feedback calibration stats.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from backend.app.db.enums import ReviewCaseStatusEnum
from backend.app.db.models.matching_config import MatchingConfig
from backend.app.db.models.review_case import ReviewCase

UPDATABLE_FIELDS = (
    "gstin_weight",
    "pan_weight",
    "name_weight",
    "address_weight",
    "pin_weight",
    "pin_requires_name_sim",
    "auto_link_threshold",
    "review_threshold",
)


@dataclass(frozen=True)
class MatchingWeights:
    gstin_weight: float
    pan_weight: float
    name_weight: float
    address_weight: float
    pin_weight: float
    pin_requires_name_sim: float
    auto_link_threshold: float
    review_threshold: float


def _row(db: Session) -> MatchingConfig:
    """The single config row, created with defaults on first access."""
    row = db.query(MatchingConfig).first()
    if row is None:
        row = MatchingConfig()
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _to_weights(row: MatchingConfig) -> MatchingWeights:
    return MatchingWeights(**{f: getattr(row, f) for f in UPDATABLE_FIELDS})


def get_weights(db: Session) -> MatchingWeights:
    return _to_weights(_row(db))


def get_config_out(db: Session) -> Dict[str, Any]:
    row = _row(db)
    return {
        **{f: getattr(row, f) for f in UPDATABLE_FIELDS},
        "updated_by": row.updated_by,
        "updated_at": row.updated_at,
    }


def update_weights(
    db: Session, updates: Dict[str, Optional[float]], updated_by: str
) -> Dict[str, Any]:
    row = _row(db)
    for field in UPDATABLE_FIELDS:
        value = updates.get(field)
        if value is not None:
            setattr(row, field, value)
    row.updated_by = updated_by
    db.commit()
    db.refresh(row)
    return get_config_out(db)


# ------------------------------------------------------------
# Calibration: how well do the current thresholds line up with what
# reviewers actually decide? Decision support, not auto-tuning — an admin
# reads this and adjusts weights/thresholds accordingly.
# ------------------------------------------------------------

_BUCKETS = [
    (0.70, 0.80, "0.70 - 0.79"),
    (0.80, 0.90, "0.80 - 0.89"),
    (0.90, 0.92, "0.90 - 0.91"),
    (0.92, 1.01, "0.92 - 1.00 (auto-link range)"),
]


def _bucket_label(confidence: float) -> Optional[str]:
    for low, high, label in _BUCKETS:
        if low <= confidence < high:
            return label
    return None


def calibration_report(db: Session) -> Dict[str, Any]:
    cases = (
        db.query(ReviewCase)
        .filter(ReviewCase.confidence.isnot(None))
        .all()
    )

    bucket_stats = {label: {"total": 0, "approved": 0, "rejected": 0, "pending": 0} for _, _, label in _BUCKETS}
    signal_stats: Dict[str, Dict[str, int]] = {}

    for case in cases:
        label = _bucket_label(case.confidence or 0.0)
        if label is None:
            continue

        stats = bucket_stats[label]
        stats["total"] += 1
        status = case.status.value if hasattr(case.status, "value") else case.status
        if status == ReviewCaseStatusEnum.APPROVED.value:
            stats["approved"] += 1
        elif status == ReviewCaseStatusEnum.REJECTED.value:
            stats["rejected"] += 1
        else:
            stats["pending"] += 1

        if status in (ReviewCaseStatusEnum.APPROVED.value, ReviewCaseStatusEnum.REJECTED.value):
            key = "approved" if status == ReviewCaseStatusEnum.APPROVED.value else "rejected"
            evidence = case.evidence or {}
            for reason in evidence.get("reasons") or []:
                signal = str(reason).split(" ")[0].rstrip(":")
                signal_stats.setdefault(signal, {"approved": 0, "rejected": 0})[key] += 1

    buckets = []
    for _, _, label in _BUCKETS:
        stats = bucket_stats[label]
        decided = stats["approved"] + stats["rejected"]
        approve_rate = round(stats["approved"] / decided, 4) if decided else None
        buckets.append(
            {
                "label": label,
                "total": stats["total"],
                "approved": stats["approved"],
                "rejected": stats["rejected"],
                "pending": stats["pending"],
                "approve_rate": approve_rate,
            }
        )

    signals = [
        {"signal": signal, "approved": s["approved"], "rejected": s["rejected"]}
        for signal, s in sorted(signal_stats.items(), key=lambda kv: -(kv[1]["approved"] + kv[1]["rejected"]))
    ]

    return {
        "weights": get_config_out(db),
        "buckets": buckets,
        "signals": signals[:15],
        "sample_size": len(cases),
    }
