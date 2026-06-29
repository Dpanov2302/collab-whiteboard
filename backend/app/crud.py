from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import ActivityLog, Board, BoardElement, BoardMember, Comment, MemberRole, User, Workspace, WorkspaceMember
from app.schemas import BoardElementCreate, BoardElementUpdate


async def log_activity(db: AsyncSession, board_id: UUID, user_id: UUID, action: str, payload: dict) -> ActivityLog:
    log = ActivityLog(board_id=board_id, user_id=user_id, action=action, payload=payload)
    db.add(log)
    await db.flush()
    return log


async def create_board_owner_membership(db: AsyncSession, board: Board) -> None:
    member = BoardMember(board_id=board.id, user_id=board.created_by_id, role=MemberRole.OWNER)
    db.add(member)


async def create_workspace_owner_membership(db: AsyncSession, workspace: Workspace) -> None:
    member = WorkspaceMember(workspace_id=workspace.id, user_id=workspace.owner_id, role=MemberRole.OWNER)
    db.add(member)


async def create_element(db: AsyncSession, board_id: UUID, author_id: UUID, payload: BoardElementCreate) -> BoardElement:
    element = BoardElement(board_id=board_id, author_id=author_id, **payload.model_dump())
    db.add(element)
    await db.flush()
    await log_activity(db, board_id, author_id, 'element.created', {'element_id': str(element.id), 'type': element.type.value})
    return element


async def update_element(db: AsyncSession, element: BoardElement, user_id: UUID, payload: BoardElementUpdate) -> BoardElement:
    data = payload.model_dump(exclude_unset=True)
    client_version = data.pop('version', None)
    if client_version is not None and client_version < element.version:
        raise HTTPException(status_code=409, detail='Element version conflict')
    for key, value in data.items():
        setattr(element, key, value)
    element.version += 1
    await db.flush()
    await log_activity(db, element.board_id, user_id, 'element.updated', {'element_id': str(element.id), 'version': element.version})
    return element


async def get_element_or_404(db: AsyncSession, board_id: UUID, element_id: UUID) -> BoardElement:
    result = await db.execute(select(BoardElement).where(BoardElement.board_id == board_id, BoardElement.id == element_id))
    element = result.scalar_one_or_none()
    if not element:
        raise HTTPException(status_code=404, detail='Element not found')
    return element


async def get_comment_or_404(db: AsyncSession, board_id: UUID, comment_id: UUID) -> Comment:
    result = await db.execute(select(Comment).where(Comment.board_id == board_id, Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail='Comment not found')
    return comment
