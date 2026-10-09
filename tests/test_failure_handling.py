from unittest.mock import patch
from sqlalchemy.orm import sessionmaker
from app.db.models import CertificateJob, JobStatus, RecipientStatus
from app.services.certificate_generator import CertificateGenerator
from app.services.job_processor import process_certificate_job


def test_partial_failure_isolation(client, test_engine):
    # 3 recipients, one of whom will fail during generation
    payload = {
        "event_name": "Distributed Systems Bootcamp",
        "organization_name": "Cloud Native Org",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "Winner One", "email": "winner1@example.com"},
            {"name": "Faulty Recipient", "email": "faulty@example.com"},
            {"name": "Winner Two", "email": "winner2@example.com"}
        ]
    }
    create_resp = client.post("/api/v1/certificate-jobs", json=payload)
    assert create_resp.status_code == 202
    job_id = create_resp.json()["job_id"]

    original_generate = CertificateGenerator.generate

    def mock_generate(*args, **kwargs):
        recipient_name = kwargs.get("recipient_name")
        if recipient_name == "Faulty Recipient":
            raise RuntimeError("Simulated PDF font rendering crash")
        return original_generate(*args, **kwargs)

    SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    with patch.object(CertificateGenerator, "generate", side_effect=mock_generate):
        process_certificate_job(job_id=job_id, db_session_factory=SessionFactory)

    status_resp = client.get(f"/api/v1/certificate-jobs/{job_id}")
    assert status_resp.status_code == 200
    job_data = status_resp.json()

    assert job_data["status"] == "completed_with_errors"
    assert job_data["total_count"] == 3
    assert job_data["success_count"] == 2
    assert job_data["failure_count"] == 1
    assert job_data["pending_count"] == 0
    assert job_data["progress_percentage"] == 100.0

    recipients = {r["name"]: r for r in job_data["recipients"]}
    
    assert recipients["Winner One"]["status"] == "completed"
    assert recipients["Winner One"]["certificate_id"] is not None
    assert recipients["Winner One"]["error_message"] is None

    assert recipients["Winner Two"]["status"] == "completed"
    assert recipients["Winner Two"]["certificate_id"] is not None
    assert recipients["Winner Two"]["error_message"] is None

    assert recipients["Faulty Recipient"]["status"] == "failed"
    assert recipients["Faulty Recipient"]["certificate_id"] is None
    assert "Simulated PDF font rendering crash" in recipients["Faulty Recipient"]["error_message"]


def test_complete_failure_all_recipients(client, test_engine):
    payload = {
        "event_name": "Crash Test Event",
        "organization_name": "Tester",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "Bad One", "email": "bad1@example.com"},
            {"name": "Bad Two", "email": "bad2@example.com"}
        ]
    }
    create_resp = client.post("/api/v1/certificate-jobs", json=payload)
    job_id = create_resp.json()["job_id"]

    SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    with patch.object(CertificateGenerator, "generate", side_effect=Exception("Disk out of space")):
        process_certificate_job(job_id=job_id, db_session_factory=SessionFactory)

    status_resp = client.get(f"/api/v1/certificate-jobs/{job_id}")
    assert status_resp.status_code == 200
    job_data = status_resp.json()

    assert job_data["status"] == "failed"
    assert job_data["total_count"] == 2
    assert job_data["success_count"] == 0
    assert job_data["failure_count"] == 2
