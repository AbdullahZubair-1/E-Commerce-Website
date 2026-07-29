import os
from datetime import datetime
import aiohttp
from app.core.logging import get_logger

logger = get_logger(__name__)

CAL_API_KEY = os.getenv("CAL_API_KEY")
CAL_API_BASE = "https://api.cal.com/v2"
# Cal.com's v2 API requires a version header to pin the exact response
# shape -- and critically, /slots and /bookings each need a DIFFERENT
# version value. Using the wrong one doesn't error; it silently falls back
# to an older API version with a different response shape, which is why
# this bug was invisible in the logs (200 OK, just wrong/unparseable data).
CAL_API_VERSION_SLOTS = "2024-09-04"
CAL_API_VERSION_BOOKINGS = "2024-08-13"


class CalComError(Exception):
    pass


async def get_available_slots(event_type_id: str, start_date: str, end_date: str) -> list[str]:
    """Get available booking slots for a doctor's Cal.com event type between
    two ISO dates (YYYY-MM-DD). No official Python SDK exists for Cal.com --
    this is a direct call to their documented REST API (v2)."""
    if not CAL_API_KEY:
        raise CalComError("CAL_API_KEY is not configured.")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{CAL_API_BASE}/slots",
            headers={
                "Authorization": f"Bearer {CAL_API_KEY}",
                "cal-api-version": CAL_API_VERSION_SLOTS,
            },
            params={
                "eventTypeId": event_type_id,
                "start": start_date,
                "end": end_date,
            },
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                logger.warning(f"Cal.com get_available_slots failed ({resp.status}): {body}")
                raise CalComError(f"Cal.com returned {resp.status}")
            payload = await resp.json()

    # Cal.com groups slots by date: {"data": {"2026-08-01": [{"start": "..."}]}}
    slots: list[str] = []
    for day_slots in (payload.get("data") or {}).values():
        for slot in day_slots:
            if slot.get("start"):
                slots.append(slot["start"])

    if not slots:
        # Successful response but nothing parsed out of it -- log the raw
        # shape so a future "no availability shown" report can actually be
        # diagnosed from the logs instead of guessing blind again.
        logger.info(f"Cal.com returned 200 but 0 parsed slots for event_type={event_type_id} {start_date}..{end_date}. Raw payload: {payload}")

    return slots


async def create_booking(
    event_type_id: str,
    start_iso: str,
    attendee_name: str,
    attendee_email: str,
    attendee_timezone: str = "UTC",
    attendee_phone: str | None = None,
) -> dict:
    """Create a real booking on Cal.com. Returns the booking response dict
    (includes the booking's uid) on success; raises CalComError on failure."""
    if not CAL_API_KEY:
        raise CalComError("CAL_API_KEY is not configured.")

    attendee: dict = {
        "name": attendee_name,
        "email": attendee_email,
        "timeZone": attendee_timezone,
    }
    if attendee_phone:
        attendee["phoneNumber"] = attendee_phone

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{CAL_API_BASE}/bookings",
            headers={
                "Authorization": f"Bearer {CAL_API_KEY}",
                "cal-api-version": CAL_API_VERSION_BOOKINGS,
                "Content-Type": "application/json",
            },
            json={
                "eventTypeId": int(event_type_id) if event_type_id.isdigit() else event_type_id,
                "start": start_iso,
                "attendee": attendee,
            },
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            body = await resp.json()
            if resp.status not in (200, 201):
                logger.warning(f"Cal.com create_booking failed ({resp.status}): {body}")
                raise CalComError(body.get("error", {}).get("message", f"Cal.com returned {resp.status}"))
            return body.get("data", body)