import pytest


def test_validation_empty_recipients(client):
    payload = {
        "event_name": "Web Security Workshop",
        "organization_name": "CyberSec Org",
        "issue_date": "2026-10-09",
        "recipients": []
    }
    response = client.post("/api/v1/certificate-jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "details" in data
    assert any("Recipient list must not be empty" in str(d["message"]) for d in data["details"])


def test_validation_invalid_email(client):
    payload = {
        "event_name": "Web Security Workshop",
        "organization_name": "CyberSec Org",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "John Doe", "email": "not-a-valid-email"}
        ]
    }
    response = client.post("/api/v1/certificate-jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "details" in data
    assert any("email" in str(d["field"]).lower() for d in data["details"])


def test_validation_empty_recipient_name(client):
    payload = {
        "event_name": "Web Security Workshop",
        "organization_name": "CyberSec Org",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "   ", "email": "valid@example.com"}
        ]
    }
    response = client.post("/api/v1/certificate-jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert any("Recipient name cannot be empty" in str(d["message"]) for d in data["details"])


def test_validation_missing_required_fields(client):
    # Missing organization_name
    payload = {
        "event_name": "Web Security Workshop",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "John Doe", "email": "valid@example.com"}
        ]
    }
    response = client.post("/api/v1/certificate-jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert any("organization_name" in str(d["field"]) for d in data["details"])


def test_validation_batch_size_exceeded(client):
    # Create 501 recipients (limit is 500)
    many_recipients = [
        {"name": f"Recipient {i}", "email": f"rec{i}@example.com"}
        for i in range(501)
    ]
    payload = {
        "event_name": "Large Scale Bootcamp",
        "organization_name": "Mega Tech",
        "issue_date": "2026-10-09",
        "recipients": many_recipients
    }
    response = client.post("/api/v1/certificate-jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert any("exceeds maximum allowed limit" in str(d["message"]) for d in data["details"])


def test_validation_invalid_date_format(client):
    payload = {
        "event_name": "Web Security Workshop",
        "organization_name": "CyberSec Org",
        "issue_date": "invalid-date",
        "recipients": [
            {"name": "John Doe", "email": "valid@example.com"}
        ]
    }
    response = client.post("/api/v1/certificate-jobs", json=payload)
    assert response.status_code == 422
