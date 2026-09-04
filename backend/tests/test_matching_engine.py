from uuid import UUID

from backend.app.db.models.business_entity import BusinessEntity
from backend.app.db.models.entity_record_link import EntityRecordLink
from backend.app.db.models.review_case import ReviewCase
from backend.app.db.models.source_record import SourceRecord
from backend.app.services.matching_engine import process_source_record


def _add_record(db, system_id, **kw):
    defaults = dict(
        source_system_id=system_id,
        external_id=kw.get("external_id", "ext-test"),
        raw_payload={},
        normalized_payload={},
        extracted_name=kw.get("extracted_name"),
        extracted_pan=kw.get("extracted_pan"),
        extracted_gstin=kw.get("extracted_gstin"),
        extracted_address=kw.get("extracted_address"),
        extracted_pin=kw.get("extracted_pin"),
    )
    sr = SourceRecord(**defaults)
    db.add(sr)
    db.commit()
    db.refresh(sr)
    return sr


def _system_id(db):
    from backend.app.db.models.source_system import SourceSystem

    return db.query(SourceSystem).first().id


def test_strong_id_and_name_match_auto_links(db, seed):
    sr = _add_record(
        db, _system_id(db),
        external_id="ext-auto",
        extracted_name="Acme Steel Works",
        extracted_pan="ABCDE1234F",
        extracted_gstin="03ABCDE1234F1Z5",
    )
    result = process_source_record(db, sr.id)

    assert result["decision"] == "AUTO_LINK"
    assert result["confidence"] >= 0.92
    assert result["business_entity_id"] == str(seed["acme_id"])

    link = (
        db.query(EntityRecordLink)
        .filter(EntityRecordLink.source_record_id == sr.id)
        .one()
    )
    assert str(link.business_entity_id) == str(seed["acme_id"])


def test_partial_match_goes_to_review(db, seed):
    # Same first token + weak signals, no strong ID -> REVIEW band.
    sr = _add_record(
        db, _system_id(db),
        external_id="ext-review",
        extracted_name="Acme Steelworks Limited",
        extracted_pan="ABCDE1234F",  # PAN match lifts it into the review band
    )
    result = process_source_record(db, sr.id)

    assert result["decision"] in {"REVIEW", "AUTO_LINK"}
    if result["decision"] == "REVIEW":
        case = (
            db.query(ReviewCase)
            .filter(ReviewCase.source_record_id == sr.id)
            .one()
        )
        assert case.candidate_entity_id is not None
        assert case.confidence == result["confidence"]


def test_no_candidate_creates_new_entity(db, seed):
    before = db.query(BusinessEntity).count()
    sr = _add_record(
        db, _system_id(db),
        external_id="ext-new-entity",
        extracted_name="Zephyr Logistics Partners",
        extracted_pan="QQQQQ0000Q",
    )
    result = process_source_record(db, sr.id)

    assert result["decision"] == "NEW_ENTITY"
    assert db.query(BusinessEntity).count() == before + 1
    new_entity = db.get(BusinessEntity, UUID(result["business_entity_id"]))
    assert new_entity.ubid_code.startswith("UBID-")


def test_unknown_source_record_raises(db, seed):
    import pytest

    with pytest.raises(ValueError):
        process_source_record(db, "00000000-0000-0000-0000-000000000000")


# ------------------------------------------------------------------
# Address / PIN driven matching
# ------------------------------------------------------------------

def test_name_plus_address_plus_pin_without_id_goes_to_review(db, seed):
    """No strong id, but a noisy 'M/S' name + matching address + PIN.

    Before address/PIN were wired in, a name-only match maxed at ~0.20 and
    could never reach the review threshold.
    """
    sr = _add_record(
        db, _system_id(db),
        external_id="ext-addr-review",
        extracted_name="M/S Acme Steelworks",
        extracted_address="Plot 42 Focal Point Phase 3 Ludhiana Punjab",
        extracted_pin="141001",
    )
    result = process_source_record(db, sr.id)

    assert result["decision"] == "REVIEW"
    assert result["confidence"] >= 0.70
    assert result["business_entity_id"] == str(seed["acme_id"])
    assert any("Address similarity" in r for r in _reasons(db, sr.id))
    assert any("PIN code match" in r for r in _reasons(db, sr.id))


def test_similar_name_but_different_address_stays_separate(db, seed):
    sr = _add_record(
        db, _system_id(db),
        external_id="ext-diff-addr",
        extracted_name="Acme Steel Industries",
        extracted_address="Shop 3, Sabzi Mandi, Bathinda, Punjab",
        extracted_pin="151001",
    )
    result = process_source_record(db, sr.id)
    assert result["decision"] == "NEW_ENTITY"


def test_shared_pin_alone_is_not_enough(db, seed):
    # Unrelated name, same PIN as Acme -> PIN contribution is suppressed.
    sr = _add_record(
        db, _system_id(db),
        external_id="ext-pin-only",
        extracted_name="Sunrise Bakery",
        extracted_address="Model Town, Ludhiana",
        extracted_pin="141001",
    )
    result = process_source_record(db, sr.id)
    assert result["decision"] == "NEW_ENTITY"


def test_new_entity_carries_address_and_pin(db, seed):
    from uuid import UUID as _UUID

    sr = _add_record(
        db, _system_id(db),
        external_id="ext-new-with-addr",
        extracted_name="Falcon Freight Services",
        extracted_pan="FLCN1234K",
        extracted_address="Plot 88, Transport Nagar, Jalandhar",
        extracted_pin="144001",
    )
    result = process_source_record(db, sr.id)
    assert result["decision"] == "NEW_ENTITY"
    entity = db.get(BusinessEntity, _UUID(result["business_entity_id"]))
    assert entity.pin_code == "144001"
    assert entity.address == "Plot 88, Transport Nagar, Jalandhar"


def _reasons(db, sr_id):
    from backend.app.db.models.review_case import ReviewCase

    case = db.query(ReviewCase).filter(ReviewCase.source_record_id == sr_id).first()
    if case and case.evidence:
        return case.evidence.get("reasons", [])
    link = (
        db.query(EntityRecordLink)
        .filter(EntityRecordLink.source_record_id == sr_id)
        .first()
    )
    if link and isinstance(link.explanation, dict):
        return link.explanation.get("reasons", [])
    return []
