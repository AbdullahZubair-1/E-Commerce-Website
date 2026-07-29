import uuid
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from app.database.session import get_db, AsyncSessionLocal
from app.schemas.base import success_response
from app.repositories.notification import NotificationRepository
from app.repositories.user import UserRepository
from app.dependencies.auth import get_current_owner
from app.models.user import User
from app.core.security import decode_access_token
from app.core.admin_notifications import admin_notification_manager
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin/notifications", tags=["Admin Notifications"])


@router.get("/")
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    repo = NotificationRepository(db)
    notifications = await repo.list_for_site(owner.site_id, page, page_size)
    return success_response(
        data=[
            {
                "id": str(n.id),
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "order_id": str(n.order_id) if n.order_id else None,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ],
        message="Notifications retrieved.",
    )


@router.get("/unread-count")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    repo = NotificationRepository(db)
    count = await repo.unread_count(owner.site_id)
    return success_response(data={"count": count}, message="Unread count retrieved.")


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    repo = NotificationRepository(db)
    await repo.mark_read(notification_id, owner.site_id)
    return success_response(message="Marked as read.")


@router.patch("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    repo = NotificationRepository(db)
    await repo.mark_all_read(owner.site_id)
    return success_response(message="All marked as read.")


@router.websocket("/ws")
async def notifications_websocket(websocket: WebSocket, token: str = Query(...)):
    """Real-time push for new orders while the admin panel is open.
    Authenticated via a `token` query param, same reasoning as the chat
    WebSocket -- browsers can't set custom headers on the handshake."""
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
        if not user or not user.is_active or not user.is_owner or not user.site_id:
            await websocket.close(code=4403)
            return
        site_id = user.site_id

    await admin_notification_manager.connect(site_id, websocket)
    logger.info(f"Admin notifications WS connected: owner={user_id} site={site_id}")

    try:
        while True:
            # This channel is push-only from the server's side; just keep
            # the connection alive and ignore anything the client sends.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        admin_notification_manager.disconnect(site_id, websocket)
        logger.info(f"Admin notifications WS disconnected: owner={user_id} site={site_id}")