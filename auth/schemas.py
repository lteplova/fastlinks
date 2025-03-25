import uuid
from fastapi_users import schemas
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class UserRead(schemas.BaseUser[uuid.UUID]):
    id: uuid.UUID
    email: str
    username: str


class UserCreate(schemas.BaseUserCreate):
    id: uuid.UUID
    email: str
    username: str
    password: str


class UserUpdate(schemas.BaseUserUpdate):
    id: uuid.UUID
    email: str
    username: str
    password: str


class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: str
    clicks: None
    expires_at: datetime


class LinkResponse(BaseModel):
    id: uuid.UUID
    original_url: str
    short_code: str
    clicks: int
    created_at: datetime
    expires_at: datetime


class LinkUpdate(BaseModel):
    original_url: Optional[HttpUrl] = None
    custom_alias: None
    expires_at: datetime


class LinkStatistics(BaseModel):
    original_url: str
    short_code: str
    clicks: int
    last_accessed: datetime = None
    expires_at: datetime = None


class CustomAlias(BaseModel):
    original_url: HttpUrl
    short_code: str
    custom_alias: str
    expires_at: datetime = None
    new_expires_at: datetime = None
