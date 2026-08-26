from pathlib import Path
import pytest

from app.services.document_ai import (
    FinancialCertificateParser,
    MakeInIndiaParser,
    OEMAuthorizationParser,
    PDFProcessor,
    calculate_fuzzy_match_score,
    is_fuzzy_name_match,
    parse_date_flexible,
    validate_icai_udin,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ==========================================
# 1. PDF Processor Engine Tests
# ==========================================

@pytest.mark.asyncio
async def test_pdf_processor_text_extraction():
    pdf_path = FIXTURES_DIR / "valid_maf.pdf"
    extracted = await PDFProcessor.extract_text(pdf_path)

    assert extracted["total_pages"] == 1
    assert extracted["is_scanned"] is False
    assert "Dell International Services India Private Limited" in extracted["full_text"]
    assert "GEM/2026/B/998877" in extracted["full_text"]


@pytest.mark.asyncio
async def test_pdf_processor_scanned_fallback():
    pdf_path = FIXTURES_DIR / "scanned_sample.pdf"
    extracted = await PDFProcessor.extract_text(pdf_path, ocr_fallback=True)

    assert extracted["is_scanned"] is True
    assert "Lenovo India Private Limited" in extracted["full_text"]
    assert "GEM/2026/B/998877" in extracted["full_text"]


# ==========================================
# 2. OEM Authorization Form (MAF) Tests
# ==========================================

@pytest.mark.asyncio
async def test_oem_maf_parser_valid():
    pdf_path = FIXTURES_DIR / "valid_maf.pdf"
    result = await OEMAuthorizationParser.parse_pdf(
        source=pdf_path,
        target_gem_bid_number="GEM/2026/B/998877",
        bidder_legal_name="Apex Data Solutions Private Limited",
    )

    assert result["is_compliant"] is True
    assert result["tender_matched"] is True
    assert result["is_expired"] is False
    assert "Dell" in result["oem_name"]
    assert result["bidder_name_match_score"] >= 80.0
    assert len(result["disqualifiers"]) == 0


@pytest.mark.asyncio
async def test_oem_maf_parser_expired():
    pdf_path = FIXTURES_DIR / "expired_maf.pdf"
    result = await OEMAuthorizationParser.parse_pdf(
        source=pdf_path,
        target_gem_bid_number="GEM/2026/B/998877",
        bidder_legal_name="Apex Data Solutions Private Limited",
    )

    assert result["is_compliant"] is False
    assert result["is_expired"] is True
    assert any("expired" in d.lower() for d in result["disqualifiers"])


@pytest.mark.asyncio
async def test_oem_maf_parser_mismatched_tender():
    pdf_path = FIXTURES_DIR / "mismatched_tender_maf.pdf"
    result = await OEMAuthorizationParser.parse_pdf(
        source=pdf_path,
        target_gem_bid_number="GEM/2026/B/998877",  # Expected 998877, document has 111111
        bidder_legal_name="Apex Data Solutions Private Limited",
    )

    assert result["is_compliant"] is False
    assert result["tender_matched"] is False
    assert any("does not match target GeM Bid Number" in d for d in result["disqualifiers"])


@pytest.mark.asyncio
async def test_oem_maf_parser_mismatched_bidder():
    pdf_path = FIXTURES_DIR / "valid_maf.pdf"
    result = await OEMAuthorizationParser.parse_pdf(
        source=pdf_path,
        target_gem_bid_number="GEM/2026/B/998877",
        bidder_legal_name="Totally Different Unrelated Corporation LLP",
    )

    assert result["is_compliant"] is False
    assert any("does not match registered bidder name" in d for d in result["disqualifiers"])


# ==========================================
# 3. Make in India (MII) Declaration Tests
# ==========================================

@pytest.mark.asyncio
async def test_mii_parser_class1_valid():
    pdf_path = FIXTURES_DIR / "valid_mii_class1.pdf"
    result = await MakeInIndiaParser.parse_pdf(
        source=pdf_path,
        min_required_percentage=50.0,
    )

    assert result["is_compliant"] is True
    assert result["local_content_percentage"] == 65.5
    assert result["supplier_class"] == "Class-I Local Supplier"
    assert "Pune" in result["location_of_value_addition"]
    assert result["udin"] == "24012345AAAAAA1234"
    assert result["udin_valid"] is True
    assert len(result["disqualifiers"]) == 0


@pytest.mark.asyncio
async def test_mii_parser_low_local_content_disqualification():
    pdf_path = FIXTURES_DIR / "low_local_content_mii.pdf"
    result = await MakeInIndiaParser.parse_pdf(
        source=pdf_path,
        min_required_percentage=50.0,
    )

    assert result["is_compliant"] is False
    assert result["local_content_percentage"] == 15.0
    assert result["supplier_class"] == "Non-Local Supplier"
    assert any("below required minimum threshold" in d for d in result["disqualifiers"])


# ==========================================
# 4. CA Financial Certificate Tests
# ==========================================

@pytest.mark.asyncio
async def test_financial_certificate_parser_valid():
    pdf_path = FIXTURES_DIR / "valid_turnover_ca_cert.pdf"
    result = await FinancialCertificateParser.parse_pdf(
        source=pdf_path,
        min_turnover_inr=50_000_000.0,  # ₹5 Crore minimum
    )

    assert result["is_compliant"] is True
    assert len(result["turnover_by_fy"]) == 3
    # FY turnovers: 10.5 Cr, 12.0 Cr, 15.0 Cr -> Avg 12.5 Cr = 125,000,000 INR
    assert result["avg_turnover_inr"] == 125_000_000.0
    assert result["net_worth_inr"] == 85_000_000.0
    assert result["udin"] == "24098765BBBBBB4321"
    assert result["udin_valid"] is True
    assert "Sharma & Associates" in result["ca_firm"]
    assert len(result["disqualifiers"]) == 0


@pytest.mark.asyncio
async def test_financial_certificate_parser_insufficient_turnover():
    pdf_path = FIXTURES_DIR / "insufficient_turnover_ca_cert.pdf"
    result = await FinancialCertificateParser.parse_pdf(
        source=pdf_path,
        min_turnover_inr=50_000_000.0,  # ₹5 Crore required vs ₹1.2 Crore achieved
    )

    assert result["is_compliant"] is False
    # FY turnovers: 1.0 Cr, 1.2 Cr, 1.4 Cr -> Avg 1.2 Cr = 12,000,000 INR
    assert result["avg_turnover_inr"] == 12_000_000.0
    assert any("below mandatory tender requirement" in d for d in result["disqualifiers"])


# ==========================================
# 5. Fuzzy Matching & UDIN Unit Tests
# ==========================================

def test_fuzzy_name_matching():
    name1 = "Apex Data Solutions Private Limited"
    name2 = "Apex Data Solutions Pvt Ltd"
    matched, score = is_fuzzy_name_match(name1, name2)
    assert matched is True
    assert score >= 80.0

    mismatch, m_score = is_fuzzy_name_match(name1, "Completely Different Services Ltd")
    assert mismatch is False
    assert m_score < 50.0


def test_udin_validation_utility():
    valid, err = validate_icai_udin("24012345AAAAAA1234")
    assert valid is True
    assert err is None

    invalid, err = validate_icai_udin("INVALID_UDIN_123")
    assert invalid is False
    assert "Invalid UDIN syntax" in err

    missing, err = validate_icai_udin(None)
    assert missing is False


def test_date_parser_utility():
    assert parse_date_flexible("31/12/2027") is not None
    assert parse_date_flexible("2027-12-31") is not None
    assert parse_date_flexible("Invalid Date String") is None
