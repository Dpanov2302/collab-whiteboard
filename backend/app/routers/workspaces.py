from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import create_workspace_owner_membership
from app.db.session import get_db
from app.deps import CurrentUser, ensure_workspace_access
from app.models import MemberRole, Workspace, WorkspaceMember
from app.schemas import MemberCreate, WorkspaceCreate, WorkspaceRead, WorkspaceUpdate

router = APIRouter(prefix='/workspaces', tags=['workspaces'])


@router.get('', response_model=list[WorkspaceRead])
async def list_workspaces(user: CurrentUser, db: AsyncSession = Depends(get_db)) -> list[Workspace]:
    if user.role.value == 'admin':
        result = await db.execute(select(Workspace).order_by(Workspace.created_at.desc()))
    else:
        result = await db.execute(
            select(Workspace)
            .outerjoin(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where((Workspace.owner_id == user.id) | (WorkspaceMember.user_id == user.id))
            .distinct()
            .order_by(Workspace.created_at.desc())
        )
    return list(result.scalars().all())


@router.post('', response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace(payload: WorkspaceCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> Workspace:
    workspace = Workspace(owner_id=user.id, **payload.model_dump())
    db.add(workspace)
    await db.flush()
    await create_workspace_owner_membership(db, workspace)
    await db.commit()
    await db.refresh(workspace)
    return workspace


@router.get('/{workspace_id}', response_model=WorkspaceRead)
async def get_workspace(workspace_id: UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> Workspace:
    await ensure_workspace_access(db, workspace_id, user)
    return await db.get(Workspace, workspace_id)


@router.patch('/{workspace_id}', response_model=WorkspaceRead)
async def update_workspace(workspace_id: UUID, payload: WorkspaceUpdate, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> Workspace:
    role = await ensure_workspace_access(db, workspace_id, user, write=True)
    if role != MemberRole.OWNER:
        raise HTTPException(status_code=403, detail='Only workspace owner can update workspace')
    workspace = await db.get(Workspace, workspace_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(workspace, key, value)
    await db.commit()
    await db.refresh(workspace)
    return workspace


@router.delete('/{workspace_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(workspace_id: UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> None:
    role = await ensure_workspace_access(db, workspace_id, user, write=True)
    if role != MemberRole.OWNER:
        raise HTTPException(status_code=403, detail='Only workspace owner can delete workspace')
    workspace = await db.get(Workspace, workspace_id)
    await db.delete(workspace)
    await db.commit()


@router.post('/{workspace_id}/members', status_code=status.HTTP_201_CREATED)
async def add_workspace_member(workspace_id: UUID, payload: MemberCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    role = await ensure_workspace_access(db, workspace_id, user, write=True)
    if role != MemberRole.OWNER:
        raise HTTPException(status_code=403, detail='Only owner can invite members')
    member = WorkspaceMember(workspace_id=workspace_id, user_id=payload.user_id, role=payload.role)
    db.add(member)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=409, detail='Member already exists or user does not exist')
    return {'status': 'created'}
