import hashlib
import json
from unittest.mock import AsyncMock, patch
import httpx
import pytest

from app.services.integrations.base import (
    AdapterTimeoutError,
    BaseStatutoryAdapter,
    InvalidIdentifierError,
    RateLimitError,
    StatutoryGatewayError,
)
from app.services.integrations.debarment_adapter import DebarmentAdapter
from app.services.integrations.epfo_adapter import EPFOAdapter
from app.services.integrations.gstn_adapter import GSTNAdapter, validate_gstin_checksum
from app.services.integrations.it_pan_adapter import IncomeTaxPANAdapter
from app.services.integrations.mock_server import MockStatutoryServer
from app.services.integrations.udyam_adapter import UdyamAdapter


# ==========================================
# 1. GSTN Adapter Tests
# ==========================================

@pytest.mark.asyncio
async def test_gstn_adapter_valid_compliant():
    adapter = GSTNAdapter()
    result = await adapter.verify("27ABCDE1234F1Z4")

    assert result["pillar"] == "GST"
    assert result["is_compliant"] is True
    assert result["findings"]["is_active"] is True
    assert result["findings"]["gstr3b_regularity_percentage"] == 100.0
    assert len(result["findings"]["disqualifiers"]) == 0
    assert len(result["payload_sha256"]) == 64


@pytest.mark.asyncio
async def test_gstn_adapter_inactive_suspended():
    adapter = GSTNAdapter()
    result = await adapter.verify("27ABCDE1234F1Z5")

    assert result["is_compliant"] is False
    assert result["findings"]["is_active"] is False
    assert any("Not Active" in d for d in result["findings"]["disqualifiers"])


@pytest.mark.asyncio
async def test_gstn_adapter_irregular_filing_defaulter():
    adapter = GSTNAdapter()
    result = await adapter.verify("27ABCDE1234F1Z9")

    assert result["is_compliant"] is False
    assert result["findings"]["gstr3b_regularity_percentage"] < 75.0
    assert any("GSTR-3B filing regularity" in d for d in result["findings"]["disqualifiers"])


@pytest.mark.asyncio
async def test_gstn_adapter_invalid_syntax():
    adapter = GSTNAdapter()
    with pytest.raises(InvalidIdentifierError) as exc_info:
        await adapter.verify("INVALID_GSTIN_123")
    assert "Invalid GSTIN syntax" in str(exc_info.value)


@pytest.mark.asyncio
async def test_gstn_adapter_injected_faults():
    adapter = GSTNAdapter()

    # Timeout
    with pytest.raises(AdapterTimeoutError):
        await adapter.verify("27ABCDE1234FTIMEOUT")

    # Rate limit (429)
    with pytest.raises(RateLimitError):
        await adapter.verify("27ABCDE1234FRATELIMIT")

    # Gateway Error (503)
    with pytest.raises(StatutoryGatewayError):
        await adapter.verify("27ABCDE1234FGATEWAYERR")


def test_gstin_checksum_utility():
    assert validate_gstin_checksum("27ABCDE1234F1Z5") is True
    assert validate_gstin_checksum("INVALID") is False


# ==========================================
# 2. Udyam MSME Adapter Tests
# ==========================================

@pytest.mark.asyncio
async def test_udyam_adapter_valid_active_with_nic_matching():
    adapter = UdyamAdapter()
    result = await adapter.verify(
        "UDYAM-MH-01-0012345",
        required_nic_codes=["26201", "26511"],
    )

    assert result["pillar"] == "UDYAM"
    assert result["is_compliant"] is True
    assert result["findings"]["is_active"] is True
    assert result["findings"]["enterprise_type"] == "Medium"
    assert "26201" in result["findings"]["matched_nic_codes"]
    assert len(result["findings"]["disqualifiers"]) == 0


@pytest.mark.asyncio
async def test_udyam_adapter_nic_mismatch_disqualification():
    adapter = UdyamAdapter()
    result = await adapter.verify(
        "UDYAM-MH-01-0012345",
        required_nic_codes=["99999"],  # Non-matching NIC code
    )

    assert result["is_compliant"] is False
    assert len(result["findings"]["matched_nic_codes"]) == 0
    assert any("do not match tender mandatory NIC codes" in d for d in result["findings"]["disqualifiers"])


@pytest.mark.asyncio
async def test_udyam_adapter_cancelled_status():
    adapter = UdyamAdapter()
    result = await adapter.verify("UDYAM-MH-01-0099999")

    assert result["is_compliant"] is False
    assert result["findings"]["is_active"] is False
    assert any("Not Active" in d for d in result["findings"]["disqualifiers"])


@pytest.mark.asyncio
async def test_udyam_adapter_invalid_syntax():
    adapter = UdyamAdapter()
    with pytest.raises(InvalidIdentifierError):
        await adapter.verify("UDYAM-INVALID-FORMAT")


# ==========================================
# 3. Income Tax PAN Adapter Tests
# ==========================================

@pytest.mark.asyncio
async def test_pan_adapter_valid_compliant():
    adapter = IncomeTaxPANAdapter()
    result = await adapter.verify("ABCDE1234F")

    assert result["pillar"] == "PAN"
    assert result["is_compliant"] is True
    assert result["findings"]["is_active"] is True
    assert result["findings"]["sec_206ab_specified_person"] is False
    assert len(result["findings"]["disqualifiers"]) == 0


