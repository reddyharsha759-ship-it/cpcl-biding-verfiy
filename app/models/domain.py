import enum
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# JSON type supporting PostgreSQL JSONB with fallback to standard JSON
JSONType = JSONB().with_variant(JSON(), "sqlite")


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RiskTier(str, enum.Enum):
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"


class PillarType(str, enum.Enum):
    GST = "GST"
    UDYAM = "UDYAM"
    PAN = "PAN"
    MII = "MII"
    DEBARMENT = "DEBARMENT"
    OEM = "OEM"


class Bidder(Base):
    """Bidder entity representing an enterprise submitting a bid on GeM."""

    __tablename__ = "bidders"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    pan: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    gstin: Mapped[str] = mapped_column(String(15), unique=True, index=True, nullable=False)
    udyam_reg_no: Mapped[Optional[str]] = mapped_column(String(30), index=True, nullable=True)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trade_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    verification_jobs: Mapped[List["VerificationJob"]] = relationship(
        "VerificationJob", back_populates="bidder", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Bidder id={self.id} legal_name='{self.legal_name}' gstin='{self.gstin}'>"


class Tender(Base):
    """Tender entity representing a government procurement notice on GeM."""

    __tablename__ = "tenders"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    gem_bid_number: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    required_nic_codes: Mapped[List[str]] = mapped_column(
        JSONType, default=list, nullable=False
    )
    min_turnover_inr: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0
    )
    mii_preference_active: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    verification_jobs: Mapped[List["VerificationJob"]] = relationship(
        "VerificationJob", back_populates="tender", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tender id={self.id} gem_bid_number='{self.gem_bid_number}'>"


class VerificationJob(Base):
    """Verification Job evaluating compliance of a Bidder against a Tender."""

    __tablename__ = "verification_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    tender_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bidder_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("bidders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="jobstatus_enum"),
        default=JobStatus.PENDING,
        nullable=False,
        index=True,
    )
    bci_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_tier: Mapped[Optional[RiskTier]] = mapped_column(
        Enum(RiskTier, name="risktier_enum"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    officer_decision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    officer_justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    officer_decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    tender: Mapped["Tender"] = relationship("Tender", back_populates="verification_jobs")
    bidder: Mapped["Bidder"] = relationship("Bidder", back_populates="verification_jobs")
    audit_logs: Mapped[List["ComplianceAuditLog"]] = relationship(
        "ComplianceAuditLog", back_populates="job", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<VerificationJob id={self.id} status={self.status} risk_tier={self.risk_tier}>"


class ComplianceAuditLog(Base):
    """Immutable audit trail log for every verification pillar check."""

    __tablename__ = "compliance_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("verification_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pillar: Mapped[PillarType] = mapped_column(
        Enum(PillarType, name="pillartype_enum"), nullable=False, index=True
    )
    raw_payload: Mapped[Dict[str, Any]] = mapped_column(
        JSONType, default=dict, nullable=False
    )
    payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    is_compliant: Mapped[bool] = mapped_column(Boolean, nullable=False)
    findings: Mapped[Dict[str, Any]] = mapped_column(
        JSONType, default=dict, nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    job: Mapped["VerificationJob"] = relationship(
        "VerificationJob", back_populates="audit_logs"
    )

    __table_args__ = (
        Index("ix_compliance_audit_job_pillar", "job_id", "pillar"),
    )

    def __repr__(self) -> str:
        return f"<ComplianceAuditLog id={self.id} pillar={self.pillar} is_compliant={self.is_compliant}>"
