"""
Self-contained development seeder for ArthSetu.

Builds a coherent synthetic ecosystem in the configured database
(SQLite by default), then runs the real status engine so every
business gets a genuine status snapshot + audit trail.

Run from the repo root:
    python -m backend.seed_dev            # seed if empty
    python -m backend.seed_dev --reset    # drop + recreate + seed
"""

from __future__ import annotations

import argparse
import random
import string
import uuid
from datetime import datetime, timedelta, timezone

from backend.app.db.base import Base
from backend.app.db.session import SessionLocal, engine
from backend.app.db import models  # noqa: F401  (register tables)
from backend.app.db.models.activity_event import ActivityEvent
from backend.app.db.models.audit_log import AuditLog
from backend.app.db.models.business_entity import BusinessEntity
from backend.app.db.models.entity_record_link import EntityRecordLink
from backend.app.db.models.review_case import ReviewCase
from backend.app.db.models.source_record import SourceRecord
from backend.app.db.models.source_system import SourceSystem
from backend.app.db.enums import (
    AuditActorEnum,
    EntityStatusEnum,
    EventTypeEnum,
    LinkDecisionEnum,
    ReviewCaseStatusEnum,
)
from backend.app.services.status_engine import infer_business_status

SEED = 42
random.seed(SEED)

DISTRICTS = [
    "Patiala", "Ludhiana", "Mohali", "Amritsar",
    "Bathinda", "Jalandhar", "Rajpura", "Mandi Gobindgarh",
]
SECTORS = [
    "Retail", "Manufacturing", "Restaurant", "Healthcare", "Education",
    "Fitness", "Automobile", "Warehouse", "Textile", "Agriculture",
]
PREFIXES = ["Sharma", "Gupta", "Singh", "Verma", "Aggarwal", "Punjab",
            "Royal", "Green", "Om", "Sai"]
SUFFIXES = ["Traders", "Industries", "Rice Mill", "Foods", "Medical Store",
            "Gym", "Auto Works", "Textiles", "Enterprises", "Steel Works"]

SYSTEMS = [
    ("LABOUR", "Shops Registration Portal", "Labour Department"),
    ("MUNICIPAL", "Trade License Registry", "Municipal Department"),
    ("POLLUTION", "Consent Monitoring System", "Pollution Control Board"),
    ("POWER", "Commercial Consumer Ledger", "Electricity Board"),
]

TOTAL_BUSINESSES = 140
NOW = datetime.now(timezone.utc)


def _pan() -> str:
    return (
        "".join(random.choices(string.ascii_uppercase, k=5))
        + "".join(random.choices(string.digits, k=4))
        + random.choice(string.ascii_uppercase)
    )


def _gstin(pan: str) -> str:
    return f"{random.choice(['03', '04', '06'])}{pan}{random.randint(1, 9)}Z" \
           f"{random.choice(string.ascii_uppercase + string.digits)}"


def _normalize(name: str) -> str:
    return " ".join(name.lower().split())


def _noisy(name: str) -> str:
    return random.choice([
        name.upper(), name.lower(), f"M/S {name}",
        name.replace("Works", "Wrks"), name.replace("Industries", "Inds"),
        name,
    ])


ARCHETYPES = ["active"] * 62 + ["dormant"] * 25 + ["closed"] * 13


POSITIVE_EVENTS = [
    EventTypeEnum.GST_FILED, EventTypeEnum.LICENSE_RENEWED,
    EventTypeEnum.POWER_USAGE, EventTypeEnum.INSPECTION,
    EventTypeEnum.EMPLOYEE_FILING, EventTypeEnum.PAYMENT_RECEIVED,
]


def _spread_ages(n: int, oldest: int, newest: int = 1) -> list[int]:
    """n event ages (days) roughly uniform across a business's lifetime."""
    if n <= 0:
        return []
    step = (oldest - newest) / n
    return [
        int(oldest - step * i - random.uniform(0, step))
        for i in range(n)
    ]


def _activity_for(archetype: str) -> list[tuple[EventTypeEnum, float, datetime]]:
    events: list[tuple[EventTypeEnum, float, datetime]] = []

    if archetype == "active":
        # onboarded 4-24 months ago, steady cadence since, plus recent activity
        onboarded = random.randint(120, 720)
        for age in _spread_ages(random.randint(6, 11), onboarded, 75):
            events.append((random.choice(POSITIVE_EVENTS), 0.85, NOW - timedelta(days=age)))
        for _ in range(random.randint(2, 4)):
            events.append((
                random.choice(POSITIVE_EVENTS), 0.85,
                NOW - timedelta(days=random.randint(3, 70)),
            ))

    elif archetype == "dormant":
        onboarded = random.randint(240, 760)
        for age in _spread_ages(random.randint(3, 6), onboarded, 200):
            et = random.choice([
                EventTypeEnum.INSPECTION, EventTypeEnum.POWER_USAGE,
                EventTypeEnum.DOCUMENT_UPDATE, EventTypeEnum.COMPLAINT,
            ])
            events.append((et, 0.4, NOW - timedelta(days=age)))

    else:  # closed
        onboarded = random.randint(400, 820)
        for age in _spread_ages(random.randint(2, 4), onboarded, 260):
            events.append((EventTypeEnum.INSPECTION, 0.15, NOW - timedelta(days=age)))
        if random.random() < 0.75:
            events.append((
                EventTypeEnum.CLOSURE_NOTICE, -1.0,
                NOW - timedelta(days=random.randint(120, 420)),
            ))

    return events


