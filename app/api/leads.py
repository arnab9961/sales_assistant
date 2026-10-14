import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.leads import CRMDealRecord, Lead
from app.schemas.leads import CRMDealResponse, LeadCreateRequest, LeadResponse
from app.services.ai_service import AIQualificationService
from app.services.webhook_service import notify_n8n_webhook

logger = logging.getLogger("sales_ops.leads")

router = APIRouter(prefix="/api", tags=["Leads & CRM"])
ai_service = AIQualificationService()


@router.post("/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_and_qualify_lead(
    lead_in: LeadCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a new sales lead, detect duplicates by email/phone (409),
    and trigger automated AI lead qualification with Groq.
    """
    # Duplicate detection by email or phone
    existing_lead = (
        db.query(Lead)
        .filter((Lead.email == lead_in.email) | (Lead.phone == lead_in.phone))
        .first()
    )
    if existing_lead:
        logger.warning(
            f"Duplicate lead submission blocked: email='{lead_in.email}', phone='{lead_in.phone}' "
            f"(Existing Lead ID: {existing_lead.id})"
        )
        field_match = "email" if existing_lead.email == lead_in.email else "phone number"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A lead with this {field_match} already exists in the system (Lead ID: {existing_lead.id}).",
        )

    # Perform AI qualification
    q_status, category, score, reason, ai_error = ai_service.qualify_lead(
        name=lead_in.name,
        budget=lead_in.budget,
        interest=lead_in.interest,
        message=lead_in.message,
    )

    # Persist lead to database
    lead_obj = Lead(
        name=lead_in.name,
        email=lead_in.email,
        phone=lead_in.phone,
        budget=lead_in.budget,
        interest=lead_in.interest,
        message=lead_in.message,
        qualification_status=q_status,
        category=category,
        score=score,
        reason=reason,
        ai_error=ai_error,
    )
    db.add(lead_obj)
    db.commit()
    db.refresh(lead_obj)

    # Forward to external n8n workflow if configured (failure does not break response)
    n8n_status = notify_n8n_webhook(
        {
            "event": "lead_qualified",
            "lead_id": lead_obj.id,
            "name": lead_obj.name,
            "budget": lead_obj.budget,
            "interest": lead_obj.interest,
            "category": lead_obj.category,
            "score": lead_obj.score,
            "qualification_status": lead_obj.qualification_status,
        }
    )
    lead_obj.n8n_status = n8n_status
    db.commit()
    db.refresh(lead_obj)

    return lead_obj


@router.get("/leads", response_model=List[LeadResponse])
def list_leads(db: Session = Depends(get_db)):
    """List all leads and their AI qualification outcomes for dashboard tracking."""
    return db.query(Lead).order_by(Lead.id.desc()).all()


def recursive_extract_field(data: Any, target_keys: List[str]) -> Optional[Any]:
    """Recursively search for first occurrence of any target key in arbitrary nested dictionaries or lists."""
    if isinstance(data, dict):
        for k, v in data.items():
            if str(k).strip().lower() in target_keys and v is not None:
                return v
        for v in data.values():
            found = recursive_extract_field(v, target_keys)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = recursive_extract_field(item, target_keys)
            if found is not None:
                return found
    return None


@router.post("/map/crm", response_model=CRMDealResponse)
def map_nested_crm_deal(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """Map arbitrary, non-standard, and nested CRM JSON objects into standardized deal records.
    Handles extra fields, missing keys, string-encoded numeric values, and varied nesting without crashing.
    """
    # 1. Extract Customer ID
    raw_id = recursive_extract_field(payload, ["customer_id", "id", "cust_id", "client_id"])
    customer_id = None
    if raw_id is not None:
        try:
            customer_id = int(str(raw_id).replace(",", "").strip())
        except (ValueError, TypeError):
            customer_id = None

    # 2. Extract Customer Name
    raw_name = recursive_extract_field(payload, ["customer_name", "name", "client_name", "full_name"])
    customer_name = str(raw_name).strip() if raw_name is not None else None

    # 3. Extract Region
    raw_region = recursive_extract_field(payload, ["region", "city", "division", "location", "zone"])
    region = str(raw_region).strip() if raw_region is not None else None

    # 4. Extract Deal Value (as float number)
    raw_amount = recursive_extract_field(
        payload, ["deal_value", "amount", "sales_price", "price", "value", "deal_amount"]
    )
    deal_value = None
    if raw_amount is not None:
        try:
            clean_str = str(raw_amount).replace(",", "").strip()
            deal_value = float(clean_str)
        except (ValueError, TypeError):
            deal_value = None

    # 5. Extract Lead Status
    raw_status = recursive_extract_field(payload, ["lead_status", "status", "stage", "state"])
    lead_status = str(raw_status).strip() if raw_status is not None else None

    # Save to crm_deal_records
    crm_record = CRMDealRecord(
        customer_id=customer_id,
        customer_name=customer_name,
        region=region,
        deal_value=deal_value,
        lead_status=lead_status,
        raw_payload=json.dumps(payload),
    )
    db.add(crm_record)
    db.commit()
    db.refresh(crm_record)

    return CRMDealResponse(
        customer_id=customer_id,
        customer_name=customer_name,
        region=region,
        deal_value=deal_value,
        lead_status=lead_status,
    )
