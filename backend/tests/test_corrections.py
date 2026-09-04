from uuid import UUID

from backend.app.db.models.activity_event import ActivityEvent
from backend.app.db.models.business_entity import BusinessEntity
from backend.app.db.models.entity_record_link import EntityRecordLink
from backend.app.db.models.review_case import ReviewCase
from backend.app.db.enums import EventTypeEnum
from backend.app.services import corrections_service as svc


def _link_id(db, seed):
    link = (
        db.query(EntityRecordLink)
        .filter(EntityRecordLink.business_entity_id == seed["acme_id"])
        .first()
    )
    return link.id


def _add_event(db, entity_id):
    ev = ActivityEvent(
        business_entity_id=entity_id,
        event_type=EventTypeEnum.GST_FILED,
        score=0.9,
        payload={},
    )
    db.add(ev)
    db.commit()
    return ev.id


class TestStatusOverride:
    def test_pins_status_and_engine_respects_it(self, db, seed):
        svc.override_status(db, "UBID000001", "rev", "closed", "verified shut")
        entity = db.get(BusinessEntity, seed["acme_id"])
        assert entity.status.value == "closed"
        assert entity.status_locked is True
        assert entity.status_overridden_by == "rev"

        from backend.app.services.status_engine import infer_business_status

        result = infer_business_status(db, seed["acme_id"])
        assert result["status"] == "CLOSED"          # effective (pinned)
        assert result["locked"] is True
        db.refresh(entity)
        assert entity.status.value == "closed"        # engine did not overwrite

    def test_clear_recomputes(self, db, seed):
        svc.override_status(db, "UBID000001", "rev", "closed", "x")
        svc.clear_status_override(db, "UBID000001", "rev")
        entity = db.get(BusinessEntity, seed["acme_id"])
        assert entity.status_locked is False
        assert entity.status_override_reason is None

    def test_clear_without_override_errors(self, db, seed):
        import pytest

        with pytest.raises(ValueError):
            svc.clear_status_override(db, "UBID000001", "rev")

    def test_undo_restores_previous(self, db, seed):
        entity = db.get(BusinessEntity, seed["acme_id"])
        original = entity.status.value
        res = svc.override_status(db, "UBID000001", "rev", "dormant", "temp")
        svc.undo(db, res["audit_id"], "rev")
        db.refresh(entity)
        assert entity.status.value == original
        assert entity.status_locked is False


class TestSplit:
    def test_reopen_review_removes_link_and_creates_case(self, db, seed):
        link_id = _link_id(db, seed)
        res = svc.split_link(db, str(link_id), "rev", "wrong firm", "reopen_review")
        assert db.get(EntityRecordLink, link_id) is None
        case_id = UUID(res["detail"]["review_case_id"])
        assert db.get(ReviewCase, case_id).status.value == "open"

    def test_new_entity_moves_link_to_a_fresh_business(self, db, seed):
        link_id = _link_id(db, seed)
        before = db.query(BusinessEntity).count()
        res = svc.split_link(db, str(link_id), "rev", "different premises", "new_entity")
        assert db.query(BusinessEntity).count() == before + 1
        link = db.get(EntityRecordLink, link_id)
        assert str(link.business_entity_id) == res["detail"]["to_entity_id"]

    def test_undo_new_entity_split_relinks_and_drops_stray(self, db, seed):
        link_id = _link_id(db, seed)
        before = db.query(BusinessEntity).count()
        res = svc.split_link(db, str(link_id), "rev", "oops", "new_entity")
        svc.undo(db, res["audit_id"], "rev")
        link = db.get(EntityRecordLink, link_id)
        assert str(link.business_entity_id) == str(seed["acme_id"])
        assert db.query(BusinessEntity).count() == before  # stray removed

    def test_undo_reopen_split_recreates_link(self, db, seed):
        link_id = _link_id(db, seed)
        res = svc.split_link(db, str(link_id), "rev", "oops", "reopen_review")
        svc.undo(db, res["audit_id"], "rev")
        relinked = (
            db.query(EntityRecordLink)
            .filter(EntityRecordLink.business_entity_id == seed["acme_id"])
            .count()
        )
        assert relinked == 1


class TestReassign:
    def test_moves_event_and_undo_moves_it_back(self, db, seed):
        eid = _add_event(db, seed["acme_id"])
        res = svc.reassign_event(db, str(eid), "rev", "UBID000002", "misfiled")
        assert str(db.get(ActivityEvent, eid).business_entity_id) == str(seed["beta_id"])

        svc.undo(db, res["audit_id"], "rev")
        assert str(db.get(ActivityEvent, eid).business_entity_id) == str(seed["acme_id"])

    def test_reassign_to_same_entity_errors(self, db, seed):
        import pytest

        eid = _add_event(db, seed["acme_id"])
        with pytest.raises(ValueError):
            svc.reassign_event(db, str(eid), "rev", "UBID000001", "x")


class TestUndoGuards:
    def test_cannot_undo_twice(self, db, seed):
        import pytest

        res = svc.override_status(db, "UBID000001", "rev", "dormant", "x")
        svc.undo(db, res["audit_id"], "rev")
        with pytest.raises(ValueError, match="already been undone"):
            svc.undo(db, res["audit_id"], "rev")

    def test_cannot_undo_non_reversible(self, db, seed):
        import pytest

        from backend.app.db.models.audit_log import AuditLog
        from backend.app.db.enums import AuditActorEnum

        a = AuditLog(
            actor_type=AuditActorEnum.SYSTEM, action="STATUS_UPDATED",
            entity_type="business_entity", entity_id="x",
        )
        db.add(a)
        db.commit()
        with pytest.raises(ValueError):
            svc.undo(db, str(a.id), "rev")


class TestCorrectionsApi:
    def test_reviewer_only(self, client, seed, token):
        body = {"status": "closed", "reason": "x"}
        assert (
            client.post(
                "/api/v1/corrections/entities/UBID000001/status-override",
                json=body, headers=token("viewer"),
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/v1/corrections/entities/UBID000001/status-override",
                json=body, headers=token("reviewer"),
            ).status_code
            == 200
        )

    def test_history_and_undo_flow(self, client, seed, token):
        headers = token("reviewer")
        res = client.post(
            "/api/v1/corrections/entities/UBID000001/status-override",
            json={"status": "dormant", "reason": "field check"},
            headers=headers,
        ).json()

        hist = client.get("/api/v1/corrections", headers=headers).json()
        assert hist["total"] >= 1
        entry = next(i for i in hist["items"] if i["audit_id"] == res["audit_id"])
        assert entry["reversible"] is True
        assert entry["undone"] is False

        client.post(f"/api/v1/corrections/undo/{res['audit_id']}", headers=headers)
        hist2 = client.get("/api/v1/corrections", headers=headers).json()
        entry2 = next(i for i in hist2["items"] if i["audit_id"] == res["audit_id"])
        assert entry2["undone"] is True
        assert entry2["reversible"] is False
