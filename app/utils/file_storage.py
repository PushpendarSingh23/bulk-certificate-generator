import re
from pathlib import Path
from typing import Optional
from app.core.config import settings
from app.core.logging import logger


def sanitize_filename(name: str) -> str:
    """Sanitizes a string to be safely used in filenames without path characters or dots."""
    # Replace anything other than alphanumeric and hyphens with underscores
    sanitized = re.sub(r'[^\w\-]', '_', name.strip())
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized).strip('_')
    return sanitized[:100] or "certificate"


def get_certificate_path(job_id: str, certificate_id: str) -> Path:
    """
    Returns an absolute, safe path inside the configured storage directory.
    Uses subdirectories by job_id to prevent directory bloat while ensuring isolation.
    """
    safe_job_id = sanitize_filename(job_id)
    safe_cert_id = sanitize_filename(certificate_id)
    
    base_dir = settings.storage_path
    job_dir = base_dir / safe_job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = job_dir / f"{safe_cert_id}.pdf"
    
    # Path traversal protection
    if not str(file_path.resolve()).startswith(str(base_dir.resolve())):
        raise ValueError("Invalid storage path detected (path traversal attempt).")
        
    return file_path


def remove_file_safely(file_path: Optional[str | Path]) -> None:
    """Safely delete an incomplete or temporary file."""
    if not file_path:
        return
    try:
        p = Path(file_path).resolve()
        if p.exists() and p.is_file():
            p.unlink()
            logger.info("Removed file %s", p)
    except Exception as e:
        logger.warning("Failed to remove file %s: %s", file_path, e)
