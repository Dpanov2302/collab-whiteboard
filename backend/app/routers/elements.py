from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import create_element, get_element_or_404, update_element
from app.db.session import get_db
from app.deps import CurrentUser, ensure_board_access
from app.models import BoardElement
from app.schemas import BoardElementCreate, BoardElementRead, BoardElementUpdate

router = APIRouter(prefix='/boards/{board_id}/elements', tags=['elements'])


@router.get('', response_model=list[BoardElementRead])
async def list_elements(board_id: UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> list[BoardElement]:
    await ensure_board_access(db, board_id, user)
    result = await db.execute(select(BoardElement).where(BoardElement.board_id == board_id).order_by(BoardElement.z_index.asc(), BoardElement.created_at.asc()))
    return list(result.scalars().all())


@router.post('', response_model=BoardElementRead, status_code=status.HTTP_201_CREATED)
async def create_board_element(board_id: UUID, payload: BoardElementCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> BoardElement:
    await ensure_board_access(db, board_id, user, write=True)
    element = await create_element(db, board_id, user.id, payload)
    await db.commit()
    await db.refresh(element)
    return element


@router.get('/{element_id}', response_model=BoardElementRead)
async def get_board_element(board_id: UUID, element_id: UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> BoardElement:
    await ensure_board_access(db, board_id, user)
    return await get_element_or_404(db, board_id, element_id)


@router.patch('/{element_id}', response_model=BoardElementRead)
async def update_board_element(board_id: UUID, element_id: UUID, payload: BoardElementUpdate, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> BoardElement:
    await ensure_board_access(db, board_id, user, write=True)
    element = await get_element_or_404(db, board_id, element_id)
    element = await update_element(db, element, user.id, payload)
    await db.commit()
    await db.refresh(element)
    return element


@router.delete('/{element_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_board_element(board_id: UUID, element_id: UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> None:
    await ensure_board_access(db, board_id, user, write=True)
    element = await get_element_or_404(db, board_id, element_id)
    await db.delete(element)
    await db.commit()
