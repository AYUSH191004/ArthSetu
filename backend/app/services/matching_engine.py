# ============================================================
# FILE: backend/app/services/match_engine.py
# ============================================================

from __future__ import annotations
from uuid import UUID
import json
import enum
from datetime import datetime, date
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.services.scoring import similarity, normalize_text
from backend.app.services.ubid_service import generate_ubid

from backend.app.db.models.business_entity import BusinessEntity
from backend.app.db.models.source_record import SourceRecord
from backend.app.db.models.entity_record_link import EntityRecordLink
from backend.app.db.models.review_case import ReviewCase
from backend.app.db.models.audit_log import AuditLog

from backend.app.db.enums import (
    LinkDecisionEnum,
    ReviewCaseStatusEnum,
    AuditActorEnum,
    EntityStatusEnum,
)

# ============================================================
# THRESHOLDS
# ============================================================

AUTO_LINK_THRESHOLD = 0.92
REVIEW_THRESHOLD = 0.70

# ============================================================
# WEIGHTS
# ============================================================

GSTIN_WEIGHT = 0.60
PAN_WEIGHT = 0.55
NAME_WEIGHT = 0.20
ADDRESS_WEIGHT = 0.15
PIN_WEIGHT = 0.05


# ============================================================
# RESPONSE DTO
# ============================================================

@dataclass
class MatchResult:
    decision: str
    confidence: float
    business_entity_id: Optional[str]
    reasons: List[str]

##Normalize JSON-ish DB values into a dict.
def _as_dict(value):
    """
    Normalize JSON-ish DB values into a dict.

    Handles:
    - dict -> returned as-is
    - JSON string -> parsed into dict
    - None / invalid / other -> {}
    """
    if value is None:
        return {}

    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return {}
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    return {}
    ##json normaization
def _json_safe(value):
    """
    Recursively convert Python objects into JSON-serializable values.
    Handles UUID, Enum, datetime/date, dict, list, tuple, set.
    """
    if value is None:
        return None

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, enum.Enum):
        return value.value

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]

    return value
# ============================================================
# PUBLIC ENTRYPOINT
# ============================================================

def process_source_record(
    db: Session,
    source_record_id: UUID | str,
) -> Dict[str, Any]:
    """
    Main entrypoint.

    Accepts a new source_record and decides:

    1. AUTO_LINK
    2. REVIEW
    3. NEW_ENTITY
    """

    if not isinstance(source_record_id, UUID):
        try:
            source_record_id = UUID(str(source_record_id))
        except (ValueError, TypeError):
            raise ValueError("Invalid source_record_id")

    source_record = db.get(SourceRecord, source_record_id)
    if not source_record:
        raise ValueError("SourceRecord not found")

    try:
        candidates = _find_candidates(db, source_record)

        if not candidates:
            result = _create_new_entity(db, source_record)
            db.commit()
            return _to_dict(result)

        best_entity, score, reasons = _best_candidate(source_record, candidates)

        if score >= AUTO_LINK_THRESHOLD:
            result = _auto_link(
                db=db,
                source_record=source_record,
                entity=best_entity,
                score=score,
                reasons=reasons,
            )

        elif score >= REVIEW_THRESHOLD:
            result = _create_review_case(
                db=db,
                source_record=source_record,
                entity=best_entity,
                score=score,
                reasons=reasons,
            )

        else:
            result = _create_new_entity(db, source_record)

        db.commit()
        return _to_dict(result)

    except Exception:
        db.rollback()
        raise


# ============================================================
# CANDIDATE BLOCKING
# ============================================================

def _find_candidates(
    db: Session,
    source_record: SourceRecord,
) -> List[BusinessEntity]:
    """
    Conservative blocking.
    Avoid full-table scans.
    """

    name = normalize_text(source_record.extracted_name)
    first_token = name.split(" ")[0] if name else None

    conditions = []

    if source_record.extracted_gstin:
        conditions.append(
            BusinessEntity.gstin == source_record.extracted_gstin
        )

    if source_record.extracted_pan:
        conditions.append(
            BusinessEntity.pan == source_record.extracted_pan
        )

    if first_token:
        conditions.append(
            BusinessEntity.normalized_name.ilike(f"{first_token}%")
        )

    if not conditions:
        return []

    return (
        db.query(BusinessEntity)
        .filter(or_(*conditions))
        .limit(25)
        .all()
    )


# ============================================================
# SCORING
# ============================================================

def _best_candidate(
    source_record: SourceRecord,
    candidates: List[BusinessEntity],
) -> Tuple[BusinessEntity, float, List[str]]:

    best_score = -1.0
    best_entity = candidates[0]
    best_reasons: List[str] = []

    for entity in candidates:
        score, reasons = _score_candidate(source_record, entity)

        if score > best_score:
            best_score = score
            best_entity = entity
            best_reasons = reasons

    return best_entity, round(best_score, 4), best_reasons


