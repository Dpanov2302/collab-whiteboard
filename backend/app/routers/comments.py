from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import get_comment_or_404, log_activity
from app.db.session import get_db
from app.deps import CurrentUser, ensure_board_access
from app.models import Comment, UserRole
from app.schemas import CommentCreate, CommentRead

router = APIRouter(prefix='/boards/{board_id}/comments', tags=['comments'])


@router.get('', response_model=list[CommentRead])
async def list_comments(board_id: UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> list[Comment]:
    await ensure_board_access(db, board_id, user)
    result = await db.execute(select(Comment).where(Comment.board_id == board_id).order_by(Comment.created_at.asc()))
    return list(result.scalars().all())


@router.post('', response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_comment(board_id: UUID, payload: CommentCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> Comment:
    await ensure_board_access(db, board_id, user, write=True)
    comment = Comment(board_id=board_id, author_id=user.id, **payload.model_dump())
    db.add(comment)
    await db.flush()
    await log_activity(db, board_id, user.id, 'comment.created', {'comment_id': str(comment.id)})
    await db.commit()
    await db.refresh(comment)
    return comment


@router.delete('/{comment_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(board_id: UUID, comment_id: UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> None:
    await ensure_board_access(db, board_id, user, write=True)
    comment = await get_comment_or_404(db, board_id, comment_id)
    if comment.author_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail='Only author or admin can delete comment')
    await db.delete(comment)
    await db.commit()
