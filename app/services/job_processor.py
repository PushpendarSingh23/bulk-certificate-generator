import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.db.database import SessionLocal
from app.db.models import CertificateJob, CertificateRecipient, JobStatus, RecipientStatus
from app.services.certificate_generator import CertificateGenerator
from app.utils.file_storage import get_certificate_path, remove_file_safely


def utcnow():
    return datetime.now(timezone.utc)


def process_certificate_job(job_id: str, db_session_factory=SessionLocal) -> None:
    """
    Background worker task to process all recipients for a given certificate job.
    Processes each recipient independently for failure isolation.
    """
    db: Session = db_session_factory()
    try:
        job: Optional[CertificateJob] = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
        if not job:
            logger.error("Job %s not found for processing", job_id)
            return

        # 1. Mark Job as Processing
        job.status = JobStatus.PROCESSING
        db.commit()
        logger.info("Started processing job %s with %d recipients", job_id, job.total_count)

        # 2. Iterate through all recipients
        recipients = db.query(CertificateRecipient).filter(CertificateRecipient.job_id == job_id).all()
        
        for recipient in recipients:
            # Skip already completed ones (for idempotency/retry safety)
            if recipient.status == RecipientStatus.COMPLETED:
                continue

            cert_id = f"CERT-{uuid.uuid4().hex[:12].upper()}"
            pdf_path = None

            try:
                recipient.status = RecipientStatus.PROCESSING
                db.commit()

                pdf_path = get_certificate_path(job_id, cert_id)

                # Generate the PDF certificate
                CertificateGenerator.generate(
                    output_path=pdf_path,
                    recipient_name=recipient.name,
                    event_name=job.event_name,
                    organization_name=job.organization_name,
                    issue_date=job.issue_date,
                    certificate_id=cert_id,
                    certificate_title=job.certificate_title or "Certificate of Completion"
                )

                # Verify file was written and is non-empty
                if not pdf_path.exists() or pdf_path.stat().st_size == 0:
                    raise IOError("Generated certificate file is missing or empty.")

                recipient.status = RecipientStatus.COMPLETED
                recipient.certificate_id = cert_id
                recipient.certificate_path = str(pdf_path)
                recipient.error_message = None
                recipient.generated_at = utcnow()

                job.success_count += 1
                db.commit()

            except Exception as exc:
                logger.exception("Failed to generate certificate for recipient %s in job %s: %s", recipient.id, job_id, exc)
                # Cleanup incomplete file if present
                if pdf_path:
                    remove_file_safely(pdf_path)

                recipient.status = RecipientStatus.FAILED
                recipient.error_message = str(exc) or "Unknown certificate generation error"
                recipient.generated_at = utcnow()

                job.failure_count += 1
                db.commit()

        # 3. Final status calculation
        # Refresh counts from actual recipient states to ensure 100% accuracy
        success_c = db.query(CertificateRecipient).filter(
            CertificateRecipient.job_id == job_id,
            CertificateRecipient.status == RecipientStatus.COMPLETED
        ).count()
        failure_c = db.query(CertificateRecipient).filter(
            CertificateRecipient.job_id == job_id,
            CertificateRecipient.status == RecipientStatus.FAILED
        ).count()

        job.success_count = success_c
        job.failure_count = failure_c
        job.completed_at = utcnow()

        if job.total_count == 0:
            job.status = JobStatus.COMPLETED
        elif failure_c == 0:
            job.status = JobStatus.COMPLETED
        elif success_c == 0:
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.COMPLETED_WITH_ERRORS

        db.commit()
        logger.info(
            "Completed job %s with status=%s (success=%d, failure=%d, total=%d)",
            job_id, job.status.value, job.success_count, job.failure_count, job.total_count
        )

    except Exception as e:
        logger.exception("Unexpected batch error processing job %s: %s", job_id, e)
        try:
            job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.completed_at = utcnow()
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()
