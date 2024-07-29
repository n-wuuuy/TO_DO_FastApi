from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class BaseUser(BaseModel):
    username: str
    password: str
    email: str
    name: Optional[str] = None
    surname: Optional[str] = None


class UserOut(BaseUser):
    is_active: Optional[str]
    is_admin: Optional[str]


class SystemUser(BaseModel):
    id: UUID
    username: str
    email: str
    password: str


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str = None
    exp: int = None
