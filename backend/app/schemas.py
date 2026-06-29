from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models import ElementType, MemberRole, UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserUpdateRole(BaseModel):
    role: UserRole


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str | None
    owner_id: UUID
    created_at: datetime


class MemberCreate(BaseModel):
    user_id: UUID
    role: MemberRole = MemberRole.VIEWER


class BoardCreate(BaseModel):
    workspace_id: UUID
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    is_public: bool = False


class BoardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    is_public: bool | None = None


class BoardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workspace_id: UUID
    title: str
    description: str | None
    created_by_id: UUID
    is_public: bool
    created_at: datetime


class BoardElementCreate(BaseModel):
    type: ElementType
    x: float = 0
    y: float = 0
    width: float = Field(default=160, ge=1, le=2000)
    height: float = Field(default=90, ge=1, le=2000)
    z_index: int = 0
    content: str = Field(default='', max_length=5000)
    style: dict = Field(default_factory=dict)


class BoardElementUpdate(BaseModel):
    x: float | None = None
    y: float | None = None
    width: float | None = Field(default=None, ge=1, le=2000)
    height: float | None = Field(default=None, ge=1, le=2000)
    z_index: int | None = None
    content: str | None = Field(default=None, max_length=5000)
    style: dict | None = None
    version: int | None = Field(default=None, ge=1)


class BoardElementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    board_id: UUID
    author_id: UUID
    type: ElementType
    x: float
    y: float
    width: float
    height: float
    z_index: int
    content: str
    style: dict
    version: int
    created_at: datetime
    updated_at: datetime


class CommentCreate(BaseModel):
    element_id: UUID | None = None
    text: str = Field(min_length=1, max_length=4000)


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    board_id: UUID
    element_id: UUID | None
    author_id: UUID
    text: str
    created_at: datetime


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    board_id: UUID
    user_id: UUID
    action: str
    payload: dict
    created_at: datetime
