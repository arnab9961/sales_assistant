import hmac
import logging
from typing import Any, Dict, Optional
import httpx

from app.config import settings

logger = logging.getLogger("sales_ops.webhook")


def verify_webhook_api_key(api_key_header: Optional[str]) -> bool:
    """Constant-time verification of the X-API-Key header against configured WEBHOOK_API_KEY."""
    if not api_key_header:
        return False
    expected_key = settings.WEBHOOK_API_KEY
    return hmac.compare_digest(api_key_header.strip(), expected_key.strip())


def notify_n8n_webhook(payload: Dict[str, Any]) -> str:
    """Non-blocking outbound notification to N8N workflow webhook if N8N_WEBHOOK_URL is configured."""
    n8n_url = settings.N8N_WEBHOOK_URL
    if not n8n_url or not n8n_url.startswith("http"):
        return "Not Configured"

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(n8n_url, json=payload)
        if resp.status_code in (200, 201, 204):
            logger.info(f"Successfully notified n8n webhook at {n8n_url}")
            return "Sent"
        else:
            logger.warning(f"n8n webhook returned status {resp.status_code}: {resp.text}")
            return f"Failed (HTTP {resp.status_code})"
    except Exception as e:
        logger.warning(f"Failed to post to n8n webhook ({n8n_url}): {e}")
        return f"Failed ({type(e).__name__})"
