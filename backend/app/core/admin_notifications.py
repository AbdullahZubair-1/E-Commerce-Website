import uuid
from fastapi import WebSocket


class AdminNotificationManager:
    """Tracks which site owners currently have the admin panel open, so a
    new order can be pushed to them immediately. Keyed by site_id (not
    user_id), since a push should reach whichever owner(s) of that site are
    currently connected. Same in-memory, single-process design as the chat
    connection manager -- see core/ws_manager.py for the same caveat about
    scaling to multiple backend workers."""

    def __init__(self):
        self._connections: dict[uuid.UUID, set[WebSocket]] = {}

    async def connect(self, site_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(site_id, set()).add(websocket)

    def disconnect(self, site_id: uuid.UUID, websocket: WebSocket) -> None:
        conns = self._connections.get(site_id)
        if conns:
            conns.discard(websocket)
            if not conns:
                self._connections.pop(site_id, None)

    async def notify_site(self, site_id: uuid.UUID, payload: dict) -> None:
        conns = self._connections.get(site_id)
        if not conns:
            return
        dead = []
        for ws in conns:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            conns.discard(ws)


admin_notification_manager = AdminNotificationManager()