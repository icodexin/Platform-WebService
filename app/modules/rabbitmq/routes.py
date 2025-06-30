from fastapi import APIRouter, status, Form, Depends, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dao import UserDAO
from app.core.database import get_db
from app.modules.auth.services import authenticate_user

router = APIRouter()


# https://github.com/rabbitmq/rabbitmq-server/tree/v3.13.x/deps/rabbitmq_auth_backend_http

@router.post("/auth/user", status_code=status.HTTP_200_OK)
async def auth_user(username: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    """RabbitMQ用户认证"""
    user = await authenticate_user(user_id=username, password=password, db=db)
    if user:
        role = await UserDAO.get_role_by_user_id(db, user_id=username)
        if role and "ADMIN" in role.role_name:
            # 如果是管理员，允许访问和管理
            return Response(content="allow management", media_type="text/plain")
        else:
            # 普通用户, 允许有限访问
            return Response(content="allow", media_type="text/plain")
    else:
        return Response(content="deny", media_type="text/plain")


@router.post("/auth/vhost")
async def auth_vhost(request: Request):
    # vhost 认证规则（可自定义）
    # print(await request.form())
    return Response(content="allow", media_type="text/plain")


@router.post("/auth/resource")
async def auth_resource(request: Request):
    # 资源访问控制，例如：
    # {username: "alice", resource: "exchange", name: "logs", permission: "read"}
    # print(await request.form())
    return Response(content="allow", media_type="text/plain")


@router.post("/auth/topic")
async def auth_topic(request: Request):
    # Topic 权限控制（topic exchange）
    # print(await request.form())
    return Response(content="allow", media_type="text/plain")
