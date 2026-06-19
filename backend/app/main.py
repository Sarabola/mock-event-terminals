from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import router
from backend.app.core.config import get_settings
from backend.app.db.session import AsyncSessionLocal
from backend.app.services.bootstrap import create_db_schema, seed_defaults


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_schema()
    async with AsyncSessionLocal() as session:
        await seed_defaults(session)
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
