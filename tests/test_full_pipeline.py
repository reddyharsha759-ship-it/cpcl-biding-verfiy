import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.domain import (
    Bidder,
    JobStatus,
    PillarType,
    RiskTier,
    Tender,
    VerificationJob,
)
from app.models.schemas import (
    BidderCreate,
    ComplianceDossierResponse,
    TenderCreate,
    VerificationJobCreate,
    VerificationJobRead,
)
from app.services.compliance_engine import (
    ComplianceEngine,
    validate_name_consistency,
    validate_nic_alignment,
    validate_pan_gstin_consistency,
    validate_pan_udyam_consistency,
)
from app.services.scoring_service import ScoringService
from app.workers.tasks import evaluate_compliance_job_async


# ==========================================
# 1. Rule Engine & Consistency Tests
# ==========================================

def test_pan_gstin_consistency_rules():
    # Valid
    valid, err = validate_pan_gstin_consistency("ABCDE1234F", "27ABCDE1234F1Z5")
    assert valid is True
    assert err is None

    # Mismatch
    valid, err = validate_pan_gstin_consistency("ABCDE1234F", "27XYZWV9876F1Z5")
    assert valid is False
    assert "PAN mismatch" in err

    # Short GSTIN
    valid, err = validate_pan_gstin_consistency("ABCDE1234F", "27ABCDE")
    assert valid is False


def test_pan_udyam_consistency_rules():
    # Valid
    valid, err = validate_pan_udyam_consistency("ABCDE1234F", {"pan": "ABCDE1234F"})
    assert valid is True
    assert err is None

    # Mismatch
    valid, err = validate_pan_udyam_consistency("ABCDE1234F", {"pan": "XXXXX9999X"})
    assert valid is False
    assert "PAN mismatch" in err


def test_nic_alignment_rules():
    # Matching prefix
    valid, matched, err = validate_nic_alignment(
        required_nic_codes=["2620", "6201"],
        registered_nic_codes=["26201", "26511", "70000"],
    )
    assert valid is True
    assert "2620" in matched
    assert err is None

    # No match
    valid, matched, err = validate_nic_alignment(
        required_nic_codes=["3000"],
        registered_nic_codes=["26201", "26511"],
    )
    assert valid is False
    assert len(matched) == 0
    assert "NIC code mismatch" in err


def test_name_consistency_rules():
    # Strong match
    valid, score, err = validate_name_consistency(
        "Premier Industrial & Tech Solutions Private Limited",
        "PREMIER INDUSTRIAL & TECH SOLUTIONS PVT LTD",
    )
    assert valid is True
    assert score >= 90.0
    assert err is None

    # Discrepancy / Disqualification (< 70)
    valid, score, err = validate_name_consistency(
        "Premier Industrial & Tech Solutions Private Limited",
        "Totally Different Global Enterprises Inc",
    )
    assert valid is False
    assert score < 70.0
    assert err is not None


# ==========================================
# 2. Scoring Service & BCI Tests
# ==========================================

def test_scoring_service_compliant_scenario():
    eval_data = {
        "pan_gstin_valid": True,
        "name_match_score": 100.0,
        "statutory_pillars": {
            "GST": {
                "is_compliant": True,
                "findings": {"is_active": True, "gstr3b_regularity_percentage": 100.0},
            },
            "PAN": {
                "is_compliant": True,
                "findings": {"is_active": True, "sec_206ab_specified_person": False},
            },
            "DEBARMENT": {"is_compliant": True, "findings": {"is_debarred": False, "disqualifiers": []}},
            "UDYAM": {"is_compliant": True, "findings": {"is_active": True}},
        },
        "documents": {
            "MAF": {"is_compliant": True, "tender_matched": True, "is_expired": False},
            "MII": {"supplier_class": "Class-I Local Supplier"},
            "FINANCIAL": {"avg_turnover_inr": 50000000.0, "net_worth_inr": 20000000.0},
        },
    }

    result = ScoringService.calculate_bci(eval_data, min_turnover_inr=10000000.0)
    assert result["has_hard_failures"] is False
    assert result["bci_score"] >= 85.0
    assert result["risk_tier"] == RiskTier.GREEN
    assert "TECHNICALLY COMPLIANT" in result["recommendation"]


def test_scoring_service_hard_failure_debarment():
    eval_data = {
        "pan_gstin_valid": True,
        "name_match_score": 100.0,
        "statutory_pillars": {
            "GST": {"findings": {"is_active": True, "gstr3b_regularity_percentage": 100.0}},
            "PAN": {"findings": {"is_active": True, "sec_206ab_specified_person": False}},
            "DEBARMENT": {
                "is_compliant": False,
                "findings": {
                    "is_debarred": True,
                    "disqualifiers": ["ACTIVE DEBARMENT ORDER [DEB/MOD/2024/089]"],
                },
            },
        },
        "documents": {},
    }

    result = ScoringService.calculate_bci(eval_data)
    assert result["has_hard_failures"] is True
    assert result["bci_score"] == 0.0
    assert result["risk_tier"] == RiskTier.RED
    assert "DISQUALIFIED" in result["recommendation"]


