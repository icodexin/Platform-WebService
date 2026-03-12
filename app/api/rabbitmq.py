from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.services.rabbitmq_auth import (
    authorize_resource,
    authorize_topic,
    authorize_user,
    authorize_vhost,
)

router = APIRouter(prefix="/auth")

# RabbitMQ HTTP auth backend:
# https://github.com/rabbitmq/rabbitmq-server/tree/v3.13.x/deps/rabbitmq_auth_backend_http


@router.post("/user", response_class=PlainTextResponse, status_code=status.HTTP_200_OK)
async def auth_user(
    username: str = Form(...),
    password: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    """校验用户对 RabbitMQ 的访问权限"""
    return await authorize_user(username=username, password=password, db=db)


@router.post("/vhost", response_class=PlainTextResponse, status_code=status.HTTP_200_OK)
async def auth_vhost(
    username: str = Form(...),
    vhost: str = Form(...),
    ip: str = Form("", alias="ip"),
    db: AsyncSession = Depends(get_db),
):
    """校验用户对指定 vhost 的访问权限"""
    _ = ip
    return await authorize_vhost(username=username, vhost=vhost, db=db)


@router.post("/resource", response_class=PlainTextResponse, status_code=status.HTTP_200_OK)
async def auth_resource(
    username: str = Form(...),
    vhost: str = Form(...),
    resource: str = Form(...),
    name: str = Form(...),
    permission: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """校验用户对 exchange/queue 级 configure|write|read 权限"""
    return await authorize_resource(
        username=username,
        vhost=vhost,
        resource=resource,
        name=name,
        permission=permission,
        db=db,
    )


@router.post("/topic", response_class=PlainTextResponse, status_code=status.HTTP_200_OK)
async def auth_topic(
    username: str = Form(...),
    vhost: str = Form(...),
    resource: str = Form("topic"),
    name: str = Form(...),
    permission: str = Form(...),
    routing_key: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """校验用户 topic exchange 上 routing key 级别权限"""
    _ = resource
    return await authorize_topic(
        username=username,
        vhost=vhost,
        exchange_name=name,
        permission=permission,
        routing_key=routing_key,
        db=db,
    )
