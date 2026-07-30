import os
from datetime import datetime, timezone
import aiohttp
from app.core.logging import get_logger

logger = get_logger(__name__)

# A Make.com "scenario" starting with a Webhook trigger, connected to a
# Google Sheets "Add a Row" action. This is a much simpler alternative to
# Composio for this one job -- no API keys, no OAuth connected-account IDs,
# no workspaces to match up. Just one URL, and Make's own UI handles the
# Google Sheets authorization entirely on their side.
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")


async def append_lead_via_make(
    name: str, email: str, phone: str | None, note: str,
    site_name: str = "", doctor_name: str = "", scheduled_at: str = "",
) -> bool:
    """POST a lead to a Make.com webhook. Best-effort -- returns False (and
    logs a warning) instead of raising, so a Make/Sheets hiccup never blocks
    the actual appointment booking, which is the part that matters.

    Includes both the Sheets-row fields (name/email/phone/note) and the
    email-confirmation fields (site_name/doctor_name/scheduled_at) in one
    payload, so this single webhook can drive two actions in the same Make
    scenario -- "Add a Row" AND "Send an Email" -- instead of needing a
    second separate webhook/scenario for the appointment confirmation email.
    """
    if not MAKE_WEBHOOK_URL:
        logger.info("MAKE_WEBHOOK_URL not configured -- skipping lead push.")
        return False

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "name": name,
        "email": email,
        "phone": phone or "",
        "note": note,
        "site_name": site_name,
        "doctor_name": doctor_name,
        "scheduled_at": scheduled_at,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                MAKE_WEBHOOK_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status not in (200, 201, 202):
                    body = await resp.text()
                    logger.warning(f"Make.com webhook push failed ({resp.status}): {body}")
                    return False
                return True
    except Exception as e:
        logger.warning(f"Make.com webhook push failed: {e}")
        return False