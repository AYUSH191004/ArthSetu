# ============================================================
# FILE: backend/app/schemas.py
# Pydantic response/request models for the public API contract.
# ============================================================

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


# ------------------------------------------------------------
# Auth
# ------------------------------------------------------------

Role = Literal["admin", "reviewer", "viewer"]


class UserOut(BaseModel):
    id: str
    username: str
    full_name: str
    email: Optional[str] = None
    role: Role
    is_active: bool
    created_at: Optional[datetime] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9._-]+$")
    full_name: str = Field(min_length=1, max_length=120)
    email: Optional[str] = None
    role: Role = "viewer"
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    email: Optional[str] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None


class PasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


# ------------------------------------------------------------
# Health
# ------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    database: str


# ------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------

class DashboardResponse(BaseModel):
    total_businesses: int
    active: int
    dormant: int
    closed: int
    unknown: int
    pending_reviews: int
    total_links: int
    auto_match_rate: float


# ------------------------------------------------------------
# Analytics
# ------------------------------------------------------------

class AnalyticsSummaryResponse(BaseModel):
    total_businesses: int
    active: int
    dormant: int
    closed: int
    unknown: int


class TrendPoint(BaseModel):
    month: str
    events: int


class DistrictRow(BaseModel):
    district: str
    total: int
    active: int
    dormant: int
    closed: int
    unknown: int


# ------------------------------------------------------------
# Business
# ------------------------------------------------------------

class BusinessSearchItem(BaseModel):
    ubid: str
    business_name: str
    status: str
    district: Optional[str] = None
    pin_code: Optional[str] = None
    pan: Optional[str] = None
    gstin: Optional[str] = None


class BusinessSearchResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[BusinessSearchItem]


class TimelineEvent(BaseModel):
    date: Optional[datetime] = None
    event: str
    score: Optional[float] = None


class LinkedRecord(BaseModel):
    link_id: str
    source_record_id: str
    source_system: Optional[str] = None
    department: Optional[str] = None
    external_id: Optional[str] = None
    extracted_name: Optional[str] = None
    extracted_address: Optional[str] = None
    extracted_pin: Optional[str] = None
    confidence: Optional[float] = None
    decision: Optional[str] = None


class MatchingEvidence(BaseModel):
    signal: str
    value: str


class StatusHistoryPoint(BaseModel):
    date: datetime
    status: str
    confidence: Optional[float] = None


class BusinessProfileResponse(BaseModel):
    id: str
    ubid: str
    business_name: str
    status: str
    pan: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    pin_code: Optional[str] = None
    district: Optional[str] = None
    sector: Optional[str] = None
    linked_records_count: int
    linked_records: List[LinkedRecord]
    matching_evidence: List[MatchingEvidence]
    timeline: List[TimelineEvent]
    status_history: List[StatusHistoryPoint]


# ------------------------------------------------------------
# Review
# ------------------------------------------------------------

class ReviewCaseItem(BaseModel):
    review_id: str
    source_record_id: str
    candidate_entity_id: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_ubid: Optional[str] = None
    source_system: Optional[str] = None
    extracted_name: Optional[str] = None
    status: str
    confidence: Optional[float] = None
    evidence: Optional[Any] = None
    notes: Optional[str] = None
    reviewer_id: Optional[str] = None
    created_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None


class ReviewListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[ReviewCaseItem]


class ReviewDecisionResponse(BaseModel):
    message: str
    review_id: str
    status: str
    linked_entity_id: Optional[str] = None
    link_id: Optional[str] = None


# ------------------------------------------------------------
# Status engine
# ------------------------------------------------------------

class StatusResultResponse(BaseModel):
    business_entity_id: str
    ubid_code: str
    status: str
    confidence: float
    reasons: List[str]


class StatusRunAllResponse(BaseModel):
    message: str
    processed: int
    failed: int
    active: int
    dormant: int
    closed: int
    duration_seconds: float
    errors: List[Any]


# ------------------------------------------------------------
# Matching
# ------------------------------------------------------------

class MatchingResultResponse(BaseModel):
    decision: str
    confidence: float
    business_entity_id: Optional[str] = None
    reasons: List[str]


# ------------------------------------------------------------
# Audit
# ------------------------------------------------------------

class AuditEntry(BaseModel):
    id: str
    actor_type: str
    actor_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    action: Optional[str] = None
    before_state: Optional[Any] = None
    after_state: Optional[Any] = None
    created_at: Optional[datetime] = None


class AuditListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[AuditEntry]


# ------------------------------------------------------------
# Ingestion
# ------------------------------------------------------------

class SourceSystemOut(BaseModel):
    code: str
    name: str
    department: str
    record_count: int


class IngestRecord(BaseModel):
    external_id: Optional[str] = None
    name: str
    pan: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    pin: Optional[str] = None


class IngestRequest(BaseModel):
    source_system_code: str
    records: List[IngestRecord]
    process: bool = True


class RowError(BaseModel):
    row: int
    error: str


class MatchingTallyOut(BaseModel):
    auto_link: int
    review: int
    new_entity: int
    failed: int


class IngestionReportOut(BaseModel):
    source_system: str
    rows_read: int
    created: int
    skipped_duplicates: int
    errors: List[RowError]
    matching: Optional[MatchingTallyOut] = None


class ProcessPendingResponse(BaseModel):
    processed: int
    auto_link: int
    review: int
    new_entity: int
    failed: int


class PendingCountResponse(BaseModel):
    pending: int
