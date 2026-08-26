import abc
import asyncio
import hashlib
import json
import logging
from typing import Any, Dict, Optional, Tuple

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


# ==========================================
# Statutory Integration Exceptions
# ==========================================

class StatutoryIntegrationError(Exception):
    """Base exception for statutory portal integration failures."""

    def __init__(self, message: str, portal_name: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.portal_name = portal_name
        self.status_code = status_code
        self.details = details or {}


class InvalidIdentifierError(StatutoryIntegrationError):
    """Raised when an identifier (GSTIN, PAN, Udyam, etc.) violates statutory syntax or checksum."""
    pass


class StatutoryGatewayError(StatutoryIntegrationError):
    """Raised when the statutory gateway returns a 5xx server error or unparseable response."""
    pass


class RateLimitError(StatutoryIntegrationError):
    """Raised when statutory portal rate limits (HTTP 429) are exhausted."""
    pass


class AdapterTimeoutError(StatutoryIntegrationError):
    """Raised when the statutory portal fails to respond within the configured timeout window."""
    pass


# ==========================================
# Base Statutory Adapter
# ==========================================

class BaseStatutoryAdapter(abc.ABC):
    """Abstract base class for government portal integration adapters."""

    def __init__(
        self,
        portal_name: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        backoff_factor: Optional[float] = None,
    ):
        self.portal_name = portal_name
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout or settings.PORTAL_REQUEST_TIMEOUT_SECONDS
        self.max_retries = max_retries if max_retries is not None else settings.PORTAL_MAX_RETRIES
        self.backoff_factor = backoff_factor or settings.PORTAL_RETRY_BACKOFF_FACTOR

    @property
    def is_mock_mode(self) -> bool:
        """Determines if the adapter should execute against synthetic mock datasets."""
        if settings.USE_MOCK_PORTALS:
            return True
        if settings.APP_ENV in ("development", "test"):
            return True
        if not self.base_url or not self.api_key:
            return True
        return False

    @staticmethod
    def compute_payload_sha256(payload: Any) -> str:
        """Computes a canonical SHA-256 hash of a payload dictionary or object."""
        if isinstance(payload, str):
            encoded = payload.encode("utf-8")
        else:
            canonical_json = json.dumps(payload, sort_keys=True, default=str)
            encoded = canonical_json.encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    async def execute_http_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Executes an HTTP request with exponential backoff retries on transient errors.
        """
        req_headers = {"User-Agent": f"GeM-Compliance-Engine/1.0 ({self.portal_name})"}
        if self.api_key:
            req_headers["Authorization"] = f"Bearer {self.api_key}"
            req_headers["X-API-Key"] = self.api_key
        if headers:
            req_headers.update(headers)

        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=req_headers,
                        params=params,
                        json=json_body,
                    )

                    if response.status_code == 429:
                        retry_after = float(response.headers.get("Retry-After", self.backoff_factor * (2 ** (attempt - 1))))
                        if attempt < self.max_retries:
                            logger.warning(f"Rate limited by {self.portal_name}. Retrying in {retry_after}s...")
                            await asyncio.sleep(retry_after)
                            continue
                        raise RateLimitError(
                            message=f"Rate limit exceeded for {self.portal_name}",
                            portal_name=self.portal_name,
                            status_code=429,
                        )

                    if 500 <= response.status_code < 600:
                        if attempt < self.max_retries:
                            sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                            logger.warning(f"Server error {response.status_code} from {self.portal_name}. Retrying in {sleep_time}s...")
                            await asyncio.sleep(sleep_time)
                            continue
                        raise StatutoryGatewayError(
                            message=f"Statutory gateway {self.portal_name} returned status {response.status_code}",
                            portal_name=self.portal_name,
                            status_code=response.status_code,
                            details={"response_body": response.text},
                        )

                    try:
                        resp_data = response.json()
                    except json.JSONDecodeError:
                        resp_data = {"raw_text": response.text}

                    return response.status_code, resp_data

            except (httpx.TimeoutException, asyncio.TimeoutError) as exc:
                last_exception = exc
                if attempt < self.max_retries:
                    sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                    logger.warning(f"Timeout connecting to {self.portal_name}. Retrying in {sleep_time}s...")
                    await asyncio.sleep(sleep_time)
                    continue
                raise AdapterTimeoutError(
                    message=f"Request to statutory portal {self.portal_name} timed out after {self.timeout}s",
                    portal_name=self.portal_name,
                    details={"error": str(exc)},
                ) from exc

            except httpx.RequestError as exc:
                last_exception = exc
                if attempt < self.max_retries:
                    sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                    await asyncio.sleep(sleep_time)
                    continue
                raise StatutoryGatewayError(
                    message=f"Network error connecting to {self.portal_name}: {exc}",
                    portal_name=self.portal_name,
                    details={"error": str(exc)},
                ) from exc

        raise StatutoryGatewayError(
            message=f"Max retries exceeded for {self.portal_name}",
            portal_name=self.portal_name,
            details={"last_error": str(last_exception)},
        )

    @abc.abstractmethod
    async def verify(self, identifier: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Executes statutory compliance verification against the portal.
        Returns a standardized dictionary containing:
          - is_compliant: bool
          - raw_payload: dict
          - payload_sha256: str
          - findings: dict
        """
        pass
