from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CertificateMetadata(BaseModel):
    certificate_id: str
    recipient_name: str
    recipient_email: str
    event_name: str
    organization_name: str
    issue_date: date
    certificate_title: str
    download_url: str

    model_config = ConfigDict(from_attributes=True)
