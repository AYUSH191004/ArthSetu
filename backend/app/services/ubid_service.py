# ============================================================
# FILE: backend/app/services/ubid_service.py
# ============================================================

from __future__ import annotations

import secrets


def generate_ubid() -> str:
    """
    Generate clean production UBID.
    Example:
        UBID-8A12BC93D1
    """
    token = secrets.token_hex(5).upper()
    return f"UBID-{token}"