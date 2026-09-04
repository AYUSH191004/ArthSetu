# ============================================================
# FILE: backend/app/services/event_scoring.py
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

# ------------------------------------------------------------
# Base event weights
#   positive => evidence of active operations
#   negative => evidence of closure / inactivity
# Keyed by EventTypeEnum *name* (upper-case).
# ------------------------------------------------------------

EVENT_BASE_WEIGHTS = {
    "GST_FILED": 0.95,
    "LICENSE_RENEWED": 0.90,
    "EMPLOYEE_FILING": 0.88,
    "PAYMENT_RECEIVED": 0.85,
    "POWER_USAGE": 0.82,
    "INSPECTION": 0.75,
    "DOCUMENT_UPDATE": 0.45,
    "COMPLAINT": 0.35,
    "ZERO_POWER_USAGE": -0.55,
    "SUSPENSION_NOTICE": -0.80,
    "CLOSURE_NOTICE": -1.00,
    "LICENSE_CANCELLED": -1.00,
}

DEFAULT_EVENT_WEIGHT = 0.20

# Events that unambiguously mean the business is closed.
HARD_CLOSURE_EVENTS = {"CLOSURE_NOTICE", "LICENSE_CANCELLED"}

# Recency decay buckets: (max_age_days, decay_factor)
DECAY_BUCKETS = [
    (30, 1.00),
    (90, 0.80),
    (180, 0.55),
    (365, 0.30),
]
DECAY_FLOOR = 0.10

# A decay factor at or above this counts the event as "recent".
RECENT_DECAY_CUTOFF = 0.80


@dataclass
class EventScore:
    event_type: str
    base: float
    decay: float
    age_days: int
    value: float

    @property
    def is_recent(self) -> bool:
        return self.decay >= RECENT_DECAY_CUTOFF

    @property
    def reason(self) -> str:
        return (
            f"{self.event_type}: base={round(self.base, 2)}, "
            f"age={self.age_days}d, decay={round(self.decay, 2)}, "
            f"score={round(self.value, 2)}"
        )


def _age_days(event_time: datetime) -> int:
    now = datetime.now(timezone.utc)
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc)
    return max((now - event_time).days, 0)


def age_decay(event_time: datetime) -> float:
    age = _age_days(event_time)
    for max_age, factor in DECAY_BUCKETS:
        if age <= max_age:
            return factor
    return DECAY_FLOOR


def score_event(event_type: str, event_time: datetime) -> EventScore:
    key = str(event_type).strip().upper().replace(" ", "_")
    base = EVENT_BASE_WEIGHTS.get(key, DEFAULT_EVENT_WEIGHT)
    age = _age_days(event_time)
    decay = age_decay(event_time)
    return EventScore(
        event_type=key,
        base=base,
        decay=decay,
        age_days=age,
        value=base * decay,
    )
