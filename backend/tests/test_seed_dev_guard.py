"""Covers the production guard in backend/seed_dev.py — the demo seeder
drops tables and installs publicly-known passwords, so it must refuse to
run against APP_ENV=production unless explicitly forced."""

import pytest

from backend import seed_dev
from backend.app.core.config import settings


class TestProductionGuard:
    def test_refuses_reset_in_production_without_force(self, monkeypatch):
        monkeypatch.setattr(settings, "APP_ENV", "production")
        with pytest.raises(SystemExit):
            seed_dev.reset()

    def test_refuses_seed_in_production_without_force(self, monkeypatch):
        monkeypatch.setattr(settings, "APP_ENV", "production")
        with pytest.raises(SystemExit):
            seed_dev.seed()

    def test_force_flag_bypasses_the_guard(self, monkeypatch, db):
        monkeypatch.setattr(settings, "APP_ENV", "production")
        seed_dev.reset(force=True)  # must not raise

    def test_allows_normal_run_outside_production(self, monkeypatch):
        monkeypatch.setattr(settings, "APP_ENV", "development")
        seed_dev._refuse_in_production(force=False)  # must not raise
