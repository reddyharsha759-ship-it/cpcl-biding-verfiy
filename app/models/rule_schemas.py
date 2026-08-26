"""
Pydantic Schemas for Dynamic Rule Book, Policy Clauses, and Statutory Evaluations
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RuleSeverity(str, Enum):
    MANDATORY = "MANDATORY"
    DISQUALIFYING = "DISQUALIFYING"
    ADVISORY = "ADVISORY"


class RuleConditionOperator(str, Enum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    GREATER_THAN_EQUAL = "GREATER_THAN_EQUAL"
    LESS_THAN_EQUAL = "LESS_THAN_EQUAL"
    IN = "IN"
    NOT_IN = "NOT_IN"
    CONTAINS = "CONTAINS"
    REGEX = "REGEX"


class RuleCondition(BaseModel):
    field_path: str = Field(..., description="Target JSON field in bidder/tender payload, e.g. 'bidder.gst_regularity_pct'")
    operator: RuleConditionOperator = Field(..., description="Comparison operator")
    expected_value: Any = Field(..., description="Target statutory threshold or expected value")
    failure_message: str = Field(..., description="Legal rationale if condition is violated")


class RuleClause(BaseModel):
    id: str = Field(..., description="Unique Clause Identifier, e.g. GFR_2017_R144")
    rulebook_id: str = Field(..., description="Parent Rulebook ID, e.g. GFR_2017")
    rulebook_title: str = Field(..., description="Title of parent rulebook")
    clause_number: str = Field(..., description="Official clause/rule number, e.g. Rule 144(xi)")
    title: str = Field(..., description="Short title of the statutory clause")
    category: str = Field(..., description="Statutory Category: GST, MSME, MII, Blacklisting, Finance, Technical")
    legal_text: str = Field(..., description="Official statutory text of the clause")
    severity: RuleSeverity = Field(default=RuleSeverity.MANDATORY, description="Violation severity")
    conditions: List[RuleCondition] = Field(default_factory=list, description="Machine-evaluable conditions")
    keywords: List[str] = Field(default_factory=list, description="Keywords for vector and keyword search")
    effective_date: Optional[str] = Field(default="2017-04-01", description="Effective date of the regulation")


class RuleBook(BaseModel):
    id: str = Field(..., description="Rulebook ID, e.g. GFR_2017")
    title: str = Field(..., description="Official title of the statutory rulebook")
    authority: str = Field(..., description="Issuing Authority (e.g., Ministry of Finance, DPIIT, GeM SPV)")
    version: str = Field(default="1.0", description="Version or Gazette Notification reference")
    category: str = Field(..., description="General category of the regulation")
    summary: str = Field(..., description="High-level overview of the rulebook")
    clauses: List[RuleClause] = Field(default_factory=list, description="Collection of clauses")
    effective_date: str = Field(default="2020-01-01")
    total_clauses: int = Field(default=0)


class PolicySearchQuery(BaseModel):
    query: str = Field(..., description="Natural language procurement question or keyword search")
    top_k: int = Field(default=5, ge=1, le=20, description="Max number of matching policy clauses to return")
    category_filter: Optional[str] = Field(default=None, description="Optional category filter (e.g., MII, MSME, GST)")


class PolicyClauseMatch(BaseModel):
    clause: RuleClause
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Semantic relevance score")
    matched_highlights: List[str] = Field(default_factory=list)


class PolicySearchResponse(BaseModel):
    query: str
    total_matches: int
    matches: List[PolicyClauseMatch]


class EvaluatedClauseResult(BaseModel):
    clause_id: str
    clause_number: str
    clause_title: str
    rulebook: str
    category: str
    is_compliant: bool
    severity: RuleSeverity
    evaluated_field: str
    actual_value: Any
    expected_value: Any
    finding: str


class RuleEvaluationRequest(BaseModel):
    tender_id: Optional[str] = None
    gem_bid_number: Optional[str] = "GEM/2026/B/998877"
    bidder_name: str
    bid_parameters: Dict[str, Any] = Field(..., description="Extracted & verified bidder parameters")


class RuleEvaluationResponse(BaseModel):
    gem_bid_number: str
    bidder_name: str
    overall_compliant: bool
    total_clauses_evaluated: int
    passed_clauses_count: int
    violated_clauses_count: int
    disqualifications: List[EvaluatedClauseResult] = Field(default_factory=list)
    advisories: List[EvaluatedClauseResult] = Field(default_factory=list)
    evaluation_timestamp: str
