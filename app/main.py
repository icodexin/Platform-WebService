from contextlib import asynccontextmanager

from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.api import auth_router, users_router
from app.core import settings, get_db
from app.dao import TokenBlocklistDAO

async def remove_expired_tokens_job():
    """清理过期令牌"""
    async for db_session in get_db():
        await TokenBlocklistDAO(db_session).remove_expired_tokens()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行的代码
    scheduler = AsyncIOScheduler()
    scheduler.add_job(remove_expired_tokens_job, "interval", hours=1)
    scheduler.start()

    # 运行时
    yield

    # 关闭时执行的代码
    scheduler.shutdown()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

app.include_router(auth_router, tags=["Authentication"])
app.include_router(users_router, prefix="/api", tags=["Users"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
