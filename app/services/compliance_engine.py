import asyncio
from typing import Any, Dict, List, Optional, Tuple

from app.services.document_ai.extractors import (
    FinancialCertificateParser,
    MakeInIndiaParser,
    OEMAuthorizationParser,
)
from app.services.document_ai.matcher import is_fuzzy_name_match
from app.services.integrations.debarment_adapter import DebarmentAdapter
from app.services.integrations.epfo_adapter import EPFOAdapter
from app.services.integrations.gstn_adapter import GSTNAdapter
from app.services.integrations.it_pan_adapter import IncomeTaxPANAdapter
from app.services.integrations.udyam_adapter import UdyamAdapter


# ==========================================
# 1. Structural & Cross-Pillar Consistency Rules
# ==========================================

def validate_pan_gstin_consistency(pan: str, gstin: str) -> Tuple[bool, Optional[str]]:
    """
    Validates that characters 3 to 12 of GSTIN strictly match the declared PAN.
    GSTIN format: [2-digit State Code][10-digit PAN][1-digit Entity][1-digit 'Z'][1-digit Checksum].
    """
    clean_pan = pan.strip().upper()
    clean_gstin = gstin.strip().upper()

    if len(clean_gstin) < 12:
        return False, f"GSTIN length ({len(clean_gstin)}) is insufficient to extract PAN."

    embedded_pan = clean_gstin[2:12]
    if embedded_pan != clean_pan:
        return (
            False,
            f"PAN mismatch: Declared PAN '{clean_pan}' does not match PAN embedded in GSTIN '{embedded_pan}'",
        )
    return True, None


def validate_pan_udyam_consistency(pan: str, udyam_payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates that the PAN linked with Udyam registration matches the declared PAN.
    """
    clean_pan = pan.strip().upper()
    udyam_pan = udyam_payload.get("pan")
    if udyam_pan:
        if udyam_pan.strip().upper() != clean_pan:
            return (
                False,
                f"PAN mismatch: Declared PAN '{clean_pan}' does not match PAN in Udyam record '{udyam_pan}'",
            )
    return True, None


def validate_nic_alignment(
    required_nic_codes: Optional[List[str]],
    registered_nic_codes: Optional[List[str]],
) -> Tuple[bool, List[str], Optional[str]]:
    """
    Validates that at least one registered NIC code matches the tender's required NIC codes (prefix or exact).
    """
    if not required_nic_codes:
        return True, registered_nic_codes or [], None

    req_clean = [str(c).strip() for c in required_nic_codes]
    reg_clean = [str(c).strip() for c in (registered_nic_codes or [])]

    matched = []
    for req in req_clean:
        if any(reg.startswith(req) or req.startswith(reg) for reg in reg_clean):
            matched.append(req)

    if not matched:
        return (
            False,
            [],
            f"NIC code mismatch: Bidder NIC codes {reg_clean} do not align with required tender NIC codes {req_clean}",
        )
    return True, matched, None


def validate_name_consistency(
    declared_name: str,
    statutory_name: str,
    threshold: float = 70.0,
) -> Tuple[bool, float, Optional[str]]:
    """
    Performs RapidFuzz token-sort matching between declared legal name and statutory portal name.
    Scores:
      >= 90.0: Strong match
      70.0 - 89.9: Acceptable match with Amber warning
      < 70.0: Disqualification flag
    """
    matched, score = is_fuzzy_name_match(declared_name, statutory_name, threshold=threshold)
    if not matched:
        return (
            False,
            score,
            f"Name discrepancy: Declared name '{declared_name}' differs significantly from statutory record '{statutory_name}' (Match: {score}%)",
        )
    return True, score, None


# ==========================================
# 2. Compliance Evaluation Orchestrator
# ==========================================

class ComplianceEngine:
    """
    Orchestrates multi-pillar statutory verification and document extraction concurrently.
    """

    def __init__(self):
        self.gstn_adapter = GSTNAdapter()
        self.udyam_adapter = UdyamAdapter()
        self.pan_adapter = IncomeTaxPANAdapter()
        self.debarment_adapter = DebarmentAdapter()
        self.epfo_adapter = EPFOAdapter()

    async def evaluate_bidder_tender_compliance(
        self,
        bidder_pan: str,
        bidder_gstin: str,
        bidder_legal_name: str,
        gem_bid_number: str,
        bidder_udyam_reg_no: Optional[str] = None,
        required_nic_codes: Optional[List[str]] = None,
        min_turnover_inr: float = 0.0,
        maf_doc_source: Optional[Any] = None,
        mii_doc_source: Optional[Any] = None,
        financial_doc_source: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Executes concurrent statutory and document evaluations and returns aggregated pillar results.
        """
        statutory_tasks = [
            self.gstn_adapter.verify(bidder_gstin),
            self.pan_adapter.verify(bidder_pan),
            self.debarment_adapter.verify(
                identifier=bidder_pan,
                company_name=bidder_legal_name,
            ),
        ]

        if bidder_udyam_reg_no:
            statutory_tasks.append(
                self.udyam_adapter.verify(
                    bidder_udyam_reg_no,
                    required_nic_codes=required_nic_codes,
                )
            )

        # Document parsing tasks
        doc_tasks = []
        if maf_doc_source:
            doc_tasks.append(
                OEMAuthorizationParser.parse_pdf(
                    source=maf_doc_source,
                    target_gem_bid_number=gem_bid_number,
                    bidder_legal_name=bidder_legal_name,
                )
            )
        if mii_doc_source:
            doc_tasks.append(
                MakeInIndiaParser.parse_pdf(source=mii_doc_source)
            )
        if financial_doc_source:
            doc_tasks.append(
                FinancialCertificateParser.parse_pdf(
                    source=financial_doc_source,
                    min_turnover_inr=min_turnover_inr,
                )
            )

        # Run all async tasks concurrently
        results = await asyncio.gather(*statutory_tasks, *doc_tasks, return_exceptions=False)

        # Unpack statutory results
        gst_result = results[0]
        pan_result = results[1]
        debarment_result = results[2]

        udyam_result = None
        doc_idx = 3
        if bidder_udyam_reg_no:
            udyam_result = results[3]
            doc_idx = 4

        # Unpack document results
        maf_result = None
        mii_result = None
        financial_result = None

        if maf_doc_source:
            maf_result = results[doc_idx]
            doc_idx += 1
        if mii_doc_source:
            mii_result = results[doc_idx]
            doc_idx += 1
        if financial_doc_source:
            financial_result = results[doc_idx]

        # Check cross-pillar consistency
        pan_gstin_valid, pan_gstin_err = validate_pan_gstin_consistency(bidder_pan, bidder_gstin)

        name_match_score = 100.0
        gst_legal_name = gst_result["findings"].get("legal_name")
        if gst_legal_name:
            _, name_match_score, name_err = validate_name_consistency(
                bidder_legal_name, gst_legal_name
            )

        return {
            "pan": bidder_pan,
            "gstin": bidder_gstin,
            "legal_name": bidder_legal_name,
            "gem_bid_number": gem_bid_number,
            "pan_gstin_valid": pan_gstin_valid,
            "pan_gstin_err": pan_gstin_err,
            "name_match_score": name_match_score,
            "statutory_pillars": {
                "GST": gst_result,
                "PAN": pan_result,
                "DEBARMENT": debarment_result,
                "UDYAM": udyam_result,
            },
            "documents": {
                "MAF": maf_result,
                "MII": mii_result,
                "FINANCIAL": financial_result,
            },
        }