def _score_candidate(
    source_record: SourceRecord,
    entity: BusinessEntity,
    ) -> Tuple[float, List[str]]:

    score = 0.0
    reasons: List[str] = []

    # normalized_payload may come back as dict or JSON string
    sr_payload = _as_dict(source_record.normalized_payload)

    # Strong IDs
    if (
        source_record.extracted_gstin
        and entity.gstin
        and source_record.extracted_gstin == entity.gstin
    ):
        score += GSTIN_WEIGHT
        reasons.append("GSTIN exact match")

    if (
        source_record.extracted_pan
        and entity.pan
        and source_record.extracted_pan == entity.pan
    ):
        score += PAN_WEIGHT
        reasons.append("PAN exact match")

    # Name similarity
    name_score = similarity(
        source_record.extracted_name,
        entity.legal_name,
    )
    score += NAME_WEIGHT * name_score
    reasons.append(f"Name similarity {round(name_score, 2)}")

    # Optional note: source payload contains address/pin, but BusinessEntity
    # currently has no address/pin fields to compare against, so we do not
    # add address/pin score here.
    source_address = sr_payload.get("address")
    source_pin = sr_payload.get("pin_code")

    if source_address:
        reasons.append("Source address present")
    if source_pin:
        reasons.append("Source pin present")

    score = min(score, 1.0)
    return score, reasons

# ============================================================
# DECISIONS
# ============================================================

def _auto_link(
    db: Session,
    source_record: SourceRecord,
    entity: BusinessEntity,
    score: float,
    reasons: List[str],
) -> MatchResult:

    link = EntityRecordLink(
        source_record_id=source_record.id,
        business_entity_id=entity.id,
        confidence=score,
        decision=LinkDecisionEnum.AUTO_LINK,
        explanation=reasons,
    )

    db.add(link)

    _audit(
        db,
        entity_type="business_entity",
        entity_id=str(entity.id),
        action="AUTO_LINK",
        after_state=_json_safe(
            {
                "source_record_id": source_record.id,
                "confidence": score,
                "reasons": reasons,
            }
        ),
    )

    return MatchResult(
        decision="AUTO_LINK",
        confidence=score,
        business_entity_id=entity.id,
        reasons=reasons,
    )


def _create_review_case(
    db: Session,
    source_record: SourceRecord,
    entity: BusinessEntity,
    score: float,
    reasons: List[str],
) -> MatchResult:

    review = ReviewCase(
        source_record_id=source_record.id,
        candidate_entity_id=entity.id,
        status=ReviewCaseStatusEnum.OPEN,
        confidence=score,
        evidence={
            "candidate_entity_id": str(entity.id),
            "candidate_name": entity.legal_name,
            "confidence": score,
            "reasons": reasons,
        },
        notes=f"Confidence {round(score, 2)}. Manual verification required.",
    )

    db.add(review)

    _audit(
        db,
        entity_type="review_case",
        entity_id=str(source_record.id),
        action="REVIEW_CREATED",
        after_state=_json_safe(
            {
                "candidate_entity_id": entity.id,
                "confidence": score,
            }
        ),
    )

    return MatchResult(
        decision="REVIEW",
        confidence=score,
        business_entity_id=entity.id,
        reasons=reasons,
    )


def _create_new_entity(
    db: Session,
    source_record: SourceRecord,
) -> MatchResult:

    entity = BusinessEntity(
        ubid_code=generate_ubid(),
        legal_name=source_record.extracted_name or "UNKNOWN",
        normalized_name=normalize_text(
            source_record.extracted_name
        ),
        pan=source_record.extracted_pan,
        gstin=source_record.extracted_gstin,
        status=EntityStatusEnum.UNKNOWN,
    )

    db.add(entity)
    db.flush()

    link = EntityRecordLink(
        source_record_id=source_record.id,
        business_entity_id=entity.id,
        confidence=1.0,
        decision=LinkDecisionEnum.AUTO_LINK,
        explanation=["No reliable candidate found"],
    )

    db.add(link)

    _audit(
        db,
        entity_type="business_entity",
        entity_id=str(entity.id),
        action="NEW_ENTITY_CREATED",
        after_state=_json_safe(
        {
            "source_record_id": source_record.id,
            "ubid_code": entity.ubid_code,
        },
    ))

    return MatchResult(
        decision="NEW_ENTITY",
        confidence=0.0,
        business_entity_id=entity.id,
        reasons=["No reliable candidate found"],
    )


# ============================================================
# AUDIT
# ============================================================

def _audit(
    db: Session,
    entity_type: str,
    entity_id: str,
    action: str,
    before_state: Optional[dict] = None,
    after_state: Optional[dict] = None,
) -> None:

    log = AuditLog(
        actor_type=AuditActorEnum.SYSTEM,
        actor_id=None,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_state=before_state,
        after_state=after_state,
    )

    db.add(log)


# ============================================================
# SERIALIZER
# ============================================================

def _to_dict(result: MatchResult) -> Dict[str, Any]:
    return {
        "decision": result.decision,
        "confidence": round(result.confidence, 4),
        "business_entity_id": (
            str(result.business_entity_id)
            if result.business_entity_id is not None
            else None
        ),
        "reasons": result.reasons,
    }