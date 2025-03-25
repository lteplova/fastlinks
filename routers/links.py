from fastapi import APIRouter, HTTPException, Depends, status, Query
from datetime import datetime, timezone
import redis
from auth.db import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import RedirectResponse
from typing import List
from pydantic import HttpUrl
from auth.schemas import LinkCreate, LinkUpdate, LinkResponse, LinkStatistics, CustomAlias
from dateutil.relativedelta import relativedelta
from services import (create_short_url, delete_short_url, update_short_url, get_original_url,
                      update_link_statistics, get_link_stats, create_custom_short, check_alias_uniq, search_short)
from auth.users import get_current_user
from config import REDIS_HOST, REDIS_PORT
from cache import get_cached_url, create_cache_url,delete_cached_link


router = APIRouter()

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

@router.post("/shorten",
             summary="Создать короткую ссылку",
             description="Этот эндпоинт создает короткую ссылку на основе предоставленного оригинального URL.",
             response_description="Возвращает информацию о созданной короткой ссылке.",
             response_model=LinkResponse)
async def shorten_link(
        link: LinkCreate,
        db: AsyncSession = Depends(get_async_session),
        current_user=Depends(get_current_user)
):
    cached_data = get_cached_url(link.custom_alias, redis_client)

    if cached_data:
        return LinkResponse(
            id=None,
            original_url=cached_data['original_url'],
            short_code=cached_data['short_code'],
            clicks=cached_data['clicks'],
            created_at=None,
            expires_at=cached_data['expires_at'],
        )
    expires_at = link.expires_at.replace(tzinfo=timezone.utc) + relativedelta(months=1)


    short_url = await create_short_url(
        db,
        original_url=str(link.original_url),
        user_id=current_user.id,
        alias=link.custom_alias,
        expires_at=expires_at
    )


    create_cache_url(
        short_url.short_code,
        short_url.original_url,
        short_url.clicks,
        short_url.expires_at,
        redis_client
    )

    return LinkResponse(
        id=short_url.id,
        original_url=short_url.original_url,
        short_code=short_url.short_code,
        clicks=short_url.clicks,
        created_at=short_url.created_at,
        expires_at=short_url.expires_at,
    )





@router.put("/{short_code}",
            summary="Обновление короткой ссылки",
            description="Этот эндпоинт генерирует новую короткую ссылку для оригинального URL",
            response_model=LinkResponse)
async def update_link(
        short_code: str,
        link_update: LinkUpdate,
        db: AsyncSession = Depends(get_async_session),
        current_user=Depends(get_current_user)
):
    expires_at = link_update.expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    min_expiry = datetime.now(timezone.utc) + relativedelta(months=1)
    if expires_at is None or expires_at < min_expiry:
        expires_at = min_expiry

    updated_link = await update_short_url(
        db,
        short_code,
        current_user.id,
        original_url=str(link_update.original_url) if link_update.original_url else None,
        new_short_code=link_update.custom_alias,
        expires_at=expires_at
    )

    delete_cached_link(short_code, redis_client)

    create_cache_url(
        updated_link.short_code,
        updated_link.original_url,
        updated_link.clicks,
        updated_link.expires_at,
        redis_client
    )

    return LinkResponse(
        id=updated_link.id,
        original_url=updated_link.original_url,
        short_code=updated_link.short_code,
        clicks=updated_link.clicks,
        created_at=updated_link.created_at,
        expires_at=updated_link.expires_at,
    )

@router.get("/{short_code}/stats",
            summary="Вывод статистики использования короткой ссылки",
            description="Этот эндпоинт показывает сколько раз кликали на короткую ссылку и время последнего клика",
            response_model=LinkStatistics)

async def get_link_statistics(
        short_code: str,
        db: AsyncSession = Depends(get_async_session)
):
    cached = get_cached_url(short_code, redis_client)

    if cached:
        return LinkStatistics(
            original_url=cached['original_url'],
            short_code=cached['short_code'],
            clicks=cached['clicks'],
            last_accessed=cached['last_accessed'],
            expires_at=cached['expires_at']
        )
    else:
        stats = await get_link_stats(db, short_code)

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ссылка с кодом '{short_code}' не найдена"
            )
        if stats.clicks == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Не было переходов"
            )

        return LinkStatistics(
            original_url=stats.original_url,
            short_code=stats.short_code,
            clicks=stats.clicks,
            last_accessed=stats.last_accessed,
            expires_at=stats.expires_at
        )

