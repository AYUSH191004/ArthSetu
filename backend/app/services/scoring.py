# ============================================================
# FILE: backend/app/services/scoring.py
# ============================================================

from __future__ import annotations

import re
from typing import Optional
from rapidfuzz import fuzz


def normalize_text(value: Optional[str]) -> str:
    """
    Normalize text for matching:
    - handles None safely
    - uppercase
    - remove punctuation
    - collapse spaces
    """
    if not value:
        return ""

    value = value.upper().strip()
    value = re.sub(r"[^A-Z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def similarity(a: Optional[str], b: Optional[str]) -> float:
    """
    Token-sort similarity score from 0.0 to 1.0
    """
    na = normalize_text(a)
    nb = normalize_text(b)

    if not na or not nb:
        return 0.0

    return fuzz.token_sort_ratio(na, nb) / 100.0


def exact_match(a: Optional[str], b: Optional[str]) -> bool:
    """
    Safe exact comparison after normalization.
    """
    return bool(normalize_text(a) and normalize_text(a) == normalize_text(b))


def normalized_contains(a: Optional[str], b: Optional[str]) -> bool:
    """
    Returns True if one normalized string contains another.
    """
    na = normalize_text(a)
    nb = normalize_text(b)

    if not na or not nb:
        return False

    return na in nb or nb in na