import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.leads import Lead
from app.services.webhook_service import verify_webhook_api_key

logger = logging.getLogger("sales_ops.webhook_api")

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


@router.post("/lead-result")
def receive_lead_webhook_result(
    payload: Dict[str, Any],
    x_api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
):
    """Secure webhook endpoint for external automation workflows (e.g., n8n).
    Protected by constant-time X-API-Key comparison.
    """
    if not verify_webhook_api_key(x_api_key):
        logger.warning("Unauthorized webhook request rejected: Invalid or missing X-API-Key.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header",
        )

    logger.info(f"Received valid authenticated webhook: {payload}")

    # Optionally update existing lead if lead_id is present
    lead_id = payload.get("lead_id")
    if lead_id:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            if "status" in payload:
                lead.qualification_status = str(payload["status"])
            if "category" in payload:
                lead.category = str(payload["category"])
            if "score" in payload:
                try:
                    lead.score = int(payload["score"])
                except (ValueError, TypeError):
                    pass
            if "n8n_notes" in payload:
                lead.reason = f"{lead.reason or ''}\n[n8n Update]: {payload['n8n_notes']}".strip()
            db.commit()
            return {"status": "success", "message": f"Lead {lead_id} updated successfully"}

    return {"status": "success", "message": "Webhook payload received and processed"}
