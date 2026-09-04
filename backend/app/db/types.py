"""Shared column helpers."""

from __future__ import annotations

import enum

from sqlalchemy import Enum as SAEnum


def str_enum(py_enum: type[enum.Enum], name: str) -> SAEnum:
    """
    A portable string-backed enum column.

    Stores the enum member's ``.value`` (e.g. "active"), as a VARCHAR with a
    CHECK constraint. Works identically on SQLite and PostgreSQL and avoids
    native ENUM-type migration headaches.
    """
    return SAEnum(
        py_enum,
        name=name,
        native_enum=False,
        validate_strings=True,
        values_callable=lambda e: [member.value for member in e],
    )
