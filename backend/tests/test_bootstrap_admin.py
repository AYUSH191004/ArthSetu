"""Covers _bootstrap_admin (backend/app/main.py) — the lifespan hook that
creates BOOTSTRAP_ADMIN_USERNAME/PASSWORD on a genuinely empty deployment,
since the fail-fast production config check (config.py) requires operators
to set a bootstrap password that has to actually do something."""

from fastapi.testclient import TestClient

from backend.app.db.models.user import User
from backend.app.main import app


class TestBootstrapAdmin:
    def test_creates_admin_on_empty_user_table(self, db):
        assert db.query(User).count() == 0

        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/auth/login",
                data={"username": "admin", "password": "arthsetu-admin"},
            )
            assert resp.status_code == 200
            assert resp.json()["user"]["role"] == "admin"

        assert db.query(User).filter(User.username == "admin").count() == 1

    def test_does_not_touch_a_non_empty_user_table(self, db, seed):
        before = db.query(User).count()
        assert before > 0

        with TestClient(app):
            pass

        assert db.query(User).count() == before
