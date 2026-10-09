from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from app.db.models import RecipientStatus


class RecipientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Full name of the recipient")
    email: EmailStr = Field(..., description="Valid email address of the recipient")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Recipient name cannot be empty or whitespace only")
        return v


class RecipientResponse(BaseModel):
    id: str
    job_id: str
    name: str
    email: str
    status: RecipientStatus
    certificate_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    generated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