@router.post("/shorten/custom",
             summary="Изменение короткой ссылки и времени",
             description="Этот эндпоинт позволяет задать кастомный алиас для ссылки и изменить время жизни существующей ссылки",
             response_model=LinkResponse)

async def create_custom_link(
        link: CustomAlias,
        db: AsyncSession = Depends(get_async_session),
        current_user=Depends(get_current_user)
):
    if link.custom_alias == "string":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Для создания кастомной ссылки необходимо указать алиас"
        )

    if not link.custom_alias:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Для создания кастомной ссылки необходимо указать алиас"
        )

    is_unique = await check_alias_uniq(db, link.custom_alias)

    if not is_unique:
        if link.new_expires_at != link.expires_at:
            expires_at = link.new_expires_at.replace(tzinfo=timezone.utc)
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
            )
    else:
        expires_at = None
        if link.expires_at:
            expires_at = link.expires_at.replace(tzinfo=timezone.utc) + relativedelta(months=1)
        else:
            expires_at = datetime.now(timezone.utc) + relativedelta(months=1)

    short_url = await create_custom_short(
        db,
        original_url=str(link.original_url),
        user_id=current_user.id,
        custom_alias=link.custom_alias,
        expires_at=expires_at
    )

    delete_cached_link(link.short_code, redis_client)

    create_cache_url(short_url.custom_alias, short_url.original_url, 0, short_url.expires_at, redis_client)

    return LinkResponse(
        id=short_url.id,
        original_url=short_url.original_url,
        short_code=short_url.short_code,
        clicks=short_url.clicks,
        created_at=short_url.created_at,
        expires_at=short_url.expires_at,
    )


@router.get("/search",
            summary="Поиск короткой ссылки",
            description="Этот эндпоинт позволяет найти короткую ссылку в БД по оригинальному URL",
            response_model=List[LinkResponse])
async def search_by_url(
        url: HttpUrl = Query(..., description="Оригинальный URL для поиска"),
        # current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session),

):

    links = await search_short(db, str(url))

    if not links:
        raise HTTPException(status_code=404, detail="Ссылки не найдены")

    response = [
        LinkResponse(
            id=link.id,
            original_url=link.original_url,
            short_code=link.short_code,
            clicks=link.clicks,
            created_at=link.created_at,
            expires_at=link.expires_at,
        )
        for link in links
    ]

    return response

@router.get("/{short_code}",
            summary="Перенаправить на оригинальный адрес",
            description="Этот эндпоинт перенаправляет на оригинальный URL по указанной короткой ссылке",
            )
async def redirect_to_original(
        short_code: str,
        db: AsyncSession = Depends(get_async_session),
):
    # проверка кэша
    cached_url = get_cached_url(short_code, redis_client)
    now = datetime.now(timezone.utc)

    if cached_url:
        create_cache_url(short_code, cached_url['original_url'], cached_url['clicks']+1, cached_url['expires_at'], redis_client, now)
        await update_link_statistics(db, short_code)
        return RedirectResponse(url=cached_url['original_url'])
    else:
        link = await get_original_url(db, short_code)

        if not link:
            raise HTTPException(status_code=404, detail="Ссылка не найдена")

        if not link.expires_at:
            if link.created_at:
                expiration_date = link.created_at + relativedelta(months=1)
                if now > expiration_date:
                    raise HTTPException(status_code=410, detail="Срок действия ссылки истек")
        elif link.expires_at < now:
            raise HTTPException(status_code=410, detail="Срок действия ссылки истек")

        await update_link_statistics(db, link.short_code)

        create_cache_url(short_code, link.original_url, link.clicks, link.expires_at, redis_client, now)

        return RedirectResponse(url=link.original_url)


@router.delete("/{short_code}",
               summary="Удаление ссылки",
               description="Этот эндпоинт удаляет короткую ссылку",
               status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
        short_code: str,
        db: AsyncSession = Depends(get_async_session),
        current_user=Depends(get_current_user)
):
    deleted = await delete_short_url(db, short_code, current_user.id)

    if deleted:
        delete_cached_link(short_code, redis_client)
        return None


    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Произошла неизвестная ошибка при удалении ссылки"
    )
