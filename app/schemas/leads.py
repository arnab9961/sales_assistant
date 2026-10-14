import re
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class LeadCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Full name of customer")
    email: EmailStr = Field(..., description="Valid email address")
    phone: str = Field(..., description="Phone number with at least 10 digits")
    budget: float = Field(..., gt=0, description="Purchase budget in BDT (must be positive)")
    interest: str = Field(..., min_length=1, max_length=255, description="Product interest (e.g. Kuakata Hotel Share)")
    message: Optional[str] = Field(None, max_length=2000, description="Customer message / inquiries")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Name cannot be empty or whitespace only")
        return clean

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        clean_digits = re.sub(r"\D", "", v)
        # Strip leading country code 88 if present
        if clean_digits.startswith("880") and len(clean_digits) >= 13:
            clean_digits = clean_digits[2:]
        if len(clean_digits) < 10:
            raise ValueError(f"Phone number must contain at least 10 digits (got {len(clean_digits)} from '{v}')")
        return clean_digits

    @field_validator("interest")
    @classmethod
    def validate_interest(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Interest cannot be empty or whitespace only")
        return clean


class AIQualificationResult(BaseModel):
    category: Optional[str] = Field(None, description="Hot, Warm, or Cold")
    score: Optional[int] = Field(None, ge=0, le=100, description="Score 0 to 100")
    reason: Optional[str] = Field(None, description="Detailed qualification rationale")


class LeadResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    budget: float
    interest: str
    message: Optional[str]
    qualification_status: str
    category: Optional[str]
    score: Optional[int]
    reason: Optional[str]
    ai_error: Optional[str]
    n8n_status: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CRMDealResponse(BaseModel):
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    region: Optional[str] = None
    deal_value: Optional[float] = None
    lead_status: Optional[str] = None
