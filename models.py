from sqlalchemy import TIMESTAMP, Boolean, func
import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class User(Base):
    __tablename__ = "user"

    id = Column(UUID, primary_key=True, index=True)
    email = Column(String, unique = True, nullable=False)
    username = Column(String, unique = True, nullable=False)
    hashed_password = Column(String, nullable=False)
    registered_at = Column(DateTime(timezone=True), default=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)
    links = relationship("Link", back_populates="user", cascade="all, delete-orphan")



class Link(Base):
    __tablename__ = "links"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_url = Column(String, nullable=False)
    short_code = Column(String, unique=True, nullable=False)
    custom_alias = Column(String, unique=True, nullable=True)
    clicks = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=func.now())
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    user_id = Column(UUID, ForeignKey("user.id"), nullable=True)
    user = relationship("User", back_populates="links")
