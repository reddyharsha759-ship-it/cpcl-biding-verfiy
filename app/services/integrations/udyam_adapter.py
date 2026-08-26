import re
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.integrations.base import (
    BaseStatutoryAdapter,
    InvalidIdentifierError,
)
from app.services.integrations.mock_server import MockStatutoryServer

UDYAM_REGEX = r"^UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7}$"


class UdyamAdapter(BaseStatutoryAdapter):
    """
    Adapter for the Ministry of MSME Udyam Registration Portal.
    Extracts enterprise classification (Micro, Small, Medium), major activities,
    and registered 2-digit/4-digit/5-digit NIC codes.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        super().__init__(
            portal_name="Udyam",
            base_url=base_url or settings.UDYAM_API_URL,
            api_key=api_key or settings.UDYAM_API_KEY,
            timeout=timeout,
            max_retries=max_retries,
        )

    def validate_format(self, udyam_no: str) -> str:
        clean = udyam_no.strip().upper()
        if not re.match(UDYAM_REGEX, clean):
            raise InvalidIdentifierError(
                message=f"Invalid Udyam Registration Number format: '{udyam_no}'. Must match pattern UDYAM-XX-00-0000000.",
                portal_name=self.portal_name,
                details={"udyam_reg_no": udyam_no},
            )
        return clean

    async def verify(self, identifier: str, required_nic_codes: Optional[List[str]] = None, **kwargs: Any) -> Dict[str, Any]:
        """
        Verifies Udyam registration validity, active status, classification tier, and NIC code coverage.
        """
        clean_udyam = self.validate_format(identifier)

        if self.is_mock_mode:
            raw_payload = MockStatutoryServer.get_udyam_response(clean_udyam)
        else:
            url = f"{self.base_url}/enterprise/{clean_udyam}"
            status_code, raw_payload = await self.execute_http_request(method="GET", url=url)

        status = raw_payload.get("status", "Unknown")
        is_active = status.lower() == "active"
        enterprise_type = raw_payload.get("enterprise_type", "Unknown")
        major_activity = raw_payload.get("major_activity", "Unknown")
        registered_nic_codes = raw_payload.get("nic_codes", [])

        # NIC code matching if tender has mandatory NIC requirements
        matched_nic_codes = []
        nic_compliant = True
        if required_nic_codes:
            # Check if any required NIC code prefix matches registered NIC codes
            for req in required_nic_codes:
                if any(nic.startswith(req) or req.startswith(nic) for nic in registered_nic_codes):
                    matched_nic_codes.append(req)
            if not matched_nic_codes:
                nic_compliant = False

        disqualifiers = []
        warnings = []
        if not is_active:
            disqualifiers.append(f"Udyam registration status is '{status}' (Not Active)")
        if required_nic_codes and not nic_compliant:
            disqualifiers.append(f"Bidder NIC codes {registered_nic_codes} do not match tender mandatory NIC codes {required_nic_codes}")

        is_compliant = is_active and nic_compliant

        findings = {
            "udyam_reg_no": clean_udyam,
            "enterprise_name": raw_payload.get("enterprise_name"),
            "status": status,
            "is_active": is_active,
            "enterprise_type": enterprise_type,
            "major_activity": major_activity,
            "registered_nic_codes": registered_nic_codes,
            "matched_nic_codes": matched_nic_codes,
            "investment_in_plant_machinery_lakhs": raw_payload.get("investment_in_plant_machinery_lakhs"),
            "turnover_lakhs": raw_payload.get("turnover_lakhs"),
            "disqualifiers": disqualifiers,
            "warnings": warnings,
        }

        payload_sha256 = self.compute_payload_sha256(raw_payload)

        return {
            "pillar": "UDYAM",
            "is_compliant": is_compliant,
            "raw_payload": raw_payload,
            "payload_sha256": payload_sha256,
            "findings": findings,
        }
