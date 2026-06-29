from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.deps import CurrentUser, require_admin
from app.models import User
from app.schemas import UserRead, UserUpdateRole

router = APIRouter(prefix='/admin', tags=['admin'])


@router.get('/users', response_model=list[UserRead])
async def list_users(_: User = Depends(require_admin), db: AsyncSession = Depends(get_db)) -> list[User]:
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


@router.patch('/users/{user_id}/role', response_model=UserRead)
async def update_user_role(user_id: UUID, payload: UserUpdateRole, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    if user.id == admin.id and payload.role.value != 'admin':
        raise HTTPException(status_code=400, detail='Admin cannot remove own admin role')
    user.role = payload.role
    await db.commit()
    await db.refresh(user)
    return user


@router.patch('/users/{user_id}/block', response_model=UserRead)
async def block_user(user_id: UUID, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail='Admin cannot block own account')
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return user