@pytest.mark.asyncio
async def test_pan_adapter_sec_206ab_non_filer():
    adapter = IncomeTaxPANAdapter()
    result = await adapter.verify("ABCDE206AB")

    assert result["is_compliant"] is False
    assert result["findings"]["sec_206ab_specified_person"] is True
    assert any("Section 206AB" in d for d in result["findings"]["disqualifiers"])


@pytest.mark.asyncio
async def test_pan_adapter_inactive_pan():
    adapter = IncomeTaxPANAdapter()
    result = await adapter.verify("ABCDEINACT")

    assert result["is_compliant"] is False
    assert result["findings"]["is_active"] is False
    assert any("Inoperative" in d for d in result["findings"]["disqualifiers"])


@pytest.mark.asyncio
async def test_pan_adapter_invalid_syntax():
    adapter = IncomeTaxPANAdapter()
    with pytest.raises(InvalidIdentifierError):
        await adapter.verify("INVALID_PAN_123")


# ==========================================
# 4. Debarment Adapter Tests
# ==========================================

@pytest.mark.asyncio
async def test_debarment_adapter_clean_record():
    adapter = DebarmentAdapter()
    result = await adapter.verify(
        identifier="ABCDE1234F",
        company_name="Clean Infotech Private Limited",
        director_dins=["01234567"],
    )

    assert result["pillar"] == "DEBARMENT"
    assert result["is_compliant"] is True
    assert result["findings"]["is_debarred"] is False
    assert result["findings"]["total_active_orders"] == 0
    assert len(result["findings"]["disqualifiers"]) == 0


@pytest.mark.asyncio
async def test_debarment_adapter_active_debarment_order():
    adapter = DebarmentAdapter()
    result = await adapter.verify(
        identifier="ABCDE9999F",
        company_name="Blacklisted Global Solutions Ltd",
    )

    assert result["pillar"] == "DEBARMENT"
    assert result["is_compliant"] is False
    assert result["findings"]["is_debarred"] is True
    assert result["findings"]["total_active_orders"] == 1
    assert any("ACTIVE DEBARMENT ORDER" in d for d in result["findings"]["disqualifiers"])


# ==========================================
# 5. EPFO Adapter Tests
# ==========================================

@pytest.mark.asyncio
async def test_epfo_adapter_compliant():
    adapter = EPFOAdapter()
    result = await adapter.verify("MH/BAN/0012345/000")

    assert result["pillar"] == "EPFO"
    assert result["is_compliant"] is True
    assert result["findings"]["is_active"] is True
    assert result["findings"]["ecr_regularity_score"] == 100.0


@pytest.mark.asyncio
async def test_epfo_adapter_inactive():
    adapter = EPFOAdapter()
    result = await adapter.verify("MH/BAN/INACT12/000")

    assert result["is_compliant"] is False
    assert result["findings"]["is_active"] is False
    assert any("Inactive" in d for d in result["findings"]["disqualifiers"])


# ==========================================
# 6. Audit Trail Cryptographic Hash Tests
# ==========================================

def test_audit_payload_sha256_reproducibility():
    payload = {
        "b_key": "sample value",
        "a_key": 12345,
        "nested": {"z": True, "y": [1, 2, 3]},
    }
    hash1 = BaseStatutoryAdapter.compute_payload_sha256(payload)

    # Different key insertion order should yield identical SHA-256
    payload_reordered = {
        "nested": {"y": [1, 2, 3], "z": True},
        "a_key": 12345,
        "b_key": "sample value",
    }
    hash2 = BaseStatutoryAdapter.compute_payload_sha256(payload_reordered)

    assert hash1 == hash2
    assert len(hash1) == 64


# ==========================================
# 7. Live HTTP Client & Retry Backoff Tests
# ==========================================

@pytest.mark.asyncio
async def test_execute_http_request_success():
    class DummyAdapter(BaseStatutoryAdapter):
        async def verify(self, identifier: str, **kwargs):
            return {}

    adapter = DummyAdapter(
        portal_name="TestPortal",
        base_url="https://api.test.gov.in",
        api_key="secret-key",
        max_retries=2,
        backoff_factor=0.01,
    )

    def handler(request: httpx.Request):
        return httpx.Response(200, json={"status": "Success", "data": 123})

    orig_async_client = httpx.AsyncClient
    transport = httpx.MockTransport(handler)

    with patch("httpx.AsyncClient", side_effect=lambda *a, **kw: orig_async_client(transport=transport, **kw)):
        status_code, body = await adapter.execute_http_request("GET", "https://api.test.gov.in/test")
        assert status_code == 200
        assert body["status"] == "Success"


@pytest.mark.asyncio
async def test_execute_http_request_retry_on_500():
    class DummyAdapter(BaseStatutoryAdapter):
        async def verify(self, identifier: str, **kwargs):
            return {}

    adapter = DummyAdapter(
        portal_name="TestPortal",
        base_url="https://api.test.gov.in",
        max_retries=2,
        backoff_factor=0.01,
    )

    call_count = 0

    def handler(request: httpx.Request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(502, text="Bad Gateway")
        return httpx.Response(200, json={"recovered": True})

    orig_async_client = httpx.AsyncClient
    transport = httpx.MockTransport(handler)

    with patch("httpx.AsyncClient", side_effect=lambda *a, **kw: orig_async_client(transport=transport, **kw)):
        status_code, body = await adapter.execute_http_request("GET", "https://api.test.gov.in/retry")
        assert status_code == 200
        assert body["recovered"] is True
        assert call_count == 2
