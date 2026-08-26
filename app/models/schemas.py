import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.domain import JobStatus, PillarType, RiskTier


# --- Enums Export ---
__all__ = [
    "JobStatus",
    "RiskTier",
    "PillarType",
    "BidderBase",
    "BidderCreate",
    "BidderRead",
    "BidderUpdate",
    "TenderBase",
    "TenderCreate",
    "TenderRead",
    "VerificationJobCreate",
    "VerificationJobRead",
    "VerificationJobSummary",
    "PillarFindingDetail",
    "PillarResultSchema",
    "ComplianceAuditLogCreate",
    "ComplianceAuditLogRead",
    "ComplianceDossierResponse",
    "OfficerOverrideRequest",
    "OfficerOverrideResponse",
    "VerifyPipelineRequest",
    "HealthResponse",
]


# ==========================================
# 1. Bidder Schemas
# ==========================================

PAN_REGEX = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"
GSTIN_REGEX = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"


class BidderBase(BaseModel):
    pan: str = Field(..., description="10-digit Permanent Account Number", min_length=10, max_length=10)
    gstin: str = Field(..., description="15-character Goods and Services Tax Identification Number", min_length=15, max_length=15)
    udyam_reg_no: Optional[str] = Field(None, description="Udyam Registration Number (e.g. UDYAM-XX-00-0000000)")
    legal_name: str = Field(..., description="Official registered entity name", min_length=2, max_length=255)
    trade_name: Optional[str] = Field(None, description="Trade name or doing-business-as name", max_length=255)

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(PAN_REGEX, v):
            raise ValueError(f"Invalid PAN format: {v}. Must match standard 10-character PAN pattern.")
        return v

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(GSTIN_REGEX, v):
            raise ValueError(f"Invalid GSTIN format: {v}. Must match 15-character GSTIN pattern.")
        return v

    @field_validator("udyam_reg_no")
    @classmethod
    def validate_udyam(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip().upper()
        return v


class BidderCreate(BidderBase):
    pass


class BidderUpdate(BaseModel):
    pan: Optional[str] = Field(None, min_length=10, max_length=10)
    gstin: Optional[str] = Field(None, min_length=15, max_length=15)
    udyam_reg_no: Optional[str] = None
    legal_name: Optional[str] = Field(None, min_length=2, max_length=255)
    trade_name: Optional[str] = Field(None, max_length=255)


class BidderRead(BidderBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. Tender Schemas
# ==========================================

class TenderBase(BaseModel):
    gem_bid_number: str = Field(..., description="Unique GeM Bid / Tender Notice Number", min_length=3, max_length=64)
    title: str = Field(..., description="Procurement Title / Description", min_length=3, max_length=500)
    required_nic_codes: List[str] = Field(default_factory=list, description="List of mandatory 2-digit/4-digit/5-digit NIC codes")
    min_turnover_inr: Optional[float] = Field(0.0, description="Minimum annual turnover requirement in INR", ge=0.0)
    mii_preference_active: bool = Field(False, description="Whether Make In India (MII) preference applies")


class TenderCreate(TenderBase):
    pass


class TenderRead(TenderBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. Verification Job Schemas
# ==========================================

class VerificationJobCreate(BaseModel):
    tender_id: uuid.UUID = Field(..., description="ID of the target GeM Tender")
    bidder_id: uuid.UUID = Field(..., description="ID of the Bidder entity to verify")


class VerificationJobSummary(BaseModel):
    id: uuid.UUID
    tender_id: uuid.UUID
    bidder_id: uuid.UUID
    status: JobStatus
    bci_score: Optional[float] = Field(None, description="Bidder Compliance Index (0 - 100)")
    risk_tier: Optional[RiskTier] = Field(None, description="Evaluated risk tier (GREEN, AMBER, RED)")
    officer_decision: Optional[str] = Field(None, description="Officer override decision (APPROVED, REJECTED, CLARIFICATION_REQUESTED)")
    officer_justification: Optional[str] = Field(None, description="Officer audit justification text")
    officer_decided_at: Optional[datetime] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. Audit Log & Pillar Schemas
# ==========================================

class PillarFindingDetail(BaseModel):
    severity: str = Field("INFO", description="Severity: INFO, LOW, MEDIUM, HIGH, CRITICAL")
    message: str = Field(..., description="Detailed finding explanation")
    data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Contextual metadata or raw evidence extract")


class PillarResultSchema(BaseModel):
    pillar: PillarType
    is_compliant: bool
    payload_sha256: str = Field(..., description="SHA-256 hash of the canonical raw payload for auditability")
    findings: Dict[str, Any] = Field(default_factory=dict, description="Structured evaluation findings and discrepancies")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class ComplianceAuditLogCreate(BaseModel):
    job_id: uuid.UUID
    pillar: PillarType
    raw_payload: Dict[str, Any]
    payload_sha256: str
    is_compliant: bool
    findings: Dict[str, Any]


class ComplianceAuditLogRead(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    pillar: PillarType
    raw_payload: Dict[str, Any]
    payload_sha256: str
    is_compliant: bool
    findings: Dict[str, Any]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 5. Full Verification Dossier & Officer Overrides
# ==========================================

class OfficerOverrideRequest(BaseModel):
    decision: str = Field(..., description="Decision: APPROVED, REJECTED, or CLARIFICATION_REQUESTED")
    justification: str = Field(..., min_length=5, max_length=2000, description="Mandatory audit justification comments")


class OfficerOverrideResponse(BaseModel):
    job_id: uuid.UUID
    status: JobStatus
    officer_decision: str
    officer_justification: str
    officer_decided_at: datetime
    message: str = "Officer decision successfully logged in compliance audit register."


class VerifyPipelineRequest(BaseModel):
    bidder_pan: str = Field(..., min_length=10, max_length=10)
    bidder_gstin: str = Field(..., min_length=15, max_length=15)
    bidder_legal_name: str = Field(..., min_length=2, max_length=255)
    gem_bid_number: str = Field(..., min_length=3, max_length=64)
    tender_title: str = Field(default="Procurement Notice", min_length=2, max_length=500)
    bidder_udyam_reg_no: Optional[str] = None
    bidder_trade_name: Optional[str] = None
    required_nic_codes: List[str] = Field(default_factory=list)
    min_turnover_inr: float = Field(0.0, ge=0.0)
    mii_preference_active: bool = Field(False)


class VerificationJobRead(VerificationJobSummary):
    tender: Optional[TenderRead] = None
    bidder: Optional[BidderRead] = None
    audit_logs: List[ComplianceAuditLogRead] = Field(default_factory=list)


class ComplianceDossierResponse(BaseModel):
    """Comprehensive compliance dossier report summarizing all 6 pillars and risk assessment."""
    job_id: uuid.UUID
    gem_bid_number: str
    tender_title: str
    bidder_legal_name: str
    bidder_gstin: str
    bidder_pan: str
    status: JobStatus
    bci_score: Optional[float] = Field(None, description="Composite Bidder Compliance Index (0-100)")
    risk_tier: Optional[RiskTier] = Field(None, description="Risk classification: GREEN, AMBER, RED")
    overall_compliance: bool = Field(..., description="True if all mandatory checks pass without critical disqualifications")
    pillar_breakdown: Dict[PillarType, PillarResultSchema] = Field(default_factory=dict)
    critical_disqualifiers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    audit_trail_hashes: List[str] = Field(default_factory=list)
    officer_decision: Optional[str] = None
    officer_justification: Optional[str] = None
    officer_decided_at: Optional[datetime] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# ==========================================
# 6. Health & System Schemas
# ==========================================

class HealthResponse(BaseModel):
    status: str = "ok"
    app: str
    environment: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
