import uuid
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from app.database.session import get_db, AsyncSessionLocal
from app.schemas.base import success_response
from app.schemas.social import FriendRequestCreate, MessageCreate
from app.services.social import SocialService
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.core.security import decode_access_token
from app.core.ws_manager import chat_manager
from app.core.logging import get_logger
from app.repositories.user import UserRepository
from app.repositories.friendship import FriendRequestRepository

logger = get_logger(__name__)

router = APIRouter(prefix="/social", tags=["Social"])


# --- Search & friend requests ---

@router.get("/search")
async def search_users(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search for other users on the same site to send a friend request to."""
    service = SocialService(db)
    results = await service.search_users(q, site_id=current_user.site_id, exclude_user_id=current_user.id)
    return success_response(data=[r.model_dump() for r in results], message="Search results.")


@router.post("/friend-requests")
async def send_friend_request(
    data: FriendRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SocialService(db)
    result = await service.send_friend_request(current_user, data.addressee_id)
    return success_response(data=result.model_dump(), message="Friend request sent.")


@router.patch("/friend-requests/{request_id}/accept")
async def accept_friend_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SocialService(db)
    result = await service.respond_to_request(current_user, request_id, accept=True)
    return success_response(data=result.model_dump(), message="Friend request accepted.")


@router.patch("/friend-requests/{request_id}/decline")
async def decline_friend_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SocialService(db)
    result = await service.respond_to_request(current_user, request_id, accept=False)
    return success_response(data=result.model_dump(), message="Friend request declined.")


@router.get("/friend-requests/incoming")
async def list_incoming_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SocialService(db)
    results = await service.list_incoming_requests(current_user.id)
    return success_response(data=[r.model_dump() for r in results], message="Incoming requests.")


@router.get("/friend-requests/outgoing")
async def list_outgoing_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SocialService(db)
    results = await service.list_outgoing_requests(current_user.id)
    return success_response(data=[r.model_dump() for r in results], message="Outgoing requests.")


@router.get("/friends")
async def list_friends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SocialService(db)
    results = await service.list_friends(current_user.id)
    online = [{**f.model_dump(), "online": chat_manager.is_online(f.id)} for f in results]
    return success_response(data=online, message="Friends list.")


# --- Messages ---

@router.get("/messages/{friend_id}")
async def get_conversation(
    friend_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get message history with a friend (also marks their messages as read)."""
    service = SocialService(db)
    results = await service.get_conversation(current_user, friend_id, page, page_size)
    return success_response(data=[m.model_dump() for m in results], message="Conversation retrieved.")


@router.post("/messages")
async def send_message_rest(
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """REST fallback for sending a message (also used by the WebSocket
    handler under the hood). Pushes to the recipient in real time if they're
    currently connected."""
    service = SocialService(db)
    result = await service.send_message(current_user, data.recipient_id, data.content)
    await chat_manager.send_to_user(
        data.recipient_id, {"type": "message", "message": result.model_dump(mode="json")}
    )
    return success_response(data=result.model_dump(), message="Message sent.")


# --- Real-time WebSocket ---

@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket, token: str = Query(...)):
    """Real-time chat connection. Authenticated via a `token` query param
    (browsers can't set custom headers on a WebSocket handshake, so the JWT
    rides along in the URL instead of an Authorization header)."""
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            await websocket.close(code=4401)
            return
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        await websocket.close(code=4401)
        return

    async with AsyncSessionLocal() as db:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            await websocket.close(code=4401)
            return

    await chat_manager.connect(user_id, websocket)
    logger.info(f"Chat WS connected: {user_id}")

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "message":
                recipient_id = data.get("recipient_id")
                content = data.get("content", "")
                if not recipient_id or not content:
                    await websocket.send_json({"type": "error", "detail": "recipient_id and content are required."})
                    continue

                async with AsyncSessionLocal() as db:
                    service = SocialService(db)
                    user_repo = UserRepository(db)
                    sender = await user_repo.get_by_id(user_id)
                    try:
                        result = await service.send_message(sender, uuid.UUID(recipient_id), content)
                        await db.commit()
                    except Exception as exc:
                        await db.rollback()
                        await websocket.send_json({"type": "error", "detail": str(exc)})
                        continue

                payload = {"type": "message", "message": result.model_dump(mode="json")}
                # Echo back to the sender (so their own UI updates) and push
                # to the recipient if they're online right now.
                await websocket.send_json(payload)
                await chat_manager.send_to_user(uuid.UUID(recipient_id), payload)

            elif msg_type == "typing":
                recipient_id = data.get("recipient_id")
                if recipient_id:
                    await chat_manager.send_to_user(
                        uuid.UUID(recipient_id), {"type": "typing", "from_user_id": str(user_id)}
                    )

    except WebSocketDisconnect:
        pass
    finally:
        chat_manager.disconnect(user_id, websocket)
        logger.info(f"Chat WS disconnected: {user_id}")