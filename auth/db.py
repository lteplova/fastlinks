from collections.abc import AsyncGenerator
from fastapi import Depends
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy import String, Integer, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from config import DATABASE_URL

import logging
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


class Base(DeclarativeBase):
    pass

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit = False)


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    registered_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    links: Mapped[list["Link"]] = relationship(
        "Link", back_populates="user", cascade="all, delete-orphan"
    )

class Link(Base):
    __tablename__ = "links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    original_url: Mapped[str] = mapped_column(String, nullable=False)
    short_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    custom_alias: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_accessed: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    user: Mapped["User"] = relationship("User", back_populates="links")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_link_db(session: AsyncSession = Depends(get_async_session)):
    yield session
async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
