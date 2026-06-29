from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import create_board_owner_membership
from app.db.session import get_db
from app.deps import CurrentUser, ensure_board_access, ensure_workspace_access
from app.models import ActivityLog, Board, BoardMember, MemberRole
from app.schemas import ActivityRead, BoardCreate, BoardRead, BoardUpdate, MemberCreate

router = APIRouter(prefix='/boards', tags=['boards'])


@router.get('', response_model=list[BoardRead])
async def list_boards(user: CurrentUser, db: AsyncSession = Depends(get_db), workspace_id: UUID | None = None) -> list[Board]:
    stmt = select(Board).order_by(Board.created_at.desc())
    if workspace_id:
        await ensure_workspace_access(db, workspace_id, user)
        stmt = stmt.where(Board.workspace_id == workspace_id)
    result = await db.execute(stmt)
    boards = []
    for board in result.scalars().all():
        try:
            await ensure_board_access(db, board.id, user)
            boards.append(board)
        except HTTPException:
            continue
    return boards


@router.post('', response_model=BoardRead, status_code=status.HTTP_201_CREATED)
async def create_board(payload: BoardCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> Board:
    await ensure_workspace_access(db, payload.workspace_id, user, write=True)
    board = Board(created_by_id=user.id, **payload.model_dump())
    db.add(board)
    await db.flush()
    await create_board_owner_membership(db, board)
    await db.commit()
    await db.refresh(board)
    return board


@router.get('/{board_id}', response_model=BoardRead)
async def get_board(board_id: UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> Board:
    await ensure_board_access(db, board_id, user)
    return await db.get(Board, board_id)


@router.patch('/{board_id}', response_model=BoardRead)
async def update_board(board_id: UUID, payload: BoardUpdate, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> Board:
    role = await ensure_board_access(db, board_id, user, write=True)
    if role != MemberRole.OWNER:
        raise HTTPException(status_code=403, detail='Only board owner can update board settings')
    board = await db.get(Board, board_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(board, key, value)
    await db.commit()
    await db.refresh(board)
    return board


@router.delete('/{board_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(board_id: UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> None:
    role = await ensure_board_access(db, board_id, user, write=True)
    if role != MemberRole.OWNER:
        raise HTTPException(status_code=403, detail='Only board owner can delete board')
    board = await db.get(Board, board_id)
    await db.delete(board)
    await db.commit()


@router.post('/{board_id}/members', status_code=status.HTTP_201_CREATED)
async def add_board_member(board_id: UUID, payload: MemberCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    role = await ensure_board_access(db, board_id, user, write=True)
    if role != MemberRole.OWNER:
        raise HTTPException(status_code=403, detail='Only owner can invite board members')
    member = BoardMember(board_id=board_id, user_id=payload.user_id, role=payload.role)
    db.add(member)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=409, detail='Member already exists or user does not exist')
    return {'status': 'created'}


@router.get('/{board_id}/activity', response_model=list[ActivityRead])
async def list_activity(board_id: UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> list[ActivityLog]:
    await ensure_board_access(db, board_id, user)
    result = await db.execute(select(ActivityLog).where(ActivityLog.board_id == board_id).order_by(ActivityLog.created_at.desc()).limit(100))
    return list(result.scalars().all())
