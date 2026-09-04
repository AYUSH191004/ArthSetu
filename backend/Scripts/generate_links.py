# backend/Scripts/generate_links.py

from backend.app.db.session import SessionLocal

from backend.app.db.models.entity_record_link import EntityRecordLink
from backend.app.db.models.source_record import SourceRecord
from backend.app.db.models.business_entity import BusinessEntity

from backend.app.db.enums import LinkDecisionEnum

from backend.Scripts.seed_master import normalize_name

import random


def choose_decision(score):
    if score >= 0.90:
        return LinkDecisionEnum.AUTO
    elif score >= 0.55:
        return LinkDecisionEnum.REVIEWED
    return LinkDecisionEnum.REJECTED


def compute_match(record, entity):
    score = 0.0
    reasons = []

    # PAN exact
    if record.extracted_pan and entity.pan:
        if record.extracted_pan == entity.pan:
            score += 0.55
            reasons.append("PAN exact match")

    # GSTIN exact
    if record.extracted_gstin and entity.gstin:
        if record.extracted_gstin == entity.gstin:
            score += 0.35
            reasons.append("GSTIN exact match")

    # Name similarity heuristic
    rname = normalize_name(record.extracted_name or "")
    ename = entity.normalized_name or ""

    if rname == ename:
        score += 0.20
        reasons.append("Exact normalized name")

    elif rname in ename or ename in rname:
        score += 0.10
        reasons.append("Partial name similarity")

    score = min(score, 0.99)

    return score, reasons


def seed_links(db):
    existing = db.query(EntityRecordLink).count()
    if existing > 0:
        print(f"[✓] Links already seeded: {existing}")
        return

    records = db.query(SourceRecord).all()
    entities = db.query(BusinessEntity).all()

    created = 0

    for record in records:
        matched = None
        best_score = 0
        best_reasons = []

        for entity in entities:
            score, reasons = compute_match(record, entity)

            if score > best_score:
                best_score = score
                matched = entity
                best_reasons = reasons

        if matched:
            decision = choose_decision(best_score)

            link = EntityRecordLink(
                source_record_id=record.id,
                business_entity_id=matched.id,
                confidence=round(best_score, 2),
                decision=decision,
                explanation={
                    "reasons": best_reasons,
                    "record_name": record.extracted_name,
                    "matched_entity": matched.legal_name,
                },
            )

            db.add(link)
            created += 1

    db.commit()

    print(f"[✓] Links seeded. Created: {created}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_links(db)
    finally:
        db.close()