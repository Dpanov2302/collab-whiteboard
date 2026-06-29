from collections import defaultdict
from uuid import UUID
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, board_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._rooms[board_id].add(websocket)

    def disconnect(self, board_id: UUID, websocket: WebSocket) -> None:
        self._rooms[board_id].discard(websocket)
        if not self._rooms[board_id]:
            self._rooms.pop(board_id, None)

    async def broadcast(self, board_id: UUID, message: dict, sender: WebSocket | None = None) -> None:
        dead: list[WebSocket] = []
        for connection in list(self._rooms.get(board_id, set())):
            if sender is not None and connection is sender:
                continue
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self.disconnect(board_id, connection)


manager = ConnectionManager()
