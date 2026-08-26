import re
from typing import Any, Dict, Optional

from app.core.config import settings
from app.services.integrations.base import (
    BaseStatutoryAdapter,
    InvalidIdentifierError,
)
from app.services.integrations.mock_server import MockStatutoryServer

PAN_REGEX = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"


class IncomeTaxPANAdapter(BaseStatutoryAdapter):
    """
    Adapter for the Income Tax Department (CBDT) Portal.
    Validates PAN active status, entity categorization, and Section 206AB / 206CCA
    compliance status for non-filer identification.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        super().__init__(
            portal_name="IncomeTax_PAN",
            base_url=base_url or settings.INCOME_TAX_API_URL,
            api_key=api_key or settings.INCOME_TAX_API_KEY,
            timeout=timeout,
            max_retries=max_retries,
        )

    def validate_format(self, pan: str) -> str:
        clean = pan.strip().upper()
        if self.is_mock_mode and any(token in clean for token in ("TIMEOUT", "RATELIMIT", "GATEWAYERR", "206AB", "INACT")):
            return clean
        if not re.match(PAN_REGEX, clean):
            raise InvalidIdentifierError(
                message=f"Invalid PAN format: '{pan}'. Must be a 10-character alphanumeric PAN string (e.g., ABCDE1234F).",
                portal_name=self.portal_name,
                details={"pan": pan},
            )
        return clean

    async def verify(self, identifier: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Verifies PAN active status and Section 206AB compliance.
        """
        clean_pan = self.validate_format(identifier)

        if self.is_mock_mode:
            raw_payload = MockStatutoryServer.get_income_tax_pan_response(clean_pan)
        else:
            url = f"{self.base_url}/pan-verification/{clean_pan}"
            status_code, raw_payload = await self.execute_http_request(method="GET", url=url)

        status = raw_payload.get("status", "Unknown")
        is_active = status.lower() == "active"
        is_sec_206ab_specified_person = bool(raw_payload.get("sec_206ab_specified_person", False))
        non_filer_years = raw_payload.get("sec_206ab_non_filer_years", [])
        aadhaar_seeding = raw_payload.get("aadhaar_seeding_status", "Linked")

        # Criteria: PAN must be active AND not a specified person under Section 206AB
        is_compliant = is_active and not is_sec_206ab_specified_person

        disqualifiers = []
        warnings = []
        if not is_active:
            disqualifiers.append(f"PAN status is '{status}' (Inoperative or Inactive)")
        if is_sec_206ab_specified_person:
            disqualifiers.append(
                f"Flagged as 'Specified Person' under Section 206AB of Income Tax Act for non-filing of ITR in {non_filer_years}"
            )
        if aadhaar_seeding.lower() == "not linked":
            warnings.append("Aadhaar seeding is pending with PAN")

        findings = {
            "pan": clean_pan,
            "registered_name": raw_payload.get("name"),
            "category": raw_payload.get("category"),
            "status": status,
            "is_active": is_active,
            "sec_206ab_specified_person": is_sec_206ab_specified_person,
            "non_filer_years": non_filer_years,
            "aadhaar_seeding_status": aadhaar_seeding,
            "itr_filing_compliance": raw_payload.get("itr_filing_compliance"),
            "disqualifiers": disqualifiers,
            "warnings": warnings,
        }

        payload_sha256 = self.compute_payload_sha256(raw_payload)

        return {
            "pillar": "PAN",
            "is_compliant": is_compliant,
            "raw_payload": raw_payload,
            "payload_sha256": payload_sha256,
            "findings": findings,
        }
