from fastapi import FastAPI
from contextlib import asynccontextmanager
from auth.db import create_db_and_tables
from routers.auth_routes import router as auth_router
from routers.links import router as links_router
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# маршруты аутентификации
app.include_router(auth_router)
app.include_router(links_router, prefix="/links", tags=["links"])

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8000, log_level="debug")
