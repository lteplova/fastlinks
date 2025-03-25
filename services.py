import random
import string
import uuid
from sqlalchemy import update
from urllib.parse import unquote
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from models.models import Link

import logging
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    short_code = ''.join(random.choice(characters) for _ in range(length))
    return short_code


async def create_short_url(db, original_url, user_id, alias=None, expires_at=None):
    created_at = datetime.now(timezone.utc)
    if expires_at is None:
        expires_at = created_at + relativedelta(months=1)

    if alias == "string":
        alias = None
    new_url = Link(
        original_url=original_url,
        short_code=generate_short_code() if not alias else alias,
        custom_alias=alias,
        user_id=user_id,
        created_at=created_at,
        expires_at=expires_at
    )
    db.add(new_url)

    try:
        await db.commit()
        await db.refresh(new_url)
        return new_url

    except IntegrityError as e:
        await db.rollback()
        error_message = str(e.orig)

        if "links_short_code_key" in error_message or "links_custom_alias_key" in error_message:
            if alias:
                raise  HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Такая ссылка '{alias}' уже существует"
            )

            raise Exception("Short code collision, please try again.")

        raise Exception(f"Failed to create short URL: {error_message}") from e


async def get_original_url(db: AsyncSession, short_code: str) -> Link:
    result = await db.execute(select(Link).where(Link.short_code == short_code))
    return result.scalars().first()



async def update_link_statistics(db: AsyncSession, short_code: str):
    now = datetime.now(timezone.utc)

    now_naive = now.replace(tzinfo=None)

    query = (
        update(Link)
        .where(Link.short_code == short_code)
        .values(
            clicks=Link.clicks + 1,
            last_accessed=now_naive
        )
    )

    await db.execute(query)
    await db.commit()


async def delete_short_url(db: AsyncSession, short_code: str, user_id: uuid.UUID):
    # проверка существует ли ссылка с таким кодом
    result = await db.execute(select(Link).where(Link.short_code == short_code))
    url = result.scalars().first()

    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ссылка с кодом '{short_code}' не найдена"
        )
    # проверка принадлежит ли ссылка пользователю
    if url.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на удаление этой ссылки"
        )

    await db.delete(url)
    await db.commit()

    return True


async def update_short_url(
        db: AsyncSession,
        short_code: str,
        user_id: uuid.UUID,
        original_url: str = None,
        alias=None,
        new_short_code: str = None,
        expires_at: datetime = None
):
    result = await db.execute(select(Link).where(Link.short_code == short_code))
    old_link = result.scalars().first()

    if not old_link:
        raise HTTPException(status_code=404, detail=f"Ссылка с кодом '{short_code}' не найдена")

    if old_link.user_id != user_id:
        raise HTTPException(status_code=403, detail="У вас нет прав на обновление этой ссылки")

    await db.delete(old_link)
    await db.flush()

    created_at = datetime.now(timezone.utc)

    if expires_at is None:
        expires_at = created_at + relativedelta(months=1)
    else:
        expires_at = expires_at + relativedelta(months=1)

    final_original_url = original_url if original_url is not None else old_link.original_url
    new_short_code = generate_short_code()

    new_link = Link(
        original_url=final_original_url,
        short_code=new_short_code if not alias else alias,
        custom_alias=alias,
        user_id=user_id,
        created_at=created_at,
        expires_at=expires_at,
        clicks=0
    )

    db.add(new_link)

    try:
        await db.commit()
        await db.refresh(new_link)
        return new_link
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Не удалось создать новую ссылку: {str(e.orig)}"
        )


async def get_link_stats(db: AsyncSession, short_code: str) -> Link:
    result = await db.execute(select(Link).where(Link.short_code == short_code))
    link = result.scalars().all()
    return link


async def check_alias_uniq(db: AsyncSession, alias: str) -> bool:
    result = await db.execute(select(Link).where(Link.short_code == alias))
    existing = result.scalars().first()
    return existing is None


async def create_custom_short(
        db: AsyncSession,
        original_url: str,
        user_id: uuid.UUID,
        custom_alias: str,
        expires_at: datetime
) -> Link:
    created_at = datetime.now(timezone.utc)

    existing_link = await db.execute(
        select(Link).filter(Link.custom_alias == custom_alias)
    )
    existing_link = existing_link.scalar_one_or_none()

    if existing_link:
        if existing_link.expires_at == expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Алиас '{custom_alias}' уже используется с текущей датой истечения."
            )

        existing_link.original_url = original_url
        existing_link.user_id = user_id
        existing_link.expires_at = expires_at

        try:
            await db.commit()
            await db.refresh(existing_link)
            return existing_link

        except IntegrityError as e:
            await db.rollback()
            raise Exception(f"Не удалось обновить короткую ссылку: {str(e.orig)}") from e

    new_url = Link(
        original_url=original_url,
        short_code=custom_alias,
        custom_alias=custom_alias,
        user_id=user_id,
        created_at=created_at,
        expires_at=expires_at
    )

    db.add(new_url)

    try:
        await db.commit()
        await db.refresh(new_url)
        return new_url


    except IntegrityError as e:
        await db.rollback()
        error_message = str(e.orig)

        if "links_short_code_key" in error_message or "links_custom_alias_key" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Алиас '{custom_alias}' уже используется"
            )
        raise Exception(f"Не удалось создать короткую ссылку: {error_message}") from e


async def search_short(db: AsyncSession, original_url: str) -> Link:
    decoded_url = unquote(original_url)
    result = await db.execute(select(Link).where(Link.original_url == decoded_url))
    return result.scalars().all()