def test_scoring_service_amber_tier_scenario():
    eval_data = {
        "pan_gstin_valid": True,
        "name_match_score": 75.0,
        "statutory_pillars": {
            "GST": {
                "findings": {
                    "is_active": True,
                    "gstr3b_regularity_percentage": 60.0,
                }
            },
            "PAN": {"findings": {"is_active": True, "sec_206ab_specified_person": False}},
            "DEBARMENT": {"is_compliant": True, "findings": {"is_debarred": False}},
            "UDYAM": {"is_compliant": False, "findings": {"is_active": True, "warnings": ["NIC Partial"]}},
        },
        "documents": {
            "MAF": {"is_compliant": False, "tender_matched": True, "is_expired": False, "warnings": ["Missing direct clause"]},
            "MII": {"supplier_class": "Class-II Local Supplier"},
        },
    }

    result = ScoringService.calculate_bci(eval_data)
    assert result["has_hard_failures"] is False
    assert 60.0 <= result["bci_score"] < 85.0
    assert result["risk_tier"] == RiskTier.AMBER
    assert "SEEK CLARIFICATION" in result["recommendation"]


# ==========================================
# 3. Async Task Worker & Full DB Integration
# ==========================================

@pytest.mark.asyncio
async def test_evaluate_compliance_job_async_execution(db_session: AsyncSession):
    from pathlib import Path
    fixtures_dir = Path(__file__).parent / "fixtures"

    # Setup Bidder and Tender in DB matching the fixture document metadata
    bidder = Bidder(
        pan="ABCDE1234F",
        gstin="27ABCDE1234F1Z1",
        udyam_reg_no="UDYAM-MH-01-0012345",
        legal_name="Apex Data Solutions Private Limited",
        trade_name="Apex Solutions",
    )
    tender = Tender(
        gem_bid_number="GEM/2026/B/998877",
        title="Procurement of IT Infrastructure",
        required_nic_codes=["2620", "6201"],
        min_turnover_inr=5000000.0,
        mii_preference_active=True,
    )
    db_session.add(bidder)
    db_session.add(tender)
    await db_session.commit()
    await db_session.refresh(bidder)
    await db_session.refresh(tender)

    # Create VerificationJob
    job = VerificationJob(
        tender_id=tender.id,
        bidder_id=bidder.id,
        status=JobStatus.PENDING,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    # Execute async pipeline with existing fixture files
    doc_paths = {
        "maf": str(fixtures_dir / "valid_maf.pdf"),
        "mii": str(fixtures_dir / "valid_mii_class1.pdf"),
        "financial": str(fixtures_dir / "valid_turnover_ca_cert.pdf"),
    }

    result = await evaluate_compliance_job_async(
        job_id=job.id,
        db=db_session,
        document_paths=doc_paths,
    )

    assert result["status"] == JobStatus.COMPLETED.value
    assert result["bci_score"] >= 85.0
    assert result["risk_tier"] == RiskTier.GREEN.value

    # Verify audit logs in database
    stmt = (
        select(VerificationJob)
        .options(selectinload(VerificationJob.audit_logs))
        .where(VerificationJob.id == job.id)
    )
    loaded_job = (await db_session.execute(stmt)).scalar_one()
    assert loaded_job.status == JobStatus.COMPLETED
    assert loaded_job.completed_at is not None
    assert len(loaded_job.audit_logs) >= 4  # GST, PAN, DEBARMENT, UDYAM, MAF, MII


# ==========================================
# 4. API Endpoints Integration Tests
# ==========================================

@pytest.mark.asyncio
async def test_verification_api_workflow(client: AsyncClient, db_session: AsyncSession):
    # 1. Create Bidder
    bidder_resp = await client.post(
        "/api/v1/verification/bidders",
        json={
            "pan": "ABCDE1234F",
            "gstin": "27ABCDE1234F1Z1",
            "udyam_reg_no": "UDYAM-MH-01-0012345",
            "legal_name": "Premier Industrial & Tech Solutions Private Limited",
            "trade_name": "Premier Solutions",
        },
    )
    assert bidder_resp.status_code == 201
    bidder_data = bidder_resp.json()
    bidder_id = bidder_data["id"]

    # 2. Create Tender
    tender_resp = await client.post(
        "/api/v1/verification/tenders",
        json={
            "gem_bid_number": "GEM/2026/B/888800",
            "title": "Supply of High Performance Workstations",
            "required_nic_codes": ["26201", "26511"],
            "min_turnover_inr": 10000000.0,
            "mii_preference_active": True,
        },
    )
    assert tender_resp.status_code == 201
    tender_data = tender_resp.json()
    tender_id = tender_data["id"]

    # 3. Trigger Verification Evaluation
    eval_resp = await client.post(
        "/api/v1/verification/evaluate",
        json={
            "tender_id": tender_id,
            "bidder_id": bidder_id,
        },
    )
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["status"] == "COMPLETED"
    assert eval_data["bci_score"] is not None
    assert eval_data["risk_tier"] is not None
    job_id = eval_data["id"]

    # 4. Fetch Job Detail
    job_resp = await client.get(f"/api/v1/verification/jobs/{job_id}")
    assert job_resp.status_code == 200
    job_data = job_resp.json()
    assert job_data["id"] == job_id
    assert len(job_data["audit_logs"]) >= 3

    # 5. Fetch Full Compliance Dossier
    dossier_resp = await client.get(f"/api/v1/verification/dossier/{job_id}")
    assert dossier_resp.status_code == 200
    dossier = dossier_resp.json()
    assert dossier["job_id"] == job_id
    assert dossier["gem_bid_number"] == "GEM/2026/B/888800"
    assert dossier["bidder_legal_name"] == "Premier Industrial & Tech Solutions Private Limited"
    assert len(dossier["audit_trail_hashes"]) >= 3
    assert "GST" in dossier["pillar_breakdown"]
    assert "PAN" in dossier["pillar_breakdown"]
    assert "DEBARMENT" in dossier["pillar_breakdown"]
