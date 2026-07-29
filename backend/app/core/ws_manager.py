import uuid
from fastapi import WebSocket


class ChatConnectionManager:
    """Tracks which users currently have an open chat WebSocket, so a new
    message can be pushed to the recipient immediately if they're online.
    In-memory and per-process -- fine for a single backend instance; if this
    is ever scaled to multiple backend workers/processes, this would need to
    move to something shared like Redis pub/sub instead."""

    def __init__(self):
        self._connections: dict[uuid.UUID, set[WebSocket]] = {}

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        conns = self._connections.get(user_id)
        if conns:
            conns.discard(websocket)
            if not conns:
                self._connections.pop(user_id, None)

    def is_online(self, user_id: uuid.UUID) -> bool:
        return bool(self._connections.get(user_id))

    async def send_to_user(self, user_id: uuid.UUID, payload: dict) -> bool:
        """Push a JSON payload to every open connection for this user.
        Returns True if the user was online and received it."""
        conns = self._connections.get(user_id)
        if not conns:
            return False
        dead = []
        for ws in conns:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            conns.discard(ws)
        return True


chat_manager = ChatConnectionManager()