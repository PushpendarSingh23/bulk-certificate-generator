import uuid
from sqlalchemy.orm import sessionmaker
from app.services.job_processor import process_certificate_job


def test_download_certificate_success(client, test_engine):
    payload = {
        "event_name": "API Design Masterclass",
        "organization_name": "OpenAPI Guild",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "Mohan Lal", "email": "mohan@example.com"}
        ]
    }
    create_resp = client.post("/api/v1/certificate-jobs", json=payload)
    job_id = create_resp.json()["job_id"]

    SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    process_certificate_job(job_id=job_id, db_session_factory=SessionFactory)

    # Get certificate ID
    status_resp = client.get(f"/api/v1/certificate-jobs/{job_id}")
    cert_id = status_resp.json()["recipients"][0]["certificate_id"]
    assert cert_id is not None

    # Download certificate
    download_resp = client.get(f"/api/v1/certificates/{cert_id}")
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"] == "application/pdf"
    assert download_resp.content.startswith(b"%PDF-")
    assert "Mohan_Lal" in download_resp.headers.get("content-disposition", "")


def test_download_certificate_not_found(client):
    fake_cert_id = f"CERT-{uuid.uuid4().hex[:12].upper()}"
    resp = client.get(f"/api/v1/certificates/{fake_cert_id}")
    assert resp.status_code == 404
    assert "was not found" in resp.json()["detail"]
