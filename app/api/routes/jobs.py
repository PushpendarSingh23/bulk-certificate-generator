import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import logger
from app.db.database import get_db
from app.db.models import CertificateJob, CertificateRecipient, JobStatus, RecipientStatus
from app.schemas.job import (
    JobCreate,
    JobCreateResponse,
    JobDetailResponse,
    JobSummaryResponse,
    PaginatedJobResponse,
    PaginatedRecipientResponse
)
from app.schemas.recipient import RecipientResponse
from app.services.job_processor import process_certificate_job

router = APIRouter(prefix="/certificate-jobs", tags=["Certificate Jobs"])


@router.post(
    "",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create bulk certificate generation job"
)
def create_certificate_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Accepts a bulk certificate generation request.
    Validates the entire batch, persists the job and recipients in the database,
    and enqueues background processing.
    """
    job_id = str(uuid.uuid4())
    total_recipients = len(payload.recipients)

    # 1. Create Job record
    new_job = CertificateJob(
        id=job_id,
        event_name=payload.event_name,
        organization_name=payload.organization_name,
        issue_date=payload.issue_date,
        certificate_title=payload.certificate_title or "Certificate of Completion",
        status=JobStatus.PENDING,
        total_count=total_recipients,
        success_count=0,
        failure_count=0
    )
    db.add(new_job)

    # 2. Create Recipient records
    for item in payload.recipients:
        rec = CertificateRecipient(
            id=str(uuid.uuid4()),
            job_id=job_id,
            name=item.name,
            email=str(item.email),
            status=RecipientStatus.PENDING
        )
        db.add(rec)

    db.commit()
    logger.info("Persisted job %s with %d recipients", job_id, total_recipients)

    # 3. Queue background execution
    background_tasks.add_task(process_certificate_job, job_id)

    status_url = f"{settings.API_V1_STR}/certificate-jobs/{job_id}"
    return JobCreateResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        status_url=status_url,
        total_count=total_recipients,
        message="Certificate generation job accepted and queued for background processing."
    )


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Get certificate job status and progress"
)
def get_certificate_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Fetches job details, including status, progress counts, and recipient-level results.
    """
    job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate job with ID '{job_id}' was not found."
        )
    return JobDetailResponse.from_orm_job(job)


@router.get(
    "",
    response_model=PaginatedJobResponse,
    summary="List certificate generation jobs"
)
def list_certificate_jobs(
    status_filter: Optional[JobStatus] = Query(None, alias="status", description="Filter by job status"),
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Lists recent certificate jobs with pagination and optional status filter.
    """
    query = db.query(CertificateJob)
    if status_filter:
        query = query.filter(CertificateJob.status == status_filter)

    total = query.count()
    jobs = query.order_by(CertificateJob.created_at.desc()).offset(offset).limit(limit).all()

    return PaginatedJobResponse(
        items=[JobSummaryResponse.from_orm_job(j) for j in jobs],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{job_id}/recipients",
    response_model=PaginatedRecipientResponse,
    summary="Get recipient-level generation results for a job"
)
def get_job_recipients(
    job_id: str,
    status_filter: Optional[RecipientStatus] = Query(None, alias="status", description="Filter by recipient status"),
    limit: int = Query(50, ge=1, le=200, description="Number of recipients to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Retrieves individual recipient results for a specific job with pagination.
    """
    job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate job with ID '{job_id}' was not found."
        )

    query = db.query(CertificateRecipient).filter(CertificateRecipient.job_id == job_id)
    if status_filter:
        query = query.filter(CertificateRecipient.status == status_filter)

    total = query.count()
    recipients = query.order_by(CertificateRecipient.created_at.asc()).offset(offset).limit(limit).all()

    return PaginatedRecipientResponse(
        items=[RecipientResponse.model_validate(r) for r in recipients],
        total=total,
        limit=limit,
        offset=offset
    )
