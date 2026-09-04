from datetime import datetime, timedelta, timezone

from backend.app.services.event_scoring import (
    DEFAULT_EVENT_WEIGHT,
    HARD_CLOSURE_EVENTS,
    age_decay,
    score_event,
)

NOW = datetime.now(timezone.utc)


def test_age_decay_buckets_are_monotonic():
    d0 = age_decay(NOW - timedelta(days=1))
    d1 = age_decay(NOW - timedelta(days=60))
    d2 = age_decay(NOW - timedelta(days=120))
    d3 = age_decay(NOW - timedelta(days=300))
    d4 = age_decay(NOW - timedelta(days=1000))
    assert d0 == 1.0
    assert d0 >= d1 >= d2 >= d3 >= d4
    assert d4 == 0.10


def test_score_event_known_positive_signal():
    es = score_event("gst_filed", NOW - timedelta(days=5))
    assert es.base == 0.95
    assert es.decay == 1.0
    assert es.value == 0.95
    assert es.is_recent is True


def test_score_event_is_recency_weighted():
    recent = score_event("gst_filed", NOW - timedelta(days=5))
    old = score_event("gst_filed", NOW - timedelta(days=300))
    assert recent.value > old.value
    assert old.is_recent is False


def test_score_event_negative_signal():
    es = score_event("closure_notice", NOW - timedelta(days=10))
    assert es.base == -1.0
    assert es.value < 0


def test_unknown_event_type_uses_default_weight():
    es = score_event("totally_made_up", NOW)
    assert es.base == DEFAULT_EVENT_WEIGHT


def test_event_type_is_normalised():
    a = score_event("GST_FILED", NOW)
    b = score_event(" gst filed ", NOW)
    assert a.base == b.base == 0.95


def test_hard_closure_set():
    assert "CLOSURE_NOTICE" in HARD_CLOSURE_EVENTS
    assert "LICENSE_CANCELLED" in HARD_CLOSURE_EVENTS
