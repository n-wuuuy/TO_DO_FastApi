from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from datetime import datetime

from src.tasks.models import Role


class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    completed: bool = False
    deadlines: datetime = None
    group_id: int

    class Config:
        from_attributes = True


class TaskGet(TaskCreate):
    id: int
    photo: Optional[str]


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    photo: Optional[str] = None
    deadlines: Optional[datetime] = None
    group_id: Optional[int] = None


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class AccessUser(BaseModel):
    id: int
    user_id: UUID
    access: bool


class TaskGetWithGroup(BaseModel):
    id: int
    name: str
    completed: bool
    deadlines: datetime


class GroupGetWithTask(BaseModel):
    id: int
    name: str
    owner: UUID
    tasks: list['TaskGetWithGroup']
    access: list['AccessUser']


class GroupGet(BaseModel):
    id: int
    name: str
    owner: UUID
    role: Role


class AccessGroupPost(BaseModel):
    user_id: UUID
    access: bool = True
    role: str


class AccessGroupUpdate(BaseModel):
    access: Optional[bool] = None
    role: Optional[str] = None
