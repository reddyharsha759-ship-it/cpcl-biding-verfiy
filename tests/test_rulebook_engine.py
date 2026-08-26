"""
Comprehensive Test Suite for Dynamic Rule Book & Regulatory Knowledge Base
Tests RulebookLoader, PolicyVectorStore, RuleEvaluator, and REST API Endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.rule_schemas import (
    RuleClause,
    RuleCondition,
    RuleConditionOperator,
    RuleEvaluationRequest,
    RuleSeverity,
)
from app.services.rulebook.loader import RulebookLoader
from app.services.rulebook.rule_evaluator import RuleEvaluator
from app.services.rulebook.vector_store import PolicyVectorStore


def test_rulebook_loader_default_rules():
    """Verifies that all pre-seeded default statutory rulebooks load correctly."""
    rbs = RulebookLoader.load_default_rulebooks()
    assert len(rbs) >= 3

    rb_ids = {rb.id for rb in rbs}
    assert "GFR_2017" in rb_ids
    assert "GEM_GTC_4" in rb_ids
    assert "MII_PPP_2017" in rb_ids

    gfr = next(rb for rb in rbs if rb.id == "GFR_2017")
    assert any(c.clause_number == "Rule 144(xi)" for c in gfr.clauses)
    assert any(c.clause_number == "Rule 151" for c in gfr.clauses)


def test_rulebook_loader_markdown_parsing():
    """Verifies parsing of Markdown procurement regulations into structured clauses."""
    md_text = """
    ### Rule 144(xi): Land Border Sharing Restriction
    Any bidder from a country which shares a land border with India must be registered with DPIIT.

    ### Clause 4.1: GST Return Compliance
    Active GSTIN status is mandatory for all participating vendors.
    """
    rb = RulebookLoader.parse_markdown_policy(
        text=md_text,
        rulebook_id="TEST_MD_POLICY",
        title="Test Markdown Policy",
        authority="CPCL Scrutiny Wing",
    )
    assert rb.id == "TEST_MD_POLICY"
    assert len(rb.clauses) == 2
    assert rb.clauses[0].clause_number == "Rule 144(xi)"
    assert "DPIIT" in rb.clauses[0].legal_text


def test_policy_vector_store_indexing_and_search():
    """Verifies semantic TF-IDF vector retrieval and keyword boosting."""
    store = PolicyVectorStore()
    clauses = [
        RuleClause(
            id="C1",
            rulebook_id="RB1",
            rulebook_title="General Rules",
            clause_number="Rule 1",
            title="Make in India Local Content Preference",
            category="Make in India",
            legal_text="Class-I local supplier must declare at least 50 percent local content with CA UDIN certification.",
            severity=RuleSeverity.MANDATORY,
            keywords=["make in india", "local content", "udin", "50%"],
        ),
        RuleClause(
            id="C2",
            rulebook_id="RB1",
            rulebook_title="General Rules",
            clause_number="Rule 2",
            title="Blacklisting and Debarment Orders",
            category="Blacklisting",
            legal_text="Bidders listed on CPPP debarment or corruption registry shall be disqualified from tender award.",
            severity=RuleSeverity.DISQUALIFYING,
            keywords=["debarred", "blacklisted", "corruption", "cppp"],
        ),
    ]
    store.add_clauses(clauses)

    # Query 1: Search for Make in India
    res1 = store.search("local content 50 percent requirement", top_k=2)
    assert res1.total_matches >= 1
    assert res1.matches[0].clause.id == "C1"
    assert res1.matches[0].similarity_score > 0.3

    # Query 2: Search for Debarment
    res2 = store.search("debarred vendor blacklist registry", top_k=2)
    assert res2.total_matches >= 1
    assert res2.matches[0].clause.id == "C2"

    # Query 3: Category filter
    res3 = store.search("local content", top_k=2, category_filter="Blacklisting")
    assert res3.total_matches == 0


def test_rule_evaluator_compliant_bidder():
    """Verifies that a fully compliant bidder passes all statutory rulebook clauses."""
    evaluator = RuleEvaluator()
    request = RuleEvaluationRequest(
        gem_bid_number="GEM/2026/B/882211",
        bidder_name="Sundaram Precision Tooling Pvt. Ltd.",
        bid_parameters={
            "land_border_compliance": True,
            "pan_status": "OPERATIVE",
            "is_debarred": False,
            "udyam_valid": True,
            "gst_status": "ACTIVE",
            "gst_filing_regularity_pct": 100.0,
            "maf_valid": True,
            "is_sec_206ab_defaulter": False,
            "local_content_pct": 65.5,
            "ca_udin_valid": True,
            "false_declaration_flag": False,
        },
    )
    res = evaluator.evaluate_bid(request)
    assert res.overall_compliant is True
    assert len(res.disqualifications) == 0
    assert res.passed_clauses_count == res.total_clauses_evaluated


def test_rule_evaluator_debarment_disqualification():
    """Verifies that an active debarment order triggers hard statutory disqualification under Rule 151."""
    evaluator = RuleEvaluator()
    request = RuleEvaluationRequest(
        gem_bid_number="GEM/2026/B/776655",
        bidder_name="Vantage Global Infrastructure Ltd",
        bid_parameters={
            "land_border_compliance": True,
            "pan_status": "OPERATIVE",
            "is_debarred": True,  # Non-compliant / Debarred
            "udyam_valid": True,
            "gst_status": "ACTIVE",
            "gst_filing_regularity_pct": 90.0,
            "maf_valid": True,
            "is_sec_206ab_defaulter": False,
            "local_content_pct": 60.0,
            "ca_udin_valid": True,
            "false_declaration_flag": False,
        },
    )
    res = evaluator.evaluate_bid(request)
    assert res.overall_compliant is False
    assert len(res.disqualifications) >= 1
    debar_violation = next(d for d in res.disqualifications if d.clause_number == "Rule 151")
    assert "Active debarment order" in debar_violation.finding


def test_rule_evaluator_low_local_content_disqualification():
    """Verifies that local content below 50% triggers MII Order violation."""
    evaluator = RuleEvaluator()
    request = RuleEvaluationRequest(
        gem_bid_number="GEM/2026/B/554433",
        bidder_name="Apex Imported Assemblies Ltd",
        bid_parameters={
            "land_border_compliance": True,
            "pan_status": "OPERATIVE",
            "is_debarred": False,
            "udyam_valid": True,
            "gst_status": "ACTIVE",
            "gst_filing_regularity_pct": 95.0,
            "maf_valid": True,
            "is_sec_206ab_defaulter": False,
            "local_content_pct": 32.0,  # Below 50% threshold
            "ca_udin_valid": True,
            "false_declaration_flag": False,
        },
    )
    res = evaluator.evaluate_bid(request)
    assert res.overall_compliant is False
    mii_violation = next(d for d in res.disqualifications if d.clause_id == "MII_PPP_CLASS1")
    assert "below 50.0% Class-I threshold" in mii_violation.finding


@pytest.mark.asyncio
async def test_rulebook_api_endpoints():
    """Verifies rulebook listing, clauses retrieval, vector query, and evaluate endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /api/v1/rulebooks
        r_list = await client.get("/api/v1/rulebooks")
        assert r_list.status_code == 200
        rbs = r_list.json()
        assert len(rbs) >= 3

        # 2. GET /api/v1/rulebooks/GFR_2017/clauses
        r_clauses = await client.get("/api/v1/rulebooks/GFR_2017/clauses")
        assert r_clauses.status_code == 200
        clauses = r_clauses.json()
        assert len(clauses) >= 4

        # 3. POST /api/v1/rulebooks/query (Semantic vector search)
        query_payload = {
            "query": "What are the rules regarding OEM Authorization and Manufacturer Certificates?",
            "top_k": 3,
        }
        r_query = await client.post("/api/v1/rulebooks/query", json=query_payload)
        assert r_query.status_code == 200
        matches = r_query.json()["matches"]
        assert len(matches) > 0
        assert any("OEM" in m["clause"]["title"] or "MAF" in m["clause"]["title"] for m in matches)

        # 4. POST /api/v1/rulebooks/evaluate
        eval_payload = {
            "gem_bid_number": "GEM/2026/B/998877",
            "bidder_name": "Test Engineering Corp",
            "bid_parameters": {
                "land_border_compliance": True,
                "pan_status": "OPERATIVE",
                "is_debarred": False,
                "udyam_valid": True,
                "gst_status": "ACTIVE",
                "gst_filing_regularity_pct": 100.0,
                "maf_valid": True,
                "is_sec_206ab_defaulter": False,
                "local_content_pct": 72.0,
                "ca_udin_valid": True,
                "false_declaration_flag": False,
            },
        }
        r_eval = await client.post("/api/v1/rulebooks/evaluate", json=eval_payload)
        assert r_eval.status_code == 200
        eval_res = r_eval.json()
        assert eval_res["overall_compliant"] is True
        assert eval_res["passed_clauses_count"] >= 8
