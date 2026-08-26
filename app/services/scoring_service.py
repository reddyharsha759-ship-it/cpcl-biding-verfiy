from typing import Any, Dict, List, Optional, Tuple

from app.models.domain import RiskTier


class ScoringService:
    """
    Computes the weighted Bidder Compliance Index (BCI 0-100),
    detects critical statutory hard failures, and assigns risk tiers.
    """

    WEIGHT_STATUTORY = 40.0
    WEIGHT_REGULARITY = 20.0
    WEIGHT_DOCUMENTS = 25.0
    WEIGHT_CONSISTENCY = 15.0

    @classmethod
    def calculate_bci(
        cls,
        evaluation_data: Dict[str, Any],
        min_turnover_inr: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Calculates the weighted Bidder Compliance Index and classifies the risk tier.
        """
        hard_failures: List[str] = []
        warnings: List[str] = []

        statutory = evaluation_data.get("statutory_pillars", {})
        documents = evaluation_data.get("documents", {})

        gst = statutory.get("GST")
        pan = statutory.get("PAN")
        debarment = statutory.get("DEBARMENT")
        udyam = statutory.get("UDYAM")

        maf = documents.get("MAF")
        mii = documents.get("MII")
        financial = documents.get("FINANCIAL")

        # -------------------------------------------------------------
        # 1. HARD FAILURE CHECKS
        # -------------------------------------------------------------
        # A. Debarment
        if debarment and not debarment.get("is_compliant", True):
            hard_failures.extend(debarment["findings"].get("disqualifiers", ["Active Debarment Order Found"]))

        # B. Inactive GSTIN
        if gst:
            if not gst.get("findings", {}).get("is_active", False):
                hard_failures.append(f"GSTIN is not active ({gst['findings'].get('status')})")
            if gst.get("findings", {}).get("gstr3b_regularity_percentage", 100.0) < 50.0:
                hard_failures.append("Severe GSTR-3B tax return default (< 50% filings)")

        # C. Inoperative PAN / Section 206AB Non-Filer
        if pan:
            if not pan.get("findings", {}).get("is_active", False):
                hard_failures.append(f"PAN is inoperative or inactive ({pan['findings'].get('status')})")
            if pan.get("findings", {}).get("sec_206ab_specified_person", False):
                hard_failures.append("Section 206AB Non-Filer Defaulter (Higher TDS Applicable)")

        # D. PAN-GSTIN Consistency
        if not evaluation_data.get("pan_gstin_valid", True):
            hard_failures.append(evaluation_data.get("pan_gstin_err", "PAN-GSTIN consistency violation"))

        # E. OEM MAF Hard Failures
        if maf:
            if not maf.get("tender_matched", True):
                hard_failures.append("MAF tender bid reference number does not match current GeM bid")
            if maf.get("is_expired", False):
                hard_failures.append(f"MAF authorization is expired ({maf.get('validity_date')})")
            if not maf.get("is_compliant", False) and not hard_failures:
                hard_failures.extend(maf.get("disqualifiers", []))

        # F. Financial Certificate
        if financial:
            if financial.get("net_worth_inr") is not None and financial.get("net_worth_inr") <= 0.0:
                hard_failures.append("Negative or Zero Net Worth reported in CA Financial Certificate")
            if min_turnover_inr > 0.0 and financial.get("avg_turnover_inr", 0.0) < min_turnover_inr:
                hard_failures.append(
                    f"Average turnover (₹{financial.get('avg_turnover_inr', 0):,.2f}) below tender minimum (₹{min_turnover_inr:,.2f})"
                )

        # -------------------------------------------------------------
        # 2. WEIGHTED SCORING ACCUMULATION
        # -------------------------------------------------------------
        score_statutory = 0.0
        score_regularity = 0.0
        score_documents = 0.0
        score_consistency = 0.0

        # Component 1: Statutory Clearance (40 pts)
        # GST Active: 15 pts
        if gst and gst.get("findings", {}).get("is_active", False):
            score_statutory += 15.0
        # PAN Active: 15 pts
        if pan and pan.get("findings", {}).get("is_active", False):
            score_statutory += 15.0
        # Udyam Active/Valid: 10 pts
        if udyam:
            if udyam.get("is_compliant", False):
                score_statutory += 10.0
            elif udyam.get("findings", {}).get("is_active", False):
                score_statutory += 5.0
                warnings.extend(udyam["findings"].get("warnings", []))
        else:
            score_statutory += 10.0  # Full points if Udyam not declared/required

        # Component 2: Filing Regularity (20 pts)
        # GSTR-3B regularity (10 pts)
        if gst:
            gstr_reg = gst.get("findings", {}).get("gstr3b_regularity_percentage", 100.0)
            score_regularity += (gstr_reg / 100.0) * 10.0
            if gstr_reg < 100.0:
                warnings.append(f"GSTR-3B filing regularity is {gstr_reg:.1f}%")
        else:
            score_regularity += 10.0

        # Income Tax Section 206AB compliance (10 pts)
        if pan and not pan.get("findings", {}).get("sec_206ab_specified_person", False):
            score_regularity += 10.0

        # Component 3: Document & OEM Validity (25 pts)
        # MAF validity (15 pts)
        if maf:
            if maf.get("is_compliant", False):
                score_documents += 15.0
            else:
                warnings.extend(maf.get("warnings", []))
        else:
            score_documents += 15.0  # Not required for non-OEM tenders

        # Make in India (10 pts)
        if mii:
            if mii.get("supplier_class") == "Class-I Local Supplier":
                score_documents += 10.0
            elif mii.get("supplier_class") == "Class-II Local Supplier":
                score_documents += 5.0
                warnings.append("Class-II Local Supplier (Local Content between 20% and 49%)")
            else:
                score_documents += 0.0
                warnings.append("Non-Local Supplier (< 20% Local Content)")
        else:
            score_documents += 10.0

        # Component 4: Entity Consistency & Turnover (15 pts)
        # Name Consistency & PAN-GSTIN (10 pts)
        name_score = evaluation_data.get("name_match_score", 100.0)
        score_consistency += (name_score / 100.0) * 10.0
        if name_score < 90.0:
            warnings.append(f"Fuzzy name match score is {name_score:.1f}% across records")

        # Turnover Requirement (5 pts)
        if financial:
            if min_turnover_inr == 0.0 or financial.get("avg_turnover_inr", 0.0) >= min_turnover_inr:
                score_consistency += 5.0
            else:
                warnings.append("Turnover below tender threshold")
        else:
            score_consistency += 5.0

        raw_bci = score_statutory + score_regularity + score_documents + score_consistency
        raw_bci = min(100.0, max(0.0, raw_bci))

        # Apply Hard Failure Override
        if hard_failures:
            final_bci = 0.0
            risk_tier = RiskTier.RED
            recommendation = "DISQUALIFIED: Hard statutory or document failure detected"
        else:
            final_bci = round(raw_bci, 2)
            if final_bci >= 85.0:
                risk_tier = RiskTier.GREEN
                recommendation = "TECHNICALLY COMPLIANT: Bidder meets all statutory and tender compliance criteria"
            elif final_bci >= 60.0:
                risk_tier = RiskTier.AMBER
                recommendation = "SEEK CLARIFICATION: Minor discrepancies or marginal filing regularity identified"
            else:
                risk_tier = RiskTier.RED
                recommendation = "DISQUALIFIED: Score below mandatory 60-point threshold"

        return {
            "bci_score": final_bci,
            "risk_tier": risk_tier,
            "recommendation": recommendation,
            "has_hard_failures": bool(hard_failures),
            "hard_failures": hard_failures,
            "warnings": warnings,
            "score_breakdown": {
                "statutory_clearance": round(score_statutory, 2),
                "filing_regularity": round(score_regularity, 2),
                "document_oem_validity": round(score_documents, 2),
                "entity_consistency_turnover": round(score_consistency, 2),
            },
        }
