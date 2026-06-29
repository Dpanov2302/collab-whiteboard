import enum
import uuid
from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class UserRole(str, enum.Enum):
    USER = 'user'
    ADMIN = 'admin'


class MemberRole(str, enum.Enum):
    OWNER = 'owner'
    EDITOR = 'editor'
    VIEWER = 'viewer'


class ElementType(str, enum.Enum):
    STICKY = 'sticky'
    TEXT = 'text'
    RECTANGLE = 'rectangle'
    ELLIPSE = 'ellipse'
    CONNECTOR = 'connector'


class ApplicationStatus(str, enum.Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name='user_role'), default=UserRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    workspaces: Mapped[list['Workspace']] = relationship(back_populates='owner')


class Workspace(Base):
    __tablename__ = 'workspaces'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    owner: Mapped[User] = relationship(back_populates='workspaces')
    members: Mapped[list['WorkspaceMember']] = relationship(back_populates='workspace', cascade='all, delete-orphan')
    boards: Mapped[list['Board']] = relationship(back_populates='workspace', cascade='all, delete-orphan')


class WorkspaceMember(Base):
    __tablename__ = 'workspace_members'
    __table_args__ = (UniqueConstraint('workspace_id', 'user_id', name='uq_workspace_member'),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole, name='member_role'), default=MemberRole.VIEWER, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    workspace: Mapped[Workspace] = relationship(back_populates='members')
    user: Mapped[User] = relationship()


class Board(Base):
    __tablename__ = 'boards'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    workspace: Mapped[Workspace] = relationship(back_populates='boards')
    created_by: Mapped[User] = relationship()
    members: Mapped[list['BoardMember']] = relationship(back_populates='board', cascade='all, delete-orphan')
    elements: Mapped[list['BoardElement']] = relationship(back_populates='board', cascade='all, delete-orphan')


class BoardMember(Base):
    __tablename__ = 'board_members'
    __table_args__ = (UniqueConstraint('board_id', 'user_id', name='uq_board_member'),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('boards.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole, name='board_member_role'), default=MemberRole.VIEWER, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    board: Mapped[Board] = relationship(back_populates='members')
    user: Mapped[User] = relationship()


class BoardElement(Base):
    __tablename__ = 'board_elements'
    __table_args__ = (
        CheckConstraint('width >= 1', name='ck_board_element_width'),
        CheckConstraint('height >= 1', name='ck_board_element_height'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('boards.id', ondelete='CASCADE'), nullable=False, index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    type: Mapped[ElementType] = mapped_column(Enum(ElementType, name='element_type'), nullable=False)
    x: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    y: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    width: Mapped[float] = mapped_column(Float, default=160, nullable=False)
    height: Mapped[float] = mapped_column(Float, default=90, nullable=False)
    z_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content: Mapped[str] = mapped_column(Text, default='', nullable=False)
    style: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    board: Mapped[Board] = relationship(back_populates='elements')
    author: Mapped[User] = relationship()


class Comment(Base):
    __tablename__ = 'comments'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('boards.id', ondelete='CASCADE'), nullable=False, index=True)
    element_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('board_elements.id', ondelete='CASCADE'), nullable=True, index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    author: Mapped[User] = relationship()
    board: Mapped[Board] = relationship()
    element: Mapped[BoardElement | None] = relationship()


class ActivityLog(Base):
    __tablename__ = 'activity_logs'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('boards.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship()
    board: Mapped[Board] = relationship()
