import uuid
from sqlalchemy import Column, UUID, String, Boolean
from sqlalchemy.orm import relationship

from src.database import Base


class User(Base):
    __tablename__ = "user"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=True)
    surname = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    group_relation = relationship("GroupTasks", back_populates="owner_relation")
    access = relationship("GroupAccess", back_populates="user")
