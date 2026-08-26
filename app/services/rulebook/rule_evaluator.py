"""
Dynamic Rule Evaluator Engine
Cross-evaluates bidder credentials and tender specifications against statutory rulebook clauses.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.models.rule_schemas import (
    EvaluatedClauseResult,
    RuleBook,
    RuleClause,
    RuleCondition,
    RuleConditionOperator,
    RuleEvaluationRequest,
    RuleEvaluationResponse,
    RuleSeverity,
)
from app.services.rulebook.loader import RulebookLoader


def get_nested_val(data: dict, field_path: str) -> Any:
    """Retrieves a nested value from a dictionary using dot notation."""
    keys = field_path.split(".")
    curr: Any = data
    for k in keys:
        if isinstance(curr, dict) and k in curr:
            curr = curr[k]
        else:
            return None
    return curr


class RuleEvaluator:
    """Evaluates arbitrary bidder parameters against statutory rule clauses."""

    def __init__(self, rulebooks: Optional[List[RuleBook]] = None) -> None:
        if rulebooks is not None:
            self.rulebooks = rulebooks
        else:
            self.rulebooks = RulebookLoader.load_default_rulebooks()

    def evaluate_condition(self, condition: RuleCondition, data: dict) -> tuple[bool, Any]:
        """Evaluates a single condition against the provided data dictionary."""
        actual = get_nested_val(data, condition.field_path)
        expected = condition.expected_value
        op = condition.operator

        if actual is None:
            # Field missing from submission
            return False, "MISSING_FIELD"

        try:
            if op == RuleConditionOperator.EQUALS:
                return bool(actual == expected), actual
            elif op == RuleConditionOperator.NOT_EQUALS:
                return bool(actual != expected), actual
            elif op == RuleConditionOperator.GREATER_THAN_EQUAL:
                return float(actual) >= float(expected), actual
            elif op == RuleConditionOperator.LESS_THAN_EQUAL:
                return float(actual) <= float(expected), actual
            elif op == RuleConditionOperator.IN:
                return actual in expected, actual
            elif op == RuleConditionOperator.NOT_IN:
                return actual not in expected, actual
            elif op == RuleConditionOperator.CONTAINS:
                return str(expected).lower() in str(actual).lower(), actual
            elif op == RuleConditionOperator.REGEX:
                return bool(re.search(str(expected), str(actual))), actual
        except Exception:
            return False, actual

        return False, actual

    def evaluate_bid(self, request: RuleEvaluationRequest) -> RuleEvaluationResponse:
        """
        Executes a complete statutory compliance audit against all loaded rulebook clauses.
        """
        data = request.bid_parameters
        disqualifications: List[EvaluatedClauseResult] = []
        advisories: List[EvaluatedClauseResult] = []
        passed_count = 0
        total_clauses = 0

        for rb in self.rulebooks:
            for clause in rb.clauses:
                total_clauses += 1
                clause_passed = True
                failed_condition: Optional[RuleCondition] = None
                actual_val: Any = None

                for cond in clause.conditions:
                    passed, val = self.evaluate_condition(cond, data)
                    if not passed:
                        clause_passed = False
                        failed_condition = cond
                        actual_val = val
                        break

                if clause_passed:
                    passed_count += 1
                else:
                    result = EvaluatedClauseResult(
                        clause_id=clause.id,
                        clause_number=clause.clause_number,
                        clause_title=clause.title,
                        rulebook=clause.rulebook_title,
                        category=clause.category,
                        is_compliant=False,
                        severity=clause.severity,
                        evaluated_field=failed_condition.field_path if failed_condition else "unknown",
                        actual_value=actual_val,
                        expected_value=failed_condition.expected_value if failed_condition else None,
                        finding=failed_condition.failure_message if failed_condition else "Clause condition violated.",
                    )

                    if clause.severity == RuleSeverity.DISQUALIFYING or clause.severity == RuleSeverity.MANDATORY:
                        disqualifications.append(result)
                    else:
                        advisories.append(result)

        overall_compliant = len(disqualifications) == 0

        return RuleEvaluationResponse(
            gem_bid_number=request.gem_bid_number or "GEM/2026/B/998877",
            bidder_name=request.bidder_name,
            overall_compliant=overall_compliant,
            total_clauses_evaluated=total_clauses,
            passed_clauses_count=passed_count,
            violated_clauses_count=len(disqualifications) + len(advisories),
            disqualifications=disqualifications,
            advisories=advisories,
            evaluation_timestamp=datetime.now(timezone.utc).isoformat(),
        )
