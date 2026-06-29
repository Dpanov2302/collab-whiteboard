from typing import Annotated
from uuid import UUID
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.db.session import get_db
from app.models import Board, BoardMember, MemberRole, User, UserRole, Workspace, WorkspaceMember
from app.security import decode_access_token

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f'{settings.API_PREFIX}/auth/login')
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = decode_access_token(token)
        user_id = payload.get('sub')
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    result = await db.execute(select(User).where(User.id == UUID(user_id), User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if not user:
        raise credentials_exception
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin role required')
    return user


async def ensure_workspace_access(db: AsyncSession, workspace_id: UUID, user: User, write: bool = False) -> MemberRole | None:
    if user.role == UserRole.ADMIN:
        return MemberRole.OWNER
    workspace = await db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail='Workspace not found')
    if workspace.owner_id == user.id:
        return MemberRole.OWNER
    result = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user.id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail='Workspace access denied')
    if write and member.role == MemberRole.VIEWER:
        raise HTTPException(status_code=403, detail='Write access required')
    return member.role


async def ensure_board_access(db: AsyncSession, board_id: UUID, user: User, write: bool = False) -> MemberRole | None:
    board = await db.get(Board, board_id)
    if not board:
        raise HTTPException(status_code=404, detail='Board not found')
    if user.role == UserRole.ADMIN:
        return MemberRole.OWNER
    if board.created_by_id == user.id:
        return MemberRole.OWNER
    result = await db.execute(select(BoardMember).where(BoardMember.board_id == board_id, BoardMember.user_id == user.id))
    member = result.scalar_one_or_none()
    if member:
        if write and member.role == MemberRole.VIEWER:
            raise HTTPException(status_code=403, detail='Write access required')
        return member.role
    if board.is_public and not write:
        return None
    raise HTTPException(status_code=403, detail='Board access denied')
