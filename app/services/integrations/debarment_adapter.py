from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.integrations.base import BaseStatutoryAdapter
from app.services.integrations.mock_server import MockStatutoryServer


class DebarmentAdapter(BaseStatutoryAdapter):
    """
    Adapter for the Central Public Procurement Portal (CPPP) and GeM Debarment / Blacklist Registers.
    Checks whether a bidder, director, or corporate entity is actively debarred or banned from public procurement.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        super().__init__(
            portal_name="CPPP_Debarment",
            base_url=base_url or settings.CPPP_DEBARMENT_API_URL,
            api_key=api_key or settings.CPPP_DEBARMENT_API_KEY,
            timeout=timeout,
            max_retries=max_retries,
        )

    async def verify(
        self,
        identifier: str,
        company_name: Optional[str] = None,
        director_dins: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Verifies active debarment orders against PAN, Company Name, or Director DINs.
        Identifier defaults to PAN or Company Identifier.
        """
        pan = identifier.strip().upper() if identifier else None

        if self.is_mock_mode:
            raw_payload = MockStatutoryServer.get_debarment_response(
                pan=pan,
                company_name=company_name,
                director_dins=director_dins,
            )
        else:
            url = f"{self.base_url}/search"
            payload = {
                "pan": pan,
                "company_name": company_name,
                "director_dins": director_dins or [],
            }
            status_code, raw_payload = await self.execute_http_request(
                method="POST", url=url, json_body=payload
            )

        is_debarred = bool(raw_payload.get("is_debarred", False))
        orders: List[Dict[str, Any]] = raw_payload.get("orders", [])

        # Compliant ONLY IF not debarred
        is_compliant = not is_debarred

        disqualifiers = []
        for order in orders:
            authority = order.get("issuing_authority", "Government Authority")
            reason = order.get("reason", "Debarment Order")
            start = order.get("debarment_start_date")
            end = order.get("debarment_end_date")
            disqualifiers.append(
                f"ACTIVE DEBARMENT ORDER [{order.get('order_id')}]: Issued by {authority} from {start} to {end}. Reason: {reason}"
            )

        findings = {
            "pan": pan,
            "company_name": company_name,
            "director_dins": director_dins or [],
            "is_debarred": is_debarred,
            "total_active_orders": len(orders),
            "orders": orders,
            "disqualifiers": disqualifiers,
            "warnings": [],
        }

        payload_sha256 = self.compute_payload_sha256(raw_payload)

        return {
            "pillar": "DEBARMENT",
            "is_compliant": is_compliant,
            "raw_payload": raw_payload,
            "payload_sha256": payload_sha256,
            "findings": findings,
        }
