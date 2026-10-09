import uuid
from app.db.models import CertificateJob, JobStatus


def test_create_bulk_job_success(client, db_session):
    payload = {
        "event_name": "Python Development Bootcamp",
        "organization_name": "Tech Academy",
        "issue_date": "2026-10-09",
        "certificate_title": "Certificate of Excellence",
        "recipients": [
            {"name": "Rahul Sharma", "email": "rahul@example.com"},
            {"name": "Priya Verma", "email": "priya@example.com"}
        ]
    }

    response = client.post("/api/v1/certificate-jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    
    assert "job_id" in data
    assert data["status"] == "pending"
    assert data["total_count"] == 2
    assert f"/api/v1/certificate-jobs/{data['job_id']}" in data["status_url"]

    # Verify persisted in database
    job = db_session.query(CertificateJob).filter(CertificateJob.id == data["job_id"]).first()
    assert job is not None
    assert job.event_name == "Python Development Bootcamp"
    assert job.organization_name == "Tech Academy"
    assert job.total_count == 2
    assert len(job.recipients) == 2


def test_get_job_details_not_found(client):
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/certificate-jobs/{fake_id}")
    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]


def test_list_jobs_and_pagination(client):
    for i in range(5):
        payload = {
            "event_name": f"Event {i}",
            "organization_name": "Academy",
            "issue_date": "2026-10-09",
            "recipients": [{"name": f"User {i}", "email": f"user{i}@example.com"}]
        }
        resp = client.post("/api/v1/certificate-jobs", json=payload)
        assert resp.status_code == 202

    # Query list
    response = client.get("/api/v1/certificate-jobs?limit=3&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 5
    assert len(data["items"]) == 3
    assert data["limit"] == 3
    assert data["offset"] == 0


def test_get_job_recipients_endpoint(client):
    payload = {
        "event_name": "Cloud Native Masterclass",
        "organization_name": "DevOps Hub",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "Alice Green", "email": "alice@example.com"},
            {"name": "Bob Stone", "email": "bob@example.com"}
        ]
    }
    create_resp = client.post("/api/v1/certificate-jobs", json=payload)
    job_id = create_resp.json()["job_id"]

    recipients_resp = client.get(f"/api/v1/certificate-jobs/{job_id}/recipients")
    assert recipients_resp.status_code == 200
    rec_data = recipients_resp.json()
    assert rec_data["total"] == 2
    assert len(rec_data["items"]) == 2
    names = [r["name"] for r in rec_data["items"]]
    assert "Alice Green" in names
    assert "Bob Stone" in names
