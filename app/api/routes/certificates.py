from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.db.database import get_db
from app.db.models import CertificateRecipient, RecipientStatus
from app.utils.file_storage import sanitize_filename

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get(
    "/{certificate_id}",
    summary="Download generated PDF certificate",
    response_class=FileResponse
)
def download_certificate(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves and downloads a successfully generated PDF certificate by its unique ID.
    Returns 404 if the certificate is missing, pending, failed, or not generated.
    """
    recipient = db.query(CertificateRecipient).filter(
        CertificateRecipient.certificate_id == certificate_id
    ).first()

    if not recipient:
        logger.warning("Certificate ID %s not found in database", certificate_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' was not found."
        )

    if recipient.status != RecipientStatus.COMPLETED or not recipient.certificate_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{certificate_id}' has not been successfully generated yet (current status: {recipient.status.value})."
        )

    file_path = Path(recipient.certificate_path).resolve()
    if not file_path.exists() or not file_path.is_file():
        logger.error("Certificate file %s registered in DB but missing on disk", file_path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate file for '{certificate_id}' is temporarily unavailable."
        )

    safe_name = sanitize_filename(recipient.name)
    download_filename = f"Certificate_{safe_name}_{certificate_id}.pdf"

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=download_filename
    )
