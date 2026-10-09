from datetime import date
from sqlalchemy.orm import sessionmaker
from app.db.models import CertificateJob, CertificateRecipient, JobStatus, RecipientStatus
from app.services.job_processor import process_certificate_job


def test_job_processing_workflow(client, db_session, test_engine):
    # 1. Create a job via API
    payload = {
        "event_name": "FastAPI Production Masterclass",
        "organization_name": "Python Foundation",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "Kavita Rao", "email": "kavita@example.com"},
            {"name": "Suresh Raina", "email": "suresh@example.com"}
        ]
    }
    res = client.post("/api/v1/certificate-jobs", json=payload)
    assert res.status_code == 202
    job_id = res.json()["job_id"]

    # 2. Synchronously execute worker for deterministic testing
    SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    process_certificate_job(job_id=job_id, db_session_factory=SessionFactory)

    # 3. Check status via API
    status_res = client.get(f"/api/v1/certificate-jobs/{job_id}")
    assert status_res.status_code == 200
    job_data = status_res.json()

    assert job_data["status"] == "completed"
    assert job_data["total_count"] == 2
    assert job_data["success_count"] == 2
    assert job_data["failure_count"] == 0
    assert job_data["pending_count"] == 0
    assert job_data["progress_percentage"] == 100.0
    assert job_data["completed_at"] is not None

    # Verify recipients have certificate_ids
    for recipient in job_data["recipients"]:
        assert recipient["status"] == "completed"
        assert recipient["certificate_id"] is not None
        assert recipient["certificate_id"].startswith("CERT-")
        assert recipient["error_message"] is None
