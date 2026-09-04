import enum


class LinkDecisionEnum(str, enum.Enum):
    """How a source record became linked to a business entity."""

    AUTO_LINK = "auto_link"      # high-confidence automatic link
    REVIEW = "review"            # sent to the human review queue
    MANUAL = "manual"            # created/confirmed by a reviewer
    REJECTED = "rejected"        # reviewer rejected the link


class EntityStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    DORMANT = "dormant"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class ReviewCaseStatusEnum(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class EventTypeEnum(str, enum.Enum):
    # Positive operational signals
    GST_FILED = "gst_filed"
    LICENSE_RENEWED = "license_renewed"
    INSPECTION = "inspection"
    POWER_USAGE = "power_usage"
    EMPLOYEE_FILING = "employee_filing"
    PAYMENT_RECEIVED = "payment_received"
    # Weak / neutral signals
    COMPLAINT = "complaint"
    DOCUMENT_UPDATE = "document_update"
    # Negative signals
    ZERO_POWER_USAGE = "zero_power_usage"
    SUSPENSION_NOTICE = "suspension_notice"
    CLOSURE_NOTICE = "closure_notice"
    LICENSE_CANCELLED = "license_cancelled"


class AuditActorEnum(str, enum.Enum):
    SYSTEM = "system"
    USER = "user"
    REVIEWER = "reviewer"
