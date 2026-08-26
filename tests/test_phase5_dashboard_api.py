import io
import uuid
import pytest
from httpx import AsyncClient
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import JobStatus, RiskTier
from app.services.dossier_pdf import DossierPDFGenerator


@pytest.mark.asyncio
async def test_verify_direct_endpoint(client: AsyncClient, db_session: AsyncSession):
    # Test POST /api/v1/verify
    payload = {
        "bidder_pan": "ABCDE1234F",
        "bidder_gstin": "27ABCDE1234F1Z1",
        "bidder_legal_name": "Apex Data Solutions Private Limited",
        "bidder_trade_name": "Apex Solutions",
        "bidder_udyam_reg_no": "UDYAM-MH-01-0012345",
        "gem_bid_number": "GEM/2026/B/998877",
        "tender_title": "Enterprise Cloud Procurement",
        "required_nic_codes": ["26201", "26511"],
        "min_turnover_inr": 50000000.0,
        "mii_preference_active": True,
    }

    resp = await client.post("/api/v1/verify", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == JobStatus.COMPLETED.value
    assert data["bci_score"] >= 85.0
    assert data["risk_tier"] == RiskTier.GREEN.value
    assert data["bidder"]["legal_name"] == "Apex Data Solutions Private Limited"
    assert data["tender"]["gem_bid_number"] == "GEM/2026/B/998877"
    assert len(data["audit_logs"]) >= 4

    job_id = data["id"]

    # Test GET /api/v1/jobs/{job_id}
    job_resp = await client.get(f"/api/v1/jobs/{job_id}")
    assert job_resp.status_code == 200
    job_data = job_resp.json()
    assert job_data["id"] == job_id
    assert job_data["bci_score"] == data["bci_score"]

    # Test GET /api/v1/jobs
    list_resp = await client.get("/api/v1/jobs")
    assert list_resp.status_code == 200
    job_list = list_resp.json()
    assert len(job_list) >= 1
    assert any(j["id"] == job_id for j in job_list)


@pytest.mark.asyncio
async def test_officer_override_endpoint(client: AsyncClient, db_session: AsyncSession):
    # 1. Create and evaluate a verification job
    payload = {
        "bidder_pan": "ABCDE1234F",
        "bidder_gstin": "27ABCDE1234F1Z1",
        "bidder_legal_name": "Apex Data Solutions Private Limited",
        "gem_bid_number": "GEM/2026/B/554433",
        "tender_title": "IT Equipment",
    }
    verify_resp = await client.post("/api/v1/verify", json=payload)
    assert verify_resp.status_code == 200
    job_id = verify_resp.json()["id"]

    # 2. Record Officer Override: APPROVED
    override_payload = {
        "decision": "APPROVED",
        "justification": "All statutory parameters validated. Bidder is fully compliant with GeM GTC clause 4(a).",
    }
    override_resp = await client.post(f"/api/v1/jobs/{job_id}/override", json=override_payload)
    assert override_resp.status_code == 200
    override_data = override_resp.json()
    assert override_data["officer_decision"] == "APPROVED"
    assert "All statutory parameters validated" in override_data["officer_justification"]
    assert override_data["officer_decided_at"] is not None

    # 3. Verify that GET /api/v1/jobs/{job_id} reflects the officer decision
    job_resp = await client.get(f"/api/v1/jobs/{job_id}")
    assert job_resp.status_code == 200
    job_data = job_resp.json()
    assert job_data["officer_decision"] == "APPROVED"
    assert job_data["officer_justification"] == override_payload["justification"]


@pytest.mark.asyncio
async def test_officer_override_invalid_input(client: AsyncClient, db_session: AsyncSession):
    fake_id = str(uuid.uuid4())
    # Non-existent job
    resp = await client.post(f"/api/v1/jobs/{fake_id}/override", json={"decision": "APPROVED", "justification": "Valid justification text"})
    assert resp.status_code == 404

    # Invalid decision type
    # First create a real job
    verify_resp = await client.post(
        "/api/v1/verify",
        json={
            "bidder_pan": "ABCDE1234F",
            "bidder_gstin": "27ABCDE1234F1Z1",
            "bidder_legal_name": "Apex Data Solutions Private Limited",
            "gem_bid_number": "GEM/2026/B/112233",
        },
    )
    job_id = verify_resp.json()["id"]

    bad_resp = await client.post(
        f"/api/v1/jobs/{job_id}/override",
        json={"decision": "UNKNOWN_DECISION", "justification": "Valid justification text"},
    )
    assert bad_resp.status_code == 422


@pytest.mark.asyncio
async def test_pdf_dossier_download_endpoint(client: AsyncClient, db_session: AsyncSession):
    # 1. Run verification
    payload = {
        "bidder_pan": "ABCDE1234F",
        "bidder_gstin": "27ABCDE1234F1Z1",
        "bidder_legal_name": "Apex Data Solutions Private Limited",
        "gem_bid_number": "GEM/2026/B/998877",
        "tender_title": "High Performance Server Clusters",
        "required_nic_codes": ["26201"],
        "min_turnover_inr": 10000000.0,
    }
    verify_resp = await client.post("/api/v1/verify", json=payload)
    assert verify_resp.status_code == 200
    job_id = verify_resp.json()["id"]

    # 2. Add an officer decision
    await client.post(
        f"/api/v1/jobs/{job_id}/override",
        json={
            "decision": "APPROVED",
            "justification": "Technical committee verified statutory and document AI extracts.",
        },
    )

    # 3. Download PDF Dossier
    pdf_resp = await client.get(f"/api/v1/jobs/{job_id}/dossier/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in pdf_resp.headers["content-disposition"]

    # 4. Verify PDF structure with pypdf
    pdf_bytes = pdf_resp.content
    assert pdf_bytes.startswith(b"%PDF-")
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1

    extracted_text = ""
    for page in reader.pages:
        extracted_text += page.extract_text() or ""

    assert "CHENNAI PETROLEUM CORPORATION LIMITED" in extracted_text
    assert "STATUTORY VENDOR SCRUTINY" in extracted_text
    assert "GEM/2026/B/998877" in extracted_text
    assert "Apex Data Solutions Private Limited" in extracted_text


@pytest.mark.asyncio
async def test_dashboard_static_and_root_endpoints(client: AsyncClient):
    # Root dashboard with browser Accept header
    root_resp = await client.get("/", headers={"accept": "text/html"})
    assert root_resp.status_code == 200
    assert "Compliance Copilot" in root_resp.text

    # /dashboard route
    dash_resp = await client.get("/dashboard")
    assert dash_resp.status_code == 200
    assert "Portal & document checks" in dash_resp.text or "Compliance Copilot" in dash_resp.text

    # /login route
    login_resp = await client.get("/login")
    assert login_resp.status_code == 200
    assert "Authorized Officer Access" in login_resp.text
    assert "Procurement Officer" in login_resp.text
    assert "System Administrator" in login_resp.text
    assert "Other User" in login_resp.text
    assert "Vigilance & Audit" in login_resp.text


def test_dossier_pdf_generator_standalone():
    sample_data = {
        "job_id": str(uuid.uuid4()),
        "gem_bid_number": "GEM/2026/B/888899",
        "tender_title": "Procurement of Solar Inverters",
        "bidder_legal_name": "SunPower Green Tech Solutions Pvt Ltd",
        "bidder_gstin": "27ABCDE1234F1Z1",
        "bidder_pan": "ABCDE1234F",
        "bci_score": 92.5,
        "risk_tier": "GREEN",
        "overall_compliance": True,
        "pillar_breakdown": {
            "GST": {"is_compliant": True, "findings": {"status": "Active"}, "payload_sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"},
            "PAN": {"is_compliant": True, "findings": {"status": "Active"}, "payload_sha256": "123456abcdef123456abcdef123456abcdef123456abcdef123456abcdef123456"},
        },
        "critical_disqualifiers": [],
        "warnings": ["Minor filing delay noted in Q2"],
        "officer_decision": "APPROVED",
        "officer_justification": "Approved per tender committee guidelines.",
        "officer_decided_at": "2026-08-26T12:00:00Z",
    }

    pdf_bytes = DossierPDFGenerator.generate_dossier_pdf(sample_data)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1


@pytest.mark.asyncio
async def test_direct_pdf_export_endpoint(client: AsyncClient):
    payload = {
        "gem_bid_number": "GEM/2026/B/778899",
        "tender_title": "IT Server Procurement",
        "bidder_legal_name": "Test Enterprise Solutions",
        "bidder_gstin": "27ABCDE1234F1Z1",
        "bidder_pan": "ABCDE1234F",
        "bci_score": 98.0,
        "risk_tier": "GREEN",
        "overall_compliance": True,
        "checks": {
            "udyam": {"status": "verified", "finding": "Active MSME", "sha": "sha256_mock"},
            "gst": {"status": "verified", "finding": "100% GSTR-3B filed", "sha": "sha256_mock"},
        },
        "officer_decision": "APPROVED",
        "officer_justification": "Verified against DigiLocker and GSTN records."
    }

    resp = await client.post("/api/v1/dossier/generate-pdf", json=payload)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF-")
    assert "attachment; filename=" in resp.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_individual_document_pdf_export_endpoint(client: AsyncClient):
    payload = {
        "title": "Make in India (MII) Declaration",
        "portal": "DPIIT · Make in India Portal",
        "status": "VERIFIED",
        "bidder_name": "Apex Data Solutions",
        "gem_bid": "GEM/2026/B/998877",
        "gstin": "27ABCDE1234F1Z1",
        "pan": "ABCDE1234F",
        "finding": "Local content declared at 65.5% (Class-I Local Supplier); CA UDIN 24012345AAAAAA1234 verified.",
        "fields": [
            {"lbl": "Supplier Class", "val": "Class-I Local Supplier"},
            {"lbl": "Declared Local Content %", "val": "65.5%"},
            {"lbl": "ICAI UDIN Reference", "val": "24012345AAAAAA1234"},
        ],
        "rules": [
            {"pass": True, "text": "Entity name strictly matches declared bid particulars."},
            {"pass": True, "text": "Local content exceeds minimum tender threshold of 50.0%."},
        ],
        "sha256": "1f129f6c3512c7a563c3a8d854a906020f9c59f0310717ef1c4058492c338c8e"
    }

    resp = await client.post("/api/v1/dossier/generate-doc-pdf", json=payload)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF-")
    assert "attachment; filename=" in resp.headers.get("content-disposition", "")
    assert "Make_in_India" in resp.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_gem_portal_ingestion_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/gem/bids/GEM/2026/B/998877")
    assert resp.status_code == 200
    data = resp.json()
    assert data["gem_bid_number"] == "GEM/2026/B/998877"
    assert "L&T Hydrocarbon" in data["bidder_legal_name"]
    assert "GeM e-Procurement Portal" in data["portal_source"]


@pytest.mark.asyncio
async def test_tender_specs_pdf_export_endpoint(client: AsyncClient):
    payload = {
        "title": "Turnaround Maintenance & High-Pressure Piping Valve Package",
        "gem_bid": "GEM/2026/B/998877",
        "ref_id": "CPCL/MANALI/M&C/2026/089",
        "dept": "Materials & Contracts Department • Manali Refinery",
        "est_value": "₹ 4,85,00,000 (INR 4.85 Cr)",
        "turnover_req": "₹ 1,20,00,000 (INR 1.20 Cr)",
        "mii_req": "Class-I Local Supplier (≥ 50% Local Content)",
        "nic_codes": "28132 (Valves & Cocks), 24102 (Piping), 33140 (Repair)",
        "emd_details": "₹ 9,70,000 (MSME / Udyam Exempt)",
        "published_date": "10-Aug-2026",
        "closing_date": "15-Sep-2026 (15:00 IST)",
        "opening_date": "15-Sep-2026 (16:00 IST)",
    }

    resp = await client.post("/api/v1/tenders/generate-specs-pdf", json=payload)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF-")
    assert "attachment; filename=" in resp.headers.get("content-disposition", "")
    assert "CPCL_Tender_Specs" in resp.headers.get("content-disposition", "")


