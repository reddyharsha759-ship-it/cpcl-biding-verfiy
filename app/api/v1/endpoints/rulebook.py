"""
API Endpoints for Dynamic Statutory Rule Book & Regulatory Knowledge Base
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, HTTPException, Query, status

from app.models.rule_schemas import (
    PolicySearchQuery,
    PolicySearchResponse,
    RuleBook,
    RuleClause,
    RuleEvaluationRequest,
    RuleEvaluationResponse,
)
from app.services.rulebook.loader import RulebookLoader
from app.services.rulebook.rule_evaluator import RuleEvaluator
from app.services.rulebook.vector_store import policy_vector_store

router = APIRouter(prefix="/rulebooks", tags=["Rulebook & Policy Knowledge Base"])

# In-memory registry of active rulebooks
ACTIVE_RULEBOOKS: Dict[str, RuleBook] = {}


def initialize_rulebook_engine() -> None:
    """Bootstraps default statutory rulebooks into the registry and vector store."""
    default_rbs = RulebookLoader.load_default_rulebooks()
    for rb in default_rbs:
        ACTIVE_RULEBOOKS[rb.id] = rb
        policy_vector_store.add_clauses(rb.clauses)


# Auto-initialize on module load
initialize_rulebook_engine()


@router.get("", response_model=List[RuleBook])
async def list_rulebooks(
    category: Optional[str] = Query(None, description="Filter rulebooks by statutory category")
) -> List[RuleBook]:
    """
    Returns all registered statutory rulebooks (GFR 2017, GeM GTC, Make-in-India Order, etc.).
    """
    rbs = list(ACTIVE_RULEBOOKS.values())
    if category:
        rbs = [rb for rb in rbs if category.lower() in rb.category.lower()]
    return rbs


@router.get("/{rulebook_id}/clauses", response_model=List[RuleClause])
async def get_rulebook_clauses(rulebook_id: str) -> List[RuleClause]:
    """
    Retrieves all individual legal clauses and rule conditions under a specific rulebook.
    """
    if rulebook_id not in ACTIVE_RULEBOOKS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rulebook '{rulebook_id}' not found in regulatory registry.",
        )
    return ACTIVE_RULEBOOKS[rulebook_id].clauses


@router.post("/upload", response_model=RuleBook, status_code=status.HTTP_201_CREATED)
async def upload_custom_rulebook(
    payload: Dict[str, Any] = Body(..., description="JSON or Markdown rulebook specification")
) -> RuleBook:
    """
    Ingests a new statutory rulebook into the compliance engine and vector index.
    Supports structured JSON format or markdown policy text.
    """
    try:
        if "markdown" in payload:
            rb = RulebookLoader.parse_markdown_policy(
                text=payload["markdown"],
                rulebook_id=payload.get("id", "CUSTOM_POLICY"),
                title=payload.get("title", "Custom Procurement Policy"),
                authority=payload.get("authority", "CPCL Directorate"),
            )
        else:
            rb = RulebookLoader.parse_dict(payload)

        ACTIVE_RULEBOOKS[rb.id] = rb
        policy_vector_store.add_clauses(rb.clauses)
        return rb
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to ingest rulebook: {str(e)}",
        )


@router.post("/query", response_model=PolicySearchResponse)
async def query_policy_knowledge_base(query: PolicySearchQuery) -> PolicySearchResponse:
    """
    Executes semantic vector search and keyword retrieval across all statutory rulebook clauses.
    Used for automated citation and compliance cross-referencing.
    """
    return policy_vector_store.search(
        query=query.query,
        top_k=query.top_k,
        category_filter=query.category_filter,
    )


@router.post("/evaluate", response_model=RuleEvaluationResponse)
async def evaluate_bid_against_rulebook(request: RuleEvaluationRequest) -> RuleEvaluationResponse:
    """
    Cross-evaluates verified bidder credentials and tender specifications
    against all machine-readable statutory rulebook conditions.
    """
    evaluator = RuleEvaluator(rulebooks=list(ACTIVE_RULEBOOKS.values()))
    return evaluator.evaluate_bid(request)
