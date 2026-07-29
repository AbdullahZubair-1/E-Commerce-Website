import os
import aiohttp
from app.core.logging import get_logger

logger = get_logger(__name__)

# ONE shared Make.com scenario for both registration and order events --
# each call includes an "event_type" field ("registration" or "order") so
# a single Router module in Make can branch to the right action(s) (Gmail
# for registration; Gmail + WhatsApp Business Cloud for orders) from one
# webhook, instead of needing a separate scenario per event (useful if
# your Make plan has a limited number of active scenarios). Optional --
# if not configured, both event types are silently skipped without ever
# blocking a real registration or order.
CUSTOMER_EVENTS_WEBHOOK_URL = os.getenv("CUSTOMER_EVENTS_WEBHOOK_URL")


async def _post_webhook(payload: dict, label: str) -> bool:
    if not CUSTOMER_EVENTS_WEBHOOK_URL:
        logger.info(f"{label} webhook not configured -- skipping.")
        return False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                CUSTOMER_EVENTS_WEBHOOK_URL, json=payload, timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status not in (200, 201, 202):
                    body = await resp.text()
                    logger.warning(f"{label} webhook failed ({resp.status}): {body}")
                    return False
                return True
    except Exception as e:
        logger.warning(f"{label} webhook failed: {e}")
        return False


async def send_welcome_email(site_name: str, customer_name: str, customer_email: str) -> bool:
    return await _post_webhook(
        {
            "event_type": "registration",
            "site_name": site_name,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": "",
            "order_id": "",
            "total_amount": "",
            "item_summary": "",
        },
        "Welcome email",
    )


async def send_order_confirmation_email(
    site_name: str, customer_name: str, customer_email: str,
    order_id: str, total_amount: str, item_summary: str,
    customer_phone: str = "",
) -> bool:
    return await _post_webhook(
        {
            "event_type": "order",
            "site_name": site_name,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
            "order_id": order_id,
            "total_amount": total_amount,
            "item_summary": item_summary,
        },
        "Order confirmation email",
    )