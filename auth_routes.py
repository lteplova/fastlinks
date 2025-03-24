from fastapi import APIRouter, Depends
from auth.users import auth_backend, get_current_user, fastapi_users
from auth.schemas import UserCreate, UserRead, UserUpdate
from auth.db import User

router = APIRouter()

# роуты для аутентификации
router.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# эндпоинты для защищенных маршрутов
@router.get("/authenticated-route")
async def authenticated_route(user: User = Depends(get_current_user)):
    return {"message": f"Hello {user.email}!"}

@router.get("/protected-route")
async def protected_route(user: User = Depends(get_current_user)):
    return f"Hello, {user.username}"

@router.get("/unprotected-route")
async def unprotected_route():
    return "Hello, anonym"
