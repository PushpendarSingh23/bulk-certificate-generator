from datetime import date
from pathlib import Path
from app.services.certificate_generator import CertificateGenerator


def test_pdf_generation_file_creation(tmp_path):
    output_pdf = tmp_path / "test_cert.pdf"
    
    result_path = CertificateGenerator.generate(
        output_path=output_pdf,
        recipient_name="Deepak Kumar",
        event_name="Full Stack Engineering Masterclass",
        organization_name="Global Tech Institute",
        issue_date=date(2026, 10, 9),
        certificate_id="CERT-TEST12345",
        certificate_title="Certificate of Achievement"
    )

    assert result_path.exists()
    assert result_path.stat().st_size > 1000  # Non-trivial PDF file size

    # Verify PDF magic header bytes
    with open(result_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"


def test_pdf_generation_custom_title(tmp_path):
    output_pdf = tmp_path / "test_custom_title.pdf"

    result_path = CertificateGenerator.generate(
        output_path=output_pdf,
        recipient_name="Ananya Roy",
        event_name="AI & Machine Learning Workshop",
        organization_name="AI Research Council",
        issue_date=date(2026, 10, 9),
        certificate_id="CERT-AI-9999",
        certificate_title="Honorary Certificate of Distinction"
    )

    assert result_path.exists()
    assert result_path.stat().st_size > 1000
    with open(result_path, "rb") as f:
        content = f.read()
        assert b"%PDF-" in content[:10]
