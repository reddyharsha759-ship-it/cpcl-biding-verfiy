import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.integrations.base import (
    AdapterTimeoutError,
    InvalidIdentifierError,
    RateLimitError,
    StatutoryGatewayError,
)


class MockStatutoryServer:
    """
    Deterministic synthetic sandbox for Indian statutory government portals.
    Simulates real-world responses, edge cases, and failure modes.
    """

    @classmethod
    def _check_injected_faults(cls, identifier: str, portal_name: str) -> None:
        """Injects simulated network/portal errors based on magic tokens in the identifier."""
        identifier_upper = identifier.upper()
        if "TIMEOUT" in identifier_upper or identifier_upper.endswith("9991F") or identifier_upper.endswith("1ZT"):
            raise AdapterTimeoutError(
                message=f"Simulated timeout error from {portal_name}",
                portal_name=portal_name,
            )
        if "RATELIMIT" in identifier_upper or identifier_upper.endswith("9992F") or identifier_upper.endswith("1ZR"):
            raise RateLimitError(
                message=f"Simulated HTTP 429 rate limit from {portal_name}",
                portal_name=portal_name,
                status_code=429,
            )
        if "GATEWAYERR" in identifier_upper or identifier_upper.endswith("9993F") or identifier_upper.endswith("1ZG"):
            raise StatutoryGatewayError(
                message=f"Simulated HTTP 503 statutory gateway error from {portal_name}",
                portal_name=portal_name,
                status_code=503,
            )

    # ==========================================
    # 1. GSTN Mock Portal
    # ==========================================
    @classmethod
    def get_gstn_response(cls, gstin: str) -> Dict[str, Any]:
        cls._check_injected_faults(gstin, "GSTN")

        gstin_clean = gstin.strip().upper()
        state_code = gstin_clean[:2] if len(gstin_clean) >= 2 else "27"
        pan = gstin_clean[2:12] if len(gstin_clean) >= 12 else "ABCDE1234F"

        # Edge-case 1: Inactive / Suspended GSTIN
        if gstin_clean.endswith("1Z5") or "INACT" in gstin_clean:
            return {
                "gstin": gstin_clean,
                "status": "Inactive",
                "trade_name": "Acme Technologies (Suspended)",
                "legal_name": "Acme Tech Solutions Private Limited",
                "state_code": state_code,
                "pan": pan,
                "registration_date": "2018-07-01",
                "cancellation_date": "2025-11-15",
                "taxpayer_type": "Regular",
                "filing_frequency": "Monthly",
                "filing_history": cls._generate_filing_history(regular=False, num_filed=4),
            }

        # Edge-case 2: Defaulter / Irregular GSTR-3B filings (<60% regularity)
        if gstin_clean.endswith("1Z9") or "DEFAULT" in gstin_clean:
            return {
                "gstin": gstin_clean,
                "status": "Active",
                "trade_name": "Irregular Enterprises",
                "legal_name": "Irregular Trading Corporation",
                "state_code": state_code,
                "pan": pan,
                "registration_date": "2019-03-20",
                "cancellation_date": None,
                "taxpayer_type": "Regular",
                "filing_frequency": "Monthly",
                "filing_history": cls._generate_filing_history(regular=False, num_filed=5),
            }

        # Default: Fully active, compliant with 100% trailing 12-month regularity
        return {
            "gstin": gstin_clean,
            "status": "Active",
            "trade_name": "Premier Solutions",
            "legal_name": "Premier Industrial & Tech Solutions Private Limited",
            "state_code": state_code,
            "pan": pan,
            "registration_date": "2017-07-01",
            "cancellation_date": None,
            "taxpayer_type": "Regular",
            "filing_frequency": "Monthly",
            "filing_history": cls._generate_filing_history(regular=True, num_filed=12),
        }

    @staticmethod
    def _generate_filing_history(regular: bool, num_filed: int = 12) -> List[Dict[str, Any]]:
        """Generates filing records for the last 12 months for GSTR-1 and GSTR-3B."""
        months = [
            ("2025-09", "September 2025"),
            ("2025-10", "October 2025"),
            ("2025-11", "November 2025"),
            ("2025-12", "December 2025"),
            ("2026-01", "January 2026"),
            ("2026-02", "February 2026"),
            ("2026-03", "March 2026"),
            ("2026-04", "April 2026"),
            ("2026-05", "May 2026"),
            ("2026-06", "June 2026"),
            ("2026-07", "July 2026"),
            ("2026-08", "August 2026"),
        ]
        history = []
        for idx, (period_code, month_name) in enumerate(months):
            is_filed = idx < num_filed if not regular else True
            for return_type in ["GSTR-1", "GSTR-3B"]:
                history.append({
                    "tax_period": period_code,
                    "month_name": month_name,
                    "return_type": return_type,
                    "status": "Filed" if is_filed else "Not Filed",
                    "filing_date": f"{period_code}-20" if is_filed else None,
                    "arn": f"AA{period_code.replace('-', '')}{return_type[:2]}001" if is_filed else None,
                })
        return history

    # ==========================================
    # 2. Udyam MSME Mock Portal
    # ==========================================
    @classmethod
    def get_udyam_response(cls, udyam_no: str) -> Dict[str, Any]:
        cls._check_injected_faults(udyam_no, "Udyam")

        udyam_clean = udyam_no.strip().upper()

        if "INACT" in udyam_clean or udyam_clean.endswith("0099999"):
            return {
                "udyam_reg_no": udyam_clean,
                "status": "Cancelled",
                "enterprise_name": "Defunct Manufacturing Private Limited",
                "enterprise_type": "Micro",
                "major_activity": "Manufacturing",
                "social_category": "General",
                "gender": "Male",
                "state": "Maharashtra",
                "district": "Pune",
                "date_of_registration": "2021-04-12",
                "nic_codes": ["26511"],
                "investment_in_plant_machinery_lakhs": 25.0,
                "turnover_lakhs": 80.0,
            }

        # Default Active MSME
        return {
            "udyam_reg_no": udyam_clean,
            "status": "Active",
            "enterprise_name": "Apex Engineering & Technologies Private Limited",
            "enterprise_type": "Medium",
            "major_activity": "Manufacturing",
            "social_category": "General",
            "gender": "Female",
            "state": "Maharashtra",
            "district": "Mumbai",
            "date_of_registration": "2020-08-15",
            "nic_codes": ["26201", "26511", "26512", "62011", "62020"],
            "investment_in_plant_machinery_lakhs": 2400.0,
            "turnover_lakhs": 9500.0,
        }

    # ==========================================
    # 3. Income Tax PAN & Section 206AB Mock Portal
    # ==========================================
    @classmethod
    def get_income_tax_pan_response(cls, pan: str) -> Dict[str, Any]:
        cls._check_injected_faults(pan, "IncomeTax")

        pan_clean = pan.strip().upper()

        # Inactive PAN (e.g. ABCDE0000F or containing INACT)
        if "INACT" in pan_clean or pan_clean.endswith("0000F"):
            return {
                "pan": pan_clean,
                "status": "Inoperative",
                "category": "Company",
                "name": "Inactive Enterprises Private Limited",
                "aadhaar_seeding_status": "Not Linked",
                "sec_206ab_specified_person": True,
                "sec_206ab_non_filer_years": ["AY 2024-25", "AY 2025-26"],
                "itr_filing_compliance": "Non-Compliant",
            }

        # Specified person under Section 206AB (e.g. ABCDE2060F or ending in 206AB)
        if pan_clean.endswith("2060F") or "206AB" in pan_clean or "NONFILER" in pan_clean:
            return {
                "pan": pan_clean,
                "status": "Active",
                "category": "Company",
                "name": "Defaulting Tech Private Limited",
                "aadhaar_seeding_status": "Linked",
                "sec_206ab_specified_person": True,
                "sec_206ab_non_filer_years": ["AY 2024-25"],
                "itr_filing_compliance": "Defaulter (Higher TDS Applicable under Sec 206AB)",
            }

        # Default: Active, fully compliant
        return {
            "pan": pan_clean,
            "status": "Active",
            "category": "Company",
            "name": "Premier Industrial & Tech Solutions Private Limited",
            "aadhaar_seeding_status": "Linked",
            "sec_206ab_specified_person": False,
            "sec_206ab_non_filer_years": [],
            "itr_filing_compliance": "Compliant",
        }

    # ==========================================
    # 4. CPPP Debarment & Blacklist Mock Portal
    # ==========================================
    @classmethod
    def get_debarment_response(
        cls,
        pan: Optional[str] = None,
        company_name: Optional[str] = None,
        director_dins: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        query_key = f"{pan or ''} {company_name or ''} {' '.join(director_dins or [])}"
        cls._check_injected_faults(query_key, "CPPP_Debarment")

        pan_clean = (pan or "").strip().upper()
        name_clean = (company_name or "").strip().upper()

        # Trigger debarment if PAN ends in 9999F, contains DEBAR, or name contains BLACKLIST
        if (
            pan_clean.endswith("9999F")
            or "DEBAR" in pan_clean
            or "BLACKLIST" in name_clean
            or any((din or "").endswith("999") for din in (director_dins or []))
        ):
            return {
                "is_debarred": True,
                "total_active_orders": 1,
                "orders": [
                    {
                        "order_id": "DEB/MOD/2024/089",
                        "issuing_authority": "Ministry of Defence (DDP)",
                        "debarred_entity_pan": pan_clean or "ABCDE9999F",
                        "debarred_entity_name": company_name or "Blacklisted Global Solutions Ltd",
                        "reason": "Submission of forged OEM authorization certificate in bid GEM/2024/B/110022",
                        "debarment_start_date": "2024-10-01",
                        "debarment_end_date": "2027-09-30",
                        "debarment_type": "Pan-India Central Government Banned List (CPPP & GeM)",
                        "status": "ACTIVE",
                    }
                ],
            }

        # Default clean record
        return {
            "is_debarred": False,
            "total_active_orders": 0,
            "orders": [],
        }

    # ==========================================
    # 5. EPFO Mock Portal
    # ==========================================
    @classmethod
    def get_epfo_response(cls, establishment_code: str) -> Dict[str, Any]:
        cls._check_injected_faults(establishment_code, "EPFO")
        code_clean = establishment_code.strip().upper()

        if "INACT" in code_clean:
            return {
                "establishment_code": code_clean,
                "status": "Inactive",
                "establishment_name": "Defunct Corp",
                "ecr_regularity_score": 30.0,
                "is_compliant": False,
            }

        return {
            "establishment_code": code_clean,
            "status": "Active",
            "establishment_name": "Premier Industrial & Tech Solutions Private Limited",
            "ecr_regularity_score": 100.0,
            "is_compliant": True,
            "total_contributing_members": 142,
        }