def reset() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(BusinessEntity).count() > 0:
            print("[=] Database already has businesses; skipping. Use --reset.")
            return

        systems = [
            SourceSystem(code=c, name=n, department=d) for c, n, d in SYSTEMS
        ]
        db.add_all(systems)
        db.flush()

        businesses: list[BusinessEntity] = []
        for i in range(1, TOTAL_BUSINESSES + 1):
            name = f"{random.choice(PREFIXES)} {random.choice(SUFFIXES)}"
            has_pan = random.random() < 0.75
            pan = _pan() if has_pan else None
            gstin = _gstin(pan) if pan and random.random() < 0.6 else None
            be = BusinessEntity(
                ubid_code=f"UBID{i:06d}",
                legal_name=name,
                normalized_name=_normalize(name),
                pan=pan,
                gstin=gstin,
                district=random.choice(DISTRICTS),
                sector=random.choice(SECTORS),
                status=EntityStatusEnum.UNKNOWN,
            )
            businesses.append(be)
        db.add_all(businesses)
        db.flush()

        n_records = n_links = n_reviews = n_events = 0

        for be, archetype in zip(businesses, random.sample(
            ARCHETYPES * (TOTAL_BUSINESSES // len(ARCHETYPES) + 1),
            TOTAL_BUSINESSES,
        )):
            for system in random.sample(systems, random.randint(1, 4)):
                dirty = _noisy(be.legal_name)
                sr = SourceRecord(
                    source_system_id=system.id,
                    external_id=str(uuid.uuid4())[:12],
                    raw_payload={"name": dirty, "system": system.code},
                    normalized_payload={"name": _normalize(dirty)},
                    extracted_name=dirty,
                    extracted_pan=be.pan if random.random() < 0.7 else None,
                    extracted_gstin=be.gstin if random.random() < 0.55 else None,
                )
                db.add(sr)
                db.flush()
                n_records += 1

                # crude confidence for the seeded link
                score = 0.35
                if sr.extracted_pan and be.pan and sr.extracted_pan == be.pan:
                    score += 0.4
                if sr.extracted_gstin and be.gstin:
                    score += 0.2
                score = min(round(score + random.uniform(-0.05, 0.1), 2), 0.99)

                if score >= 0.85:
                    decision = LinkDecisionEnum.AUTO_LINK
                elif score >= 0.55:
                    decision = LinkDecisionEnum.REVIEW
                else:
                    decision = LinkDecisionEnum.AUTO_LINK  # low-info auto link

                link = EntityRecordLink(
                    source_record_id=sr.id,
                    business_entity_id=be.id,
                    confidence=score,
                    decision=decision,
                    explanation={"reasons": ["PAN match" if score > 0.7
                                             else "Name similarity"]},
                )
                db.add(link)
                n_links += 1

                if decision == LinkDecisionEnum.REVIEW:
                    db.add(ReviewCase(
                        source_record_id=sr.id,
                        candidate_entity_id=be.id,
                        status=ReviewCaseStatusEnum.OPEN,
                        confidence=score,
                        evidence={
                            "candidate_entity_id": str(be.id),
                            "candidate_name": be.legal_name,
                            "confidence": score,
                            "reasons": ["Partial name similarity",
                                        "PAN missing on source record"],
                        },
                        notes=f"Confidence {score}. Manual verification required.",
                    ))
                    n_reviews += 1

            for et, sc, occurred in _activity_for(archetype):
                db.add(ActivityEvent(
                    business_entity_id=be.id,
                    event_type=et,
                    score=sc,
                    occurred_at=occurred,
                    created_at=occurred,
                    payload={"source": "synthetic_seed"},
                ))
                n_events += 1

        db.commit()

        # audit rows for the automatic link decisions
        for link in db.query(EntityRecordLink).limit(400).all():
            db.add(AuditLog(
                actor_type=AuditActorEnum.SYSTEM,
                actor_id=None,
                entity_type="entity_record_link",
                entity_id=str(link.id),
                action="AUTO_LINK_EVALUATED",
                after_state={
                    "confidence": link.confidence,
                    "decision": link.decision.value,
                },
            ))
        db.commit()

        print(f"[+] source_systems : {len(systems)}")
        print(f"[+] businesses     : {len(businesses)}")
        print(f"[+] source_records : {n_records}")
        print(f"[+] links          : {n_links}")
        print(f"[+] review_cases   : {n_reviews}")
        print(f"[+] activity_events: {n_events}")

        print("[*] Running status engine for every business ...")
        ids = [b.id for b in db.query(BusinessEntity).all()]
        for bid in ids:
            try:
                infer_business_status(db, bid)
            except Exception as exc:  # noqa: BLE001
                db.rollback()
                print(f"    ! {bid}: {exc}")

        counts = {
            s.value: db.query(BusinessEntity)
            .filter(BusinessEntity.status == s).count()
            for s in EntityStatusEnum
        }
        print(f"[+] status snapshot: {counts}")
        print("[done] seed complete")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="drop + recreate")
    args = parser.parse_args()
    if args.reset:
        print("[*] Resetting schema ...")
        reset()
    seed()
