import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.domain import (
    Bidder,
    ComplianceAuditLog,
    JobStatus,
    PillarType,
    RiskTier,
    Tender,
    VerificationJob,
)
from app.services.compliance_engine import ComplianceEngine
from app.services.integrations.base import BaseStatutoryAdapter
from app.services.scoring_service import ScoringService


async def evaluate_compliance_job_async(
    job_id: uuid.UUID,
    db: AsyncSession,
    document_paths: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Executes the full multi-pillar compliance verification workflow for a VerificationJob asynchronously.
    Updates the job status, generates immutable ComplianceAuditLogs, and computes the BCI score.
    """
    # 1. Fetch Job, Tender, and Bidder
    stmt = (
        select(VerificationJob)
        .options(
            selectinload(VerificationJob.tender),
            selectinload(VerificationJob.bidder),
            selectinload(VerificationJob.audit_logs),
        )
        .where(VerificationJob.id == job_id)
    )
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise ValueError(f"VerificationJob {job_id} not found in database.")

    # 2. Transition status to PROCESSING
    job.status = JobStatus.PROCESSING
    await db.flush()

    doc_paths = document_paths or {}
    maf_path = doc_paths.get("maf")
    mii_path = doc_paths.get("mii")
    financial_path = doc_paths.get("financial")

    engine = ComplianceEngine()

    try:
        # 3. Execute multi-pillar verification
        eval_result = await engine.evaluate_bidder_tender_compliance(
            bidder_pan=job.bidder.pan,
            bidder_gstin=job.bidder.gstin,
            bidder_legal_name=job.bidder.legal_name,
            gem_bid_number=job.tender.gem_bid_number,
            bidder_udyam_reg_no=job.bidder.udyam_reg_no,
            required_nic_codes=job.tender.required_nic_codes,
            min_turnover_inr=job.tender.min_turnover_inr or 0.0,
            maf_doc_source=maf_path,
            mii_doc_source=mii_path,
            financial_doc_source=financial_path,
        )

        # 4. Calculate BCI Score and Risk Tier
        scoring_result = ScoringService.calculate_bci(
            evaluation_data=eval_result,
            min_turnover_inr=job.tender.min_turnover_inr or 0.0,
        )

        # 5. Persist ComplianceAuditLog records for each pillar
        statutory = eval_result["statutory_pillars"]
        docs = eval_result["documents"]

        pillar_mapping = [
            (PillarType.GST, statutory.get("GST")),
            (PillarType.PAN, statutory.get("PAN")),
            (PillarType.DEBARMENT, statutory.get("DEBARMENT")),
            (PillarType.UDYAM, statutory.get("UDYAM")),
            (PillarType.OEM, docs.get("MAF")),
            (PillarType.MII, docs.get("MII")),
        ]

        for pillar_enum, pillar_data in pillar_mapping:
            if pillar_data is not None:
                raw_payload = pillar_data.get("raw_payload", pillar_data)
                payload_sha256 = pillar_data.get(
                    "payload_sha256", BaseStatutoryAdapter.compute_payload_sha256(raw_payload)
                )
                is_compliant = bool(pillar_data.get("is_compliant", False))
                findings = pillar_data.get("findings", pillar_data)

                audit_log = ComplianceAuditLog(
                    job_id=job.id,
                    pillar=pillar_enum,
                    raw_payload=raw_payload,
                    payload_sha256=payload_sha256,
                    is_compliant=is_compliant,
                    findings=findings,
                    timestamp=datetime.now(timezone.utc),
                )
                job.audit_logs.append(audit_log)
                db.add(audit_log)

        # 6. Update VerificationJob outcome
        job.status = JobStatus.COMPLETED
        job.bci_score = scoring_result["bci_score"]
        job.risk_tier = scoring_result["risk_tier"]
        job.completed_at = datetime.now(timezone.utc)

        await db.commit()

        return {
            "job_id": str(job.id),
            "status": job.status.value,
            "bci_score": job.bci_score,
            "risk_tier": job.risk_tier.value,
            "scoring_result": scoring_result,
            "evaluation_result": eval_result,
        }

    except Exception as exc:
        job.status = JobStatus.FAILED
        job.completed_at = datetime.now(timezone.utc)
        await db.commit()
        raise exc


@celery_app.task(name="app.workers.tasks.process_bid_compliance_evaluation", bind=True)
def process_bid_compliance_evaluation(self, job_id_str: str, document_paths: Optional[Dict[str, str]] = None):
    """
    Celery worker task for executing compliance evaluations in distributed worker processes.
    """
    job_id = uuid.UUID(job_id_str)

    async def _runner():
        async with AsyncSessionLocal() as session:
            return await evaluate_compliance_job_async(
                job_id=job_id,
                db=session,
                document_paths=document_paths,
            )

    return asyncio.run(_runner())
