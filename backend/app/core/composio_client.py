import os
from composio import Composio
from app.core.logging import get_logger

logger = get_logger(__name__)

COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY")
# The Composio "user" whose connected Google Sheets account should receive
# the lead. This must match whatever user_id the store owner used when they
# ran `composio connected-accounts link googlesheets` themselves (a one-time
# manual OAuth step on Composio's side -- not something this code can do).
COMPOSIO_USER_ID = os.getenv("COMPOSIO_USER_ID", "chemisto-store-owner")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_SHEET_RANGE = os.getenv("GOOGLE_SHEET_RANGE", "Sheet1!A:E")

_client: Composio | None = None


def _get_client() -> Composio:
    global _client
    if _client is None:
        _client = Composio(api_key=COMPOSIO_API_KEY)
    return _client


async def append_lead_to_sheet(name: str, email: str, phone: str | None, note: str) -> bool:
    """Append a row [timestamp, name, email, phone, note] to the configured
    Google Sheet via Composio. Best-effort -- returns False (and logs a
    warning) instead of raising, so a Google Sheets/Composio hiccup never
    blocks the actual appointment booking, which is the part that matters.

    Uses Composio's official Python SDK (`composio.tools.execute`), not raw
    HTTP -- this is the documented way to call a Composio-connected action.
    """
    if not COMPOSIO_API_KEY or not GOOGLE_SHEET_ID:
        logger.info("Composio/Google Sheet not configured -- skipping lead push.")
        return False

    from datetime import datetime, timezone

    try:
        client = _get_client()
        client.tools.execute(
            "GOOGLESHEETS_SPREADSHEETS_VALUES_APPEND",
            user_id=COMPOSIO_USER_ID,
            arguments={
                "spreadsheet_id": GOOGLE_SHEET_ID,
                "range": GOOGLE_SHEET_RANGE,
                "values": [[
                    datetime.now(timezone.utc).isoformat(),
                    name,
                    email,
                    phone or "",
                    note,
                ]],
                "value_input_option": "USER_ENTERED",
            },
        )
        return True
    except Exception as e:
        # Non-fatal: the appointment is already booked/saved locally by the
        # time this runs. Losing the Sheets row is unfortunate but should
        # never undo a real booking.
        logger.warning(f"Composio Google Sheets push failed: {e}")
        return False