import uuid
from app.utils.file_storage import sanitize_filename, get_certificate_path


def test_sanitize_filename_special_characters():
    name = "../../../etc/passwd && malicious <file>! name"
    clean = sanitize_filename(name)
    assert "/" not in clean
    assert ".." not in clean
    assert "<" not in clean
    assert ">" not in clean
    assert "\\" not in clean


def test_list_jobs_empty(client):
    # Filter for non-existent status or empty query
    resp = client.get("/api/v1/certificate-jobs?status=failed")
    assert resp.status_code == 200
    assert isinstance(resp.json()["items"], list)


def test_get_nonexistent_job_recipients(client):
    fake_id = str(uuid.uuid4())
    resp = client.get(f"/api/v1/certificate-jobs/{fake_id}/recipients")
    assert resp.status_code == 404
    assert "was not found" in resp.json()["detail"]


def test_pagination_limits(client):
    resp = client.get("/api/v1/certificate-jobs?limit=500")
    # limit max is 100, should trigger validation error
    assert resp.status_code == 422
