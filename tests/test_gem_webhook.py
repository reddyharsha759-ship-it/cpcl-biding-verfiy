"""
Unit Tests for Live GeM Webhook Endpoint & Event Processing
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_gem_webhook_valid_bid_submission():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "gem_bid_number": "GEM/2026/B/889900",
            "tender_id": "CPCL/MANALI/M&C/2026/160",
            "vendor_name": "Bharat Forge Energy Equipment Ltd",
            "gstin": "27AABCB1234K1Z5",
            "pan": "AABCB1234K",
            "udyam_registration": "UDYAM-MH-12-0055443",
            "declared_local_content": 72.5,
            "oem_maf_attached": True,
            "annual_turnover_cr": 14.80,
            "nic_code": "27100"
        }
        resp = await client.post("/api/v1/gem/webhook/bid-submission", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "PROCESSED"
        assert data["gem_bid_number"] == "GEM/2026/B/889900"
        assert data["risk_tier"] == "GREEN"
        assert data["bci_score"] >= 80.0
        assert data["overall_compliance"] is True
        assert len(data["audit_seal"]) == 64


@pytest.mark.asyncio
async def test_gem_webhook_debarred_bidder_rejection():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "gem_bid_number": "GEM/2026/B/999999",
            "tender_id": "CPCL/MANALI/M&C/2026/160",
            "vendor_name": "Debarred Global Suppliers Pvt Ltd",
            "gstin": "27AAPFV9999L1Z9",
            "pan": "AAPFV9999L",
            "oem_maf_attached": False
        }
        resp = await client.post("/api/v1/gem/webhook/bid-submission", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_tier"] == "RED"
        assert data["bci_score"] < 50.0
        assert data["overall_compliance"] is False
