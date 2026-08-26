import re
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.document_ai.matcher import (
    calculate_fuzzy_match_score,
    is_fuzzy_name_match,
    parse_date_flexible,
    validate_icai_udin,
)
from app.services.document_ai.parser import PDFProcessor


# ==========================================
# 1. OEM Authorization Form (MAF) Parser
# ==========================================

class OEMAuthorizationParser:
    """
    Parser for Manufacturer Authorization Forms (MAF) submitted by Channel Partners / Resellers.
    Validates OEM identity, authorized bidder entity, tender bid number matching, and validity window.
    """

    TENDER_NO_PATTERNS = [
        r"(GEM\/\d{4}\/[B|R]\/\d+)",
        r"(?:GEM|Bid|Tender|RFP|NIT)\s*(?:No\.?|Number|Ref\.?|ID)?\s*[:\-]?\s*([A-Za-z0-9\/\-_\.]+)",
    ]

    OEM_NAME_PATTERNS = [
        r"(?:We,?\s*(?:M/s)?\s*|OEM\s*[:\-]\s*|Manufacturer\s*[:\-]\s*)([A-Za-z0-9\s\.\-&]+?(?:Private Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|LLP|Corporation|Inc))",
        r"(?:For\s+)([A-Za-z0-9\s\.\-&]+?(?:Private Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|LLP|Corporation))",
    ]

    BIDDER_NAME_PATTERNS = [
        r"(?:authorize|appoint|authorize\s+partner|authorized\s+bidder)\s*[:\-]?\s*(?:M/s\.?\s*)?([A-Za-z0-9\s\.\-&]+?(?:Private Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|Enterprises|Solutions|Services|Corporation|LLP))",
        r"(?:M/s\.?\s*)([A-Za-z0-9\s\.\-&]+?(?:Private Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|LLP))\s*(?:\(Authorized Bidder\)|as authorized bidder)",
        r"(?:Authorized\s+Bidder|Partner|Channel\s+Partner)\s*[:\-]?\s*(?:M/s\.?\s*)?([A-Za-z0-9\s\.\-&]+?(?:Private Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|LLP))",
    ]

    DATE_PATTERNS = [
        r"(?:Valid\s+(?:till|upto|until|through)|Expiry\s+Date|Valid\s+to)\s*[:\-]?\s*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})",
        r"(?:Date\s+of\s+Issue|Dated|Date)\s*[:\-]?\s*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})",
    ]

    @classmethod
    async def parse_text(cls, text: str, target_gem_bid_number: Optional[str] = None, bidder_legal_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Extracts MAF attributes and evaluates compliance against target GeM Bid and Bidder identity.
        """
        extracted_tender_no = None
        for pattern in cls.TENDER_NO_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_tender_no = match.group(1).strip()
                break

        extracted_oem = None
        for pattern in cls.OEM_NAME_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_oem = match.group(1).strip()
                break

        extracted_bidder = None
        for pattern in cls.BIDDER_NAME_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_bidder = match.group(1).strip()
                break

        validity_date_str = None
        for pattern in cls.DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                validity_date_str = match.group(1).strip()
                break

        parsed_validity_date = parse_date_flexible(validity_date_str) if validity_date_str else None

        # Disqualifiers & Warnings evaluation
        disqualifiers = []
        warnings = []

        # 1. Tender Reference Matching Check
        tender_matched = False
        if target_gem_bid_number:
            if extracted_tender_no:
                # Normalize tender numbers (remove spaces, case insensitive)
                n_target = re.sub(r"[^A-Za-z0-9]", "", target_gem_bid_number.upper())
                n_extracted = re.sub(r"[^A-Za-z0-9]", "", extracted_tender_no.upper())
                if n_target == n_extracted or n_target in n_extracted or n_extracted in n_target:
                    tender_matched = True
                else:
                    disqualifiers.append(
                        f"Tender number in MAF ('{extracted_tender_no}') does not match target GeM Bid Number ('{target_gem_bid_number}')"
                    )
            else:
                disqualifiers.append("No Tender / GeM Bid Reference Number found in MAF document")
        else:
            tender_matched = bool(extracted_tender_no)

        # 2. Expiry / Validity Date Check
        is_expired = False
        today = datetime.now(timezone.utc).date()
        if parsed_validity_date:
            if parsed_validity_date < today:
                is_expired = True
                disqualifiers.append(f"OEM Authorization expired on {parsed_validity_date.isoformat()}")
        else:
            warnings.append("Explicit MAF validity/expiry date could not be determined")

        # 3. Bidder Entity Name Fuzzy Matching
        bidder_name_match_score = 0.0
        bidder_matched = True
        if bidder_legal_name:
            if extracted_bidder:
                bidder_matched, bidder_name_match_score = is_fuzzy_name_match(
                    bidder_legal_name, extracted_bidder, threshold=70.0
                )
                if not bidder_matched:
                    disqualifiers.append(
                        f"Authorized entity in MAF ('{extracted_bidder}') does not match registered bidder name ('{bidder_legal_name}') (Match score: {bidder_name_match_score}%)"
                    )
            else:
                # If bidder name wasn't explicitly captured by regex, search if bidder legal name is in document text
                matched_in_text, score_in_text = is_fuzzy_name_match(bidder_legal_name, text, threshold=75.0)
                if not matched_in_text:
                    bidder_matched = False
                    disqualifiers.append(f"Registered bidder name ('{bidder_legal_name}') not found in MAF")

        is_compliant = bool(tender_matched and not is_expired and bidder_matched and extracted_oem)

        return {
            "oem_name": extracted_oem,
            "authorized_bidder_name": extracted_bidder,
            "extracted_tender_no": extracted_tender_no,
            "target_gem_bid_number": target_gem_bid_number,
            "validity_date": parsed_validity_date.isoformat() if parsed_validity_date else None,
            "is_expired": is_expired,
            "tender_matched": tender_matched,
            "bidder_name_match_score": bidder_name_match_score,
            "is_compliant": is_compliant,
            "disqualifiers": disqualifiers,
            "warnings": warnings,
        }

    @classmethod
    async def parse_pdf(cls, source: Any, target_gem_bid_number: Optional[str] = None, bidder_legal_name: Optional[str] = None) -> Dict[str, Any]:
        extracted = await PDFProcessor.extract_text(source)
        result = await cls.parse_text(
            text=extracted["full_text"],
            target_gem_bid_number=target_gem_bid_number,
            bidder_legal_name=bidder_legal_name,
        )
        result["pdf_metadata"] = extracted["metadata"]
        result["is_scanned"] = extracted["is_scanned"]
        return result


# ==========================================
# 2. Make in India (MII) Declaration Parser
# ==========================================

class MakeInIndiaParser:
    """
    Parser for Make in India (MII) Self/CA Declarations under Public Procurement (Preference to Make in India) Order.
    Evaluates Local Content Percentage, Supplier Tier (Class-I, Class-II, Non-Local), and UDIN validity.
    """

    PERCENTAGE_PATTERNS = [
        r"(?:local\s+content(?:\s+percentage)?|percentage\s+of\s+local\s+value\s+addition|indigenous\s+content)\s*(?:is|equals|of|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*%",
        r"([0-9]+(?:\.[0-9]+)?)\s*%\s*(?:local\s+content|local\s+value\s+addition)",
    ]

    LOCATION_PATTERNS = [
        r"(?:location|facility|plant|factory|place)\s+of\s+(?:local\s+value\s+addition|manufacturing)\s*[:\-]\s*([A-Za-z0-9\s,\.\-]+)",
        r"(?:value\s+addition\s+made\s+at)\s*[:\-]\s*([A-Za-z0-9\s,\.\-]+)",
    ]

    UDIN_PATTERNS = [
        r"(?:UDIN|ICAI\s*UDIN)\s*[:\-]?\s*([0-9]{2}[0-9]{6}[A-Z0-9]{10})",
        r"\b([0-9]{8}[A-Z0-9]{10})\b",
    ]

    @classmethod
    async def parse_text(cls, text: str, min_required_percentage: float = 50.0) -> Dict[str, Any]:
        """
        Parses MII declaration text and returns local content classification and UDIN details.
        """
        local_content_pct: Optional[float] = None
        for pattern in cls.PERCENTAGE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    local_content_pct = float(match.group(1))
                    break
                except ValueError:
                    continue

        location_of_addition: Optional[str] = None
        for pattern in cls.LOCATION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location_of_addition = match.group(1).split("\n")[0].strip()
                break

        udin: Optional[str] = None
        for pattern in cls.UDIN_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                udin = match.group(1).strip()
                break

        # Determine MII Class
        supplier_class = "Unknown"
        if local_content_pct is not None:
            if local_content_pct >= 50.0:
                supplier_class = "Class-I Local Supplier"
            elif local_content_pct >= 20.0:
                supplier_class = "Class-II Local Supplier"
            else:
                supplier_class = "Non-Local Supplier"

        disqualifiers = []
        warnings = []

        if local_content_pct is None:
            disqualifiers.append("Could not extract Make in India local content percentage from declaration")
        elif local_content_pct < min_required_percentage:
            disqualifiers.append(
                f"Local content percentage ({local_content_pct}%) is below required minimum threshold ({min_required_percentage}%) for Class-I preference"
            )

        udin_valid = None
        if udin:
            udin_valid, udin_err = validate_icai_udin(udin)
            if not udin_valid:
                warnings.append(f"ICAI UDIN verification warning: {udin_err}")

        is_compliant = bool(local_content_pct is not None and local_content_pct >= min_required_percentage)

        return {
            "local_content_percentage": local_content_pct,
            "supplier_class": supplier_class,
            "location_of_value_addition": location_of_addition,
            "udin": udin,
            "udin_valid": udin_valid,
            "min_required_percentage": min_required_percentage,
            "is_compliant": is_compliant,
            "disqualifiers": disqualifiers,
            "warnings": warnings,
        }

    @classmethod
    async def parse_pdf(cls, source: Any, min_required_percentage: float = 50.0) -> Dict[str, Any]:
        extracted = await PDFProcessor.extract_text(source)
        result = await cls.parse_text(
            text=extracted["full_text"],
            min_required_percentage=min_required_percentage,
        )
        result["pdf_metadata"] = extracted["metadata"]
        result["is_scanned"] = extracted["is_scanned"]
        return result


# ==========================================
# 3. CA Financial & Turnover Certificate Parser
# ==========================================

class FinancialCertificateParser:
    """
    Parser for Chartered Accountant (CA) Certified Turnover & Net Worth Certificates.
    Extracts 3-year annual turnover records, average turnover, net worth, and validates UDIN & tender threshold.
    """

    TURNOVER_ROW_PATTERN = r"(?:[\-\*•]?\s*(?:FY|Financial\s+Year)?\s*(20\d{2}[-\/](?:20)?\d{2}))\s*[:\-]?\s*(?:INR|Rs\.?|₹)?\s*([0-9]+(?:\.[0-9]+)?)\s*(Cr|Crore|Crores|Lakh|Lakhs|Lacs|Inr|Rupees)?"
    AVG_TURNOVER_PATTERN = r"(?:Average\s+Annual\s+Turnover|Avg\s+Turnover)\s*[:\-]?\s*(?:INR|Rs\.?|₹)?\s*([0-9]+(?:\.[0-9]+)?)\s*(Cr|Crore|Crores|Lakh|Lakhs|Lacs|Inr|Rupees)?"
    NET_WORTH_PATTERN = r"(?:Net\s*Worth|Networth)[^\n]*?(?:INR|Rs\.?|₹|is|:)\s*([0-9]+(?:\.[0-9]+)?)\s*(Cr|Crore|Crores|Lakh|Lakhs|Lacs|Inr|Rupees)?"
    UDIN_PATTERN = r"(?:UDIN|ICAI\s*UDIN)\s*[:\-]?\s*([0-9]{2}[0-9]{6}[A-Z0-9]{10})"
    CA_NAME_PATTERN = r"(?:Chartered\s+Accountant|For\s+M/s|CA)\s*[:\-]?\s*([A-Za-z\s,\.\-&]+?(?:Associates|LLP|Chartered\s+Accountants))"

    @classmethod
    def _convert_to_inr(cls, value: float, unit: Optional[str]) -> float:
        if not unit:
            return value
        u = unit.lower().strip()
        if "cr" in u:
            return value * 10_000_000.0  # 1 Crore = 10,000,000 INR
        if "lakh" in u or "lac" in u:
            return value * 100_000.0     # 1 Lakh = 100,000 INR
        return value

    @classmethod
    async def parse_text(cls, text: str, min_turnover_inr: float = 0.0) -> Dict[str, Any]:
        """
        Extracts financial turnover, net worth, and UDIN from certificate text.
        """
        turnover_by_fy: Dict[str, float] = {}

        for match in re.finditer(cls.TURNOVER_ROW_PATTERN, text, re.IGNORECASE):
            fy = match.group(1).replace("/", "-").strip()
            raw_val = float(match.group(2))
            unit = match.group(3)
            turnover_inr = cls._convert_to_inr(raw_val, unit)
            turnover_by_fy[fy] = turnover_inr

        # Calculate or extract average turnover
        avg_turnover_inr = 0.0
        if turnover_by_fy:
            avg_turnover_inr = sum(turnover_by_fy.values()) / len(turnover_by_fy)
        else:
            avg_match = re.search(cls.AVG_TURNOVER_PATTERN, text, re.IGNORECASE)
            if avg_match:
                avg_turnover_inr = cls._convert_to_inr(float(avg_match.group(1)), avg_match.group(2))

        # Extract Net Worth
        net_worth_inr: Optional[float] = None
        nw_match = re.search(cls.NET_WORTH_PATTERN, text, re.IGNORECASE)
        if nw_match:
            raw_nw = float(nw_match.group(1))
            nw_unit = nw_match.group(2)
            net_worth_inr = cls._convert_to_inr(raw_nw, nw_unit)

        # Extract UDIN
        udin: Optional[str] = None
        udin_match = re.search(cls.UDIN_PATTERN, text, re.IGNORECASE)
        if udin_match:
            udin = udin_match.group(1).strip()

        # Extract CA Name / Firm
        ca_firm: Optional[str] = None
        ca_match = re.search(cls.CA_NAME_PATTERN, text, re.IGNORECASE)
        if ca_match:
            ca_firm = ca_match.group(1).strip()

        disqualifiers = []
        warnings = []

        if not turnover_by_fy and avg_turnover_inr == 0.0:
            disqualifiers.append("No financial year turnover figures could be extracted from CA certificate")
        elif min_turnover_inr > 0.0 and avg_turnover_inr < min_turnover_inr:
            disqualifiers.append(
                f"Average Annual Turnover (₹{avg_turnover_inr:,.2f}) is below mandatory tender requirement of ₹{min_turnover_inr:,.2f}"
            )

        if net_worth_inr is not None and net_worth_inr <= 0.0:
            disqualifiers.append(f"Net Worth is negative or zero (₹{net_worth_inr:,.2f})")

        udin_valid = None
        if udin:
            udin_valid, udin_err = validate_icai_udin(udin)
            if not udin_valid:
                disqualifiers.append(f"Invalid CA UDIN: {udin_err}")
        else:
            warnings.append("ICAI UDIN missing from CA Financial Certificate")

        is_compliant = bool(
            (turnover_by_fy or avg_turnover_inr > 0.0)
            and (min_turnover_inr == 0.0 or avg_turnover_inr >= min_turnover_inr)
            and (net_worth_inr is None or net_worth_inr > 0.0)
            and (udin is None or udin_valid is True)
        )

        return {
            "turnover_by_fy": turnover_by_fy,
            "avg_turnover_inr": round(avg_turnover_inr, 2),
            "min_turnover_inr": min_turnover_inr,
            "net_worth_inr": round(net_worth_inr, 2) if net_worth_inr is not None else None,
            "udin": udin,
            "udin_valid": udin_valid,
            "ca_firm": ca_firm,
            "is_compliant": is_compliant,
            "disqualifiers": disqualifiers,
            "warnings": warnings,
        }

    @classmethod
    async def parse_pdf(cls, source: Any, min_turnover_inr: float = 0.0) -> Dict[str, Any]:
        extracted = await PDFProcessor.extract_text(source)
        result = await cls.parse_text(
            text=extracted["full_text"],
            min_turnover_inr=min_turnover_inr,
        )
        result["pdf_metadata"] = extracted["metadata"]
        result["is_scanned"] = extracted["is_scanned"]
        return result
