from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.deps import ensure_board_access
from app.models import User
from app.realtime.manager import manager
from app.security import decode_access_token

router = APIRouter(tags=['websocket'])


@router.websocket('/ws/boards/{board_id}')
async def board_websocket(websocket: WebSocket, board_id: UUID, token: str) -> None:
    async with AsyncSessionLocal() as db:
        try:
            payload = decode_access_token(token)
            user_id = UUID(payload['sub'])
            result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
            user = result.scalar_one_or_none()
            if not user:
                await websocket.close(code=4401)
                return
            await ensure_board_access(db, board_id, user)
        except Exception:
            await websocket.close(code=4401)
            return

        await manager.connect(board_id, websocket)
        await manager.broadcast(board_id, {'type': 'presence.joined', 'user_id': str(user.id), 'username': user.username}, sender=websocket)
        try:
            while True:
                message = await websocket.receive_json()
                event_type = message.get('type', 'board.event')
                if event_type not in {'cursor.moved', 'element.created', 'element.updated', 'element.deleted', 'comment.created'}:
                    await websocket.send_json({'type': 'error', 'detail': 'Unsupported event type'})
                    continue
                await manager.broadcast(
                    board_id,
                    {'type': event_type, 'user_id': str(user.id), 'username': user.username, 'payload': message.get('payload', {})},
                    sender=websocket,
                )
        except WebSocketDisconnect:
            manager.disconnect(board_id, websocket)
            await manager.broadcast(board_id, {'type': 'presence.left', 'user_id': str(user.id), 'username': user.username})
