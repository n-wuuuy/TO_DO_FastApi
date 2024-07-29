import enum

from sqlalchemy import Column, Integer, String, LargeBinary, Boolean, DateTime, ForeignKey, UUID, Enum
from sqlalchemy.orm import relationship, Mapped

from src.database import Base


class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    completed = Column(Boolean)
    photo = Column(String)
    deadlines = Column(DateTime)
    group_id = Column(Integer, ForeignKey("group_tasks.id"))

    group_tasks = relationship("GroupTasks", back_populates="tasks")


class GroupTasks(Base):
    __tablename__ = "group_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    owner = Column(UUID, ForeignKey("user.uuid"))

    tasks = relationship("Task", back_populates="group_tasks")
    owner_relation = relationship("User", back_populates="group_relation")
    access = relationship("GroupAccess", back_populates="group")


class Role(enum.Enum):
    admin = "admin"
    manager = "manager"
    user = "user"


class GroupAccess(Base):
    __tablename__ = "group_access"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID, ForeignKey("user.uuid"))
    group_id = Column(Integer, ForeignKey("group_tasks.id"))
    access = Column(Boolean, default=True)
    role = Column(Enum(Role))

    user = relationship("User", back_populates="access")
    group = relationship("GroupTasks", back_populates="access")
