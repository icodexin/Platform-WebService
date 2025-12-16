import asyncio

from dotenv import load_dotenv
load_dotenv("../.env")

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.core.database import get_db
from app.common.dao import TokenBlocklistDAO
from app.modules.auth import auth_router
from app.modules.datastream import datastream_router, data_consumer_task, WebsocketManager
from app.modules.users import users_router
from app.modules.rabbitmq import rabbitmq_router


async def remove_expired_tokens_job():
    """
    定期清理过期的令牌。
    该函数会被调度器定期调用。
    """
    async for db_session in get_db():
        await TokenBlocklistDAO.remove_expired_tokens(db_session)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    应用程序的生命周期管理器，可用于管理后台任务
    """
    # 创建任务调度器
    scheduler = AsyncIOScheduler()
    # 添加异步任务
    scheduler.add_job(
        func=remove_expired_tokens_job,
        trigger=IntervalTrigger(minutes=60),
        max_instances=1,
    )
    # 启动调度器
    scheduler.start()
    # 实例化应用级资源
    app.state.datastream_ws_mgr = WebsocketManager()
    # 创建后台任务
    app.state.tasks = [
        asyncio.create_task(data_consumer_task(app.state.datastream_ws_mgr))
    ]
    # 运行时
    yield
    # 在应用关闭时清理调度器
    scheduler.shutdown()
    # 关闭时取消后台任务
    for task in app.state.tasks:
        task.cancel()
    await asyncio.gather(*app.state.tasks, return_exceptions=True)


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.include_router(auth_router, tags=["Authentication"])
app.include_router(users_router, prefix="/api", tags=["Users"])
app.include_router(rabbitmq_router, prefix="/api/rabbitmq", tags=["RabbitMQ"])
app.include_router(datastream_router, prefix="/datastream", tags=["DataStream"])


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


@app.get("/register", response_class=HTMLResponse)
async def register():
    with open("static/register.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
