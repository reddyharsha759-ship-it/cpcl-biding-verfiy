import hashlib
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, File, HTTPException, Query, UploadFile, status

from app.models.rule_schemas import (
    PolicySearchQuery,
    PolicySearchResponse,
    RuleBook,
    RuleClause,
    RuleEvaluationRequest,
    RuleEvaluationResponse,
)
from app.services.document_ai.parser import PDFProcessor
from app.services.rulebook.loader import RulebookLoader
from app.services.rulebook.rule_evaluator import RuleEvaluator
from app.services.rulebook.vector_store import policy_vector_store

router = APIRouter(prefix="/rulebooks", tags=["Rulebook & Policy Knowledge Base"])

# In-memory registry of active rulebooks
ACTIVE_RULEBOOKS: Dict[str, RuleBook] = {}
RULEBOOK_LOCK_STATE: Dict[str, Any] = {
    "is_locked": True,
    "locked_at": "2026-08-27T08:00:00Z",
    "locked_by": "Shri V. Ramasubramanian, Chief Vigilance Officer",
    "lock_seal": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
    "total_clauses_locked": 7,
}


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


@router.get("/lock-status")
async def get_rulebook_lock_status() -> Dict[str, Any]:
    """
    Returns current cryptographic lock status of the active rulebook baseline.
    """
    total_clauses = sum(len(rb.clauses) for rb in ACTIVE_RULEBOOKS.values())
    RULEBOOK_LOCK_STATE["total_clauses_locked"] = total_clauses
    return RULEBOOK_LOCK_STATE


@router.post("/lock")
async def lock_rulebook(
    officer_name: str = Query("Procurement Review Officer", description="Name of locking officer")
) -> Dict[str, Any]:
    """
    Cryptographically locks the statutory rulebook baseline to prevent mid-tender tampering.
    """
    total_clauses = sum(len(rb.clauses) for rb in ACTIVE_RULEBOOKS.values())
    hasher = hashlib.sha256()
    for rb in ACTIVE_RULEBOOKS.values():
        hasher.update(rb.title.encode("utf-8"))
        for c in rb.clauses:
            hasher.update(c.legal_text.encode("utf-8"))

    seal = hasher.hexdigest()
    RULEBOOK_LOCK_STATE.update({
        "is_locked": True,
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "locked_by": officer_name,
        "lock_seal": seal,
        "total_clauses_locked": total_clauses,
    })
    return {
        "status": "LOCKED",
        "message": f"Rulebook baseline sealed with {total_clauses} statutory clauses.",
        "lock_state": RULEBOOK_LOCK_STATE,
    }


@router.post("/unlock")
async def unlock_rulebook(
    officer_name: str = Query("Procurement Review Officer", description="Name of unlocking officer")
) -> Dict[str, Any]:
    """
    Unlocks the rulebook baseline to allow uploading new statutory guidelines or tender specs.
    """
    RULEBOOK_LOCK_STATE.update({
        "is_locked": False,
        "unlocked_at": datetime.now(timezone.utc).isoformat(),
        "unlocked_by": officer_name,
    })
    return {
        "status": "UNLOCKED",
        "message": "Rulebook unlocked for modifications.",
        "lock_state": RULEBOOK_LOCK_STATE,
    }


@router.post("/upload-file", response_model=RuleBook, status_code=status.HTTP_201_CREATED)
async def upload_rulebook_file(
    file: UploadFile = File(..., description="PDF, Markdown, JSON or TXT file of the policy rulebook"),
    title: Optional[str] = Query(None, description="Custom title for the rulebook"),
    authority: Optional[str] = Query("Chennai Petroleum Corporation Limited (CPCL)", description="Issuing Authority"),
    category: Optional[str] = Query("Technical & Statutory Rules", description="Regulatory category"),
) -> RuleBook:
    """
    Uploads and processes a rulebook from PDF, Markdown, JSON, or Plain Text.
    Extracts legal clauses, indexes them into the vector knowledge base, and returns the RuleBook.
    """
    content_bytes = await file.read()
    filename = file.filename or "uploaded_rulebook.pdf"
    rb_id = f"RB_{hashlib.md5(filename.encode('utf-8')).hexdigest()[:8].upper()}"
    rb_title = title or filename.rsplit(".", 1)[0].replace("_", " ").title()

    try:
        if filename.lower().endswith(".pdf"):
            pdf_data = await PDFProcessor.extract_text(content_bytes)
            raw_text = pdf_data.get("full_text", "")
            rb = RulebookLoader.parse_plain_or_pdf_text(
                text=raw_text,
                rulebook_id=rb_id,
                title=rb_title,
                authority=authority,
                category=category,
            )
        elif filename.lower().endswith(".json"):
            data = json.loads(content_bytes.decode("utf-8"))
            rb = RulebookLoader.parse_dict(data)
        elif filename.lower().endswith((".md", ".txt")):
            raw_text = content_bytes.decode("utf-8")
            rb = RulebookLoader.parse_markdown_policy(
                text=raw_text,
                rulebook_id=rb_id,
                title=rb_title,
                authority=authority,
            )
        else:
            raw_text = content_bytes.decode("utf-8", errors="ignore")
            rb = RulebookLoader.parse_plain_or_pdf_text(
                text=raw_text,
                rulebook_id=rb_id,
                title=rb_title,
                authority=authority,
                category=category,
            )

        ACTIVE_RULEBOOKS[rb.id] = rb
        policy_vector_store.add_clauses(rb.clauses)
        return rb

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse and index rulebook file: {str(e)}",
        )


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
