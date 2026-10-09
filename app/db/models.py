import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class RecipientStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CertificateJob(Base):
    __tablename__ = "certificate_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    event_name = Column(String(255), nullable=False)
    organization_name = Column(String(255), nullable=False)
    issue_date = Column(Date, nullable=False)
    certificate_title = Column(String(255), nullable=False, default="Certificate of Completion")
    status = Column(SQLEnum(JobStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=JobStatus.PENDING, index=True)
    total_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    failure_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    recipients = relationship(
        "CertificateRecipient",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="CertificateRecipient.created_at"
    )

    @property
    def pending_count(self) -> int:
        return max(0, self.total_count - (self.success_count + self.failure_count))

    @property
    def progress_percentage(self) -> float:
        if self.total_count == 0:
            return 100.0 if self.status in (JobStatus.COMPLETED, JobStatus.COMPLETED_WITH_ERRORS, JobStatus.FAILED) else 0.0
        processed = self.success_count + self.failure_count
        return round((processed / self.total_count) * 100.0, 2)


class CertificateRecipient(Base):
    __tablename__ = "certificate_recipients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    job_id = Column(String(36), ForeignKey("certificate_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    status = Column(SQLEnum(RecipientStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=RecipientStatus.PENDING, index=True)
    certificate_id = Column(String(64), unique=True, nullable=True, index=True)
    certificate_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=True)

    job = relationship("CertificateJob", back_populates="recipients")
