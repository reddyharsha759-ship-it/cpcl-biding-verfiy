import hashlib
import json
import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.models.domain import (
    Bidder,
    ComplianceAuditLog,
    JobStatus,
    PillarType,
    RiskTier,
    Tender,
    VerificationJob,
)
from app.models.schemas import (
    BidderCreate,
    BidderRead,
    ComplianceAuditLogRead,
    ComplianceDossierResponse,
    PillarResultSchema,
    TenderCreate,
    TenderRead,
    VerificationJobCreate,
    VerificationJobSummary,
)


def test_bidder_schema_validation():
    # Valid Bidder
    valid_data = {
        "pan": "ABCDE1234F",
        "gstin": "27ABCDE1234F1Z5",
        "udyam_reg_no": "UDYAM-MH-01-0012345",
        "legal_name": "Acme Infotech Private Limited",
        "trade_name": "Acme Tech",
    }
    bidder = BidderCreate(**valid_data)
    assert bidder.pan == "ABCDE1234F"
    assert bidder.gstin == "27ABCDE1234F1Z5"

    # Invalid PAN
    with pytest.raises(ValidationError):
        BidderCreate(
            pan="INVALID_PAN",
            gstin="27ABCDE1234F1Z5",
            legal_name="Test Corp",
        )

    # Invalid GSTIN
    with pytest.raises(ValidationError):
        BidderCreate(
            pan="ABCDE1234F",
            gstin="INVALID_GSTIN",
            legal_name="Test Corp",
        )


def test_tender_schema_validation():
    tender_data = {
        "gem_bid_number": "GEM/2026/B/998877",
        "title": "Supply and Installation of Smart Energy Meters",
        "required_nic_codes": ["26511", "26512"],
        "min_turnover_inr": 50000000.0,
        "mii_preference_active": True,
    }
    tender = TenderCreate(**tender_data)
    assert tender.gem_bid_number == "GEM/2026/B/998877"
    assert len(tender.required_nic_codes) == 2
    assert tender.mii_preference_active is True


@pytest.mark.asyncio
async def test_domain_model_persistence(db_session):
    # 1. Create Bidder
    bidder = Bidder(
        pan="ABCDE1234F",
        gstin="27ABCDE1234F1Z5",
        udyam_reg_no="UDYAM-MH-01-0012345",
        legal_name="Acme Infotech Private Limited",
        trade_name="Acme Tech",
    )
    db_session.add(bidder)
    await db_session.flush()
    assert bidder.id is not None

    # 2. Create Tender
    tender = Tender(
        gem_bid_number="GEM/2026/B/998877",
        title="Procurement of IT Equipment",
        required_nic_codes=["26201", "26202"],
        min_turnover_inr=10000000.0,
        mii_preference_active=True,
    )
    db_session.add(tender)
    await db_session.flush()
    assert tender.id is not None

    # 3. Create Verification Job
    job = VerificationJob(
        tender_id=tender.id,
        bidder_id=bidder.id,
        status=JobStatus.PROCESSING,
        bci_score=88.5,
        risk_tier=RiskTier.GREEN,
    )
    db_session.add(job)
    await db_session.flush()
    assert job.id is not None

    # 4. Create Compliance Audit Log
    raw_payload = {"gstin": bidder.gstin, "status": "Active", "filing_frequency": "Monthly"}
    payload_hash = hashlib.sha256(json.dumps(raw_payload, sort_keys=True).encode()).hexdigest()

    audit_log = ComplianceAuditLog(
        job_id=job.id,
        pillar=PillarType.GST,
        raw_payload=raw_payload,
        payload_sha256=payload_hash,
        is_compliant=True,
        findings={"active_status": True, "return_filed_on_time": True},
    )
    db_session.add(audit_log)
    await db_session.flush()
    assert audit_log.id is not None

    # Query and assert relationships
    result = await db_session.execute(
        select(VerificationJob).where(VerificationJob.id == job.id)
    )
    queried_job = result.scalar_one()
    assert queried_job.status == JobStatus.PROCESSING
    assert queried_job.risk_tier == RiskTier.GREEN
    assert queried_job.tender.gem_bid_number == "GEM/2026/B/998877"
    assert queried_job.bidder.legal_name == "Acme Infotech Private Limited"


def test_compliance_dossier_response_schema():
    job_id = uuid.uuid4()
    dossier = ComplianceDossierResponse(
        job_id=job_id,
        gem_bid_number="GEM/2026/B/123456",
        tender_title="Supply of High-Capacity Servers",
        bidder_legal_name="Apex Data Solutions Pvt Ltd",
        bidder_gstin="29ABCDE1234F1Z8",
        bidder_pan="ABCDE1234F",
        status=JobStatus.COMPLETED,
        bci_score=94.2,
        risk_tier=RiskTier.GREEN,
        overall_compliance=True,
        pillar_breakdown={
            PillarType.GST: PillarResultSchema(
                pillar=PillarType.GST,
                is_compliant=True,
                payload_sha256="abc123sha256hash",
                findings={"active_gstin": True, "3b_compliance": "100%"},
            ),
            PillarType.UDYAM: PillarResultSchema(
                pillar=PillarType.UDYAM,
                is_compliant=True,
                payload_sha256="def456sha256hash",
                findings={"msme_category": "Medium", "nic_match": True},
            ),
        },
        critical_disqualifiers=[],
        warnings=["Turnover marginally matches requirement threshold"],
        audit_trail_hashes=["abc123sha256hash", "def456sha256hash"],
        created_at=datetime.now(timezone.utc),
    )
    assert dossier.overall_compliance is True
    assert dossier.bci_score == 94.2
    assert dossier.risk_tier == RiskTier.GREEN
    assert len(dossier.pillar_breakdown) == 2
