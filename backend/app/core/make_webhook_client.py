import os
from datetime import datetime, timezone
import aiohttp
from app.core.logging import get_logger

logger = get_logger(__name__)

MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")


async def append_lead_via_make(name: str, email: str, phone: str | None, note: str) -> bool:
    if not MAKE_WEBHOOK_URL:
        logger.info("MAKE_WEBHOOK_URL not configured -- skipping lead push.")
        return False

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "name": name,
        "email": email,
        "phone": phone or "",
        "note": note,
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