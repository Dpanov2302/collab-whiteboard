import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models import Board, BoardElement, ElementType, MemberRole, User, UserRole, Workspace
from app.crud import create_board_owner_membership, create_workspace_owner_membership
from app.security import hash_password


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == 'admin@example.com'))
        if existing.scalar_one_or_none():
            print('Seed skipped: data already exists')
            return
        admin = User(email='admin@example.com', username='admin', role=UserRole.ADMIN, hashed_password=hash_password('Admin12345'))
        demo = User(email='demo@example.com', username='demo', hashed_password=hash_password('Demo12345'))
        teammate = User(email='teammate@example.com', username='teammate', hashed_password=hash_password('Demo12345'))
        db.add_all([admin, demo, teammate])
        await db.flush()
        workspace = Workspace(name='Учебный проект', description='Рабочее пространство для демонстрации realtime-доски', owner_id=demo.id)
        db.add(workspace)
        await db.flush()
        await create_workspace_owner_membership(db, workspace)
        board = Board(workspace_id=workspace.id, title='Планирование курсовой работы', description='Пример доски со стикерами и комментариями', created_by_id=demo.id, is_public=False)
        db.add(board)
        await db.flush()
        await create_board_owner_membership(db, board)
        db.add_all([
            BoardElement(board_id=board.id, author_id=demo.id, type=ElementType.STICKY, x=80, y=80, content='Собрать требования', style={'color': '#fff7ad'}),
            BoardElement(board_id=board.id, author_id=demo.id, type=ElementType.STICKY, x=280, y=80, content='Спроектировать API', style={'color': '#c8f7c5'}),
            BoardElement(board_id=board.id, author_id=demo.id, type=ElementType.RECTANGLE, x=120, y=260, width=260, height=120, content='Realtime WebSocket слой', style={'color': '#d8e9ff'}),
        ])
        await db.commit()
        print('Seed completed')


if __name__ == '__main__':
    asyncio.run(seed())
