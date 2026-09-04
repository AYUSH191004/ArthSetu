"""
Shared test fixtures.

A throwaway SQLite database is configured via env vars *before* any
`backend.app` module is imported, so the app's engine points at it.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest

_TMP_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_TMP_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB.name}"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

import bcrypt  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

# Speed up the suite: minimum bcrypt work factor is plenty for tests.
_orig_gensalt = bcrypt.gensalt
bcrypt.gensalt = lambda rounds=4, prefix=b"2b": _orig_gensalt(4, prefix)

from backend.app.db import models  # noqa: E402,F401  (register tables)
from backend.app.db.base import Base  # noqa: E402
from backend.app.db.enums import (  # noqa: E402
    EntityStatusEnum,
    LinkDecisionEnum,
    ReviewCaseStatusEnum,
    UserRole,
)
from backend.app.db.models.business_entity import BusinessEntity  # noqa: E402
from backend.app.db.models.entity_record_link import EntityRecordLink  # noqa: E402
from backend.app.db.models.review_case import ReviewCase  # noqa: E402
from backend.app.db.models.source_record import SourceRecord  # noqa: E402
from backend.app.db.models.source_system import SourceSystem  # noqa: E402
from backend.app.db.models.user import User  # noqa: E402
from backend.app.db.session import SessionLocal, engine  # noqa: E402
from backend.app.core.security import hash_password  # noqa: E402
from backend.app.services.scoring import normalize_address  # noqa: E402
from backend.app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_schema() -> Iterator[None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _teardown_file() -> None:
    try:
        os.unlink(_TMP_DB.name)
    except OSError:
        pass


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    _teardown_file()


@pytest.fixture
def db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def seed(db: Session) -> dict:
    """A small, deterministic dataset covering every role and match outcome."""

    users = {
        "admin": User(
            username="admin", full_name="Admin", role=UserRole.ADMIN,
            hashed_password=hash_password("adminpass"), is_active=True,
        ),
        "reviewer": User(
            username="rev", full_name="Reviewer", role=UserRole.REVIEWER,
            hashed_password=hash_password("revpass"), is_active=True,
        ),
        "viewer": User(
            username="view", full_name="Viewer", role=UserRole.VIEWER,
            hashed_password=hash_password("viewpass"), is_active=True,
        ),
    }
    db.add_all(users.values())

    system = SourceSystem(code="LABOUR", name="Labour Portal", department="Labour")
    db.add(system)
    db.flush()

    acme = BusinessEntity(
        ubid_code="UBID000001",
        legal_name="Acme Steel Works",
        normalized_name="acme steel works",
        pan="ABCDE1234F",
        gstin="03ABCDE1234F1Z5",
        address="Plot 42, Focal Point 3, Ludhiana, Punjab",
        normalized_address=normalize_address("Plot 42, Focal Point 3, Ludhiana, Punjab"),
        pin_code="141001",
        district="Ludhiana",
        sector="Manufacturing",
        status=EntityStatusEnum.ACTIVE,
    )
    beta = BusinessEntity(
        ubid_code="UBID000002",
        legal_name="Beta Traders",
        normalized_name="beta traders",
        pan="ZZZZZ9999Z",
        address="Shop 9, Grain Market, Mohali, Punjab",
        pin_code="160055",
        district="Mohali",
        sector="Retail",
        status=EntityStatusEnum.CLOSED,
    )
    db.add_all([acme, beta])
    db.flush()

    # A source record that clearly belongs to Acme (exact PAN + name).
    sr_match = SourceRecord(
        source_system_id=system.id,
        external_id="ext-match",
        raw_payload={"name": "ACME STEEL WORKS"},
        normalized_payload={"name": "acme steel works"},
        extracted_name="ACME STEEL WORKS",
        extracted_pan="ABCDE1234F",
        extracted_gstin="03ABCDE1234F1Z5",
        extracted_address="PLOT 42, FOCAL POINT, LUDHIANA",
        extracted_pin="141001",
    )
    # A source record with no plausible match.
    sr_new = SourceRecord(
        source_system_id=system.id,
        external_id="ext-new",
        raw_payload={"name": "Zephyr Logistics"},
        normalized_payload={"name": "zephyr logistics"},
        extracted_name="Zephyr Logistics",
        extracted_pan="QQQQQ0000Q",
        extracted_address="Plot 7, Transport Nagar, Amritsar",
        extracted_pin="143001",
    )
    db.add_all([sr_match, sr_new])
    db.flush()

    link = EntityRecordLink(
        source_record_id=sr_match.id,
        business_entity_id=acme.id,
        confidence=0.97,
        decision=LinkDecisionEnum.AUTO_LINK,
        explanation={"reasons": ["PAN exact match"]},
    )
    review = ReviewCase(
        source_record_id=sr_new.id,
        candidate_entity_id=beta.id,
        status=ReviewCaseStatusEnum.OPEN,
        confidence=0.6,
        evidence={"candidate_name": "Beta Traders", "reasons": ["weak name match"]},
        notes="needs a human",
    )
    db.add_all([link, review])
    db.commit()

    return {
        "acme_id": acme.id,
        "beta_id": beta.id,
        "sr_match_id": sr_match.id,
        "sr_new_id": sr_new.id,
        "review_id": review.id,
    }


@pytest.fixture
def token(client: TestClient):
    """token('admin'|'reviewer'|'viewer') -> Authorization header dict."""
    creds = {
        "admin": ("admin", "adminpass"),
        "reviewer": ("rev", "revpass"),
        "viewer": ("view", "viewpass"),
    }

    def _for(role: str = "admin") -> dict[str, str]:
        username, password = creds[role]
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": username, "password": password},
        )
        assert resp.status_code == 200, resp.text
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    return _for
