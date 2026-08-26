from typing import Any, Dict, Optional

from app.core.config import settings
from app.services.integrations.base import BaseStatutoryAdapter
from app.services.integrations.mock_server import MockStatutoryServer


class EPFOAdapter(BaseStatutoryAdapter):
    """
    Adapter for the Employees' Provident Fund Organisation (EPFO) Portal.
    Validates establishment code validity, active status, and monthly ECR electronic challan filings.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        super().__init__(
            portal_name="EPFO",
            base_url=base_url or settings.EPFO_API_URL,
            api_key=api_key or settings.EPFO_API_KEY,
            timeout=timeout,
            max_retries=max_retries,
        )

    async def verify(self, identifier: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Verifies EPFO establishment active status and ECR regularity.
        """
        clean_code = identifier.strip().upper()

        if self.is_mock_mode:
            raw_payload = MockStatutoryServer.get_epfo_response(clean_code)
        else:
            url = f"{self.base_url}/establishment/{clean_code}"
            status_code, raw_payload = await self.execute_http_request(method="GET", url=url)

        status = raw_payload.get("status", "Unknown")
        is_active = status.lower() == "active"
        ecr_score = float(raw_payload.get("ecr_regularity_score", 0.0))
        is_compliant = is_active and ecr_score >= 70.0

        disqualifiers = []
        warnings = []
        if not is_active:
            disqualifiers.append(f"EPFO establishment is {status}")
        if ecr_score < 70.0:
            disqualifiers.append(f"EPFO ECR regularity score is {ecr_score}% (Minimum 70% required)")

        findings = {
            "establishment_code": clean_code,
            "establishment_name": raw_payload.get("establishment_name"),
            "status": status,
            "is_active": is_active,
            "ecr_regularity_score": ecr_score,
            "total_contributing_members": raw_payload.get("total_contributing_members"),
            "disqualifiers": disqualifiers,
            "warnings": warnings,
        }

        payload_sha256 = self.compute_payload_sha256(raw_payload)

        return {
            "pillar": "EPFO",
            "is_compliant": is_compliant,
            "raw_payload": raw_payload,
            "payload_sha256": payload_sha256,
            "findings": findings,
        }
