from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.core.config import settings
from app.db.models import JobStatus
from app.schemas.recipient import RecipientCreate, RecipientResponse


class JobCreate(BaseModel):
    event_name: str = Field(..., min_length=1, max_length=200, description="Name of the course, workshop, or event")
    organization_name: str = Field(..., min_length=1, max_length=200, description="Issuing organization name")
    issue_date: date = Field(..., description="Date of certificate issuance (YYYY-MM-DD)")
    certificate_title: Optional[str] = Field(
        default="Certificate of Completion",
        min_length=1,
        max_length=200,
        description="Title or achievement text displayed on the certificate"
    )
    recipients: List[RecipientCreate] = Field(..., description="List of recipients to generate certificates for")

    @field_validator("event_name", "organization_name")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty or whitespace only")
        return v

    @field_validator("certificate_title")
    @classmethod
    def validate_certificate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return "Certificate of Completion"
        return v

    @field_validator("recipients")
    @classmethod
    def validate_recipients_batch(cls, v: List[RecipientCreate]) -> List[RecipientCreate]:
        if not v:
            raise ValueError("Recipient list must not be empty. At least one recipient is required.")
        if len(v) > settings.MAX_BATCH_SIZE:
            raise ValueError(
                f"Batch size exceeds maximum allowed limit of {settings.MAX_BATCH_SIZE} recipients per job. Received {len(v)}."
            )
        return v


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus
    status_url: str
    total_count: int
    message: str


class JobSummaryResponse(BaseModel):
    job_id: str
    event_name: str
    organization_name: str
    issue_date: date
    certificate_title: str
    status: JobStatus
    total_count: int
    success_count: int
    failure_count: int
    pending_count: int
    progress_percentage: float
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_job(cls, job):
        return cls(
            job_id=job.id,
            event_name=job.event_name,
            organization_name=job.organization_name,
            issue_date=job.issue_date,
            certificate_title=job.certificate_title or "Certificate of Completion",
            status=job.status,
            total_count=job.total_count,
            success_count=job.success_count,
            failure_count=job.failure_count,
            pending_count=job.pending_count,
            progress_percentage=job.progress_percentage,
            created_at=job.created_at,
            completed_at=job.completed_at
        )


class JobDetailResponse(JobSummaryResponse):
    recipients: List[RecipientResponse] = []

    @classmethod
    def from_orm_job(cls, job):
        return cls(
            job_id=job.id,
            event_name=job.event_name,
            organization_name=job.organization_name,
            issue_date=job.issue_date,
            certificate_title=job.certificate_title or "Certificate of Completion",
            status=job.status,
            total_count=job.total_count,
            success_count=job.success_count,
            failure_count=job.failure_count,
            pending_count=job.pending_count,
            progress_percentage=job.progress_percentage,
            created_at=job.created_at,
            completed_at=job.completed_at,
            recipients=[RecipientResponse.model_validate(r) for r in job.recipients]
        )


class PaginatedJobResponse(BaseModel):
    items: List[JobSummaryResponse]
    total: int
    limit: int
    offset: int


class PaginatedRecipientResponse(BaseModel):
    items: List[RecipientResponse]
    total: int
    limit: int
    offset: int
