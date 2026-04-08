from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.permissions import PERMISSION_MANAGE
from app.core import get_db
from app.schemas.permission import (
    PermissionCreate,
    PermissionListResponse,
    PermissionResponse,
    PermissionUpdate,
    RabbitMQPermissionBindingCreate,
    RabbitMQPermissionBindingListResponse,
    RabbitMQPermissionBindingResponse,
    RabbitMQPermissionBindingUpdate,
)
from app.services.permission import (
    create_permission,
    create_permission_rabbitmq_binding,
    delete_permission,
    delete_permission_rabbitmq_binding,
    get_permission_detail,
    get_permission_rabbitmq_binding_detail,
    list_permissions,
    list_permission_rabbitmq_bindings,
    permission_list_pagination,
    require_permission,
    update_permission,
    update_permission_rabbitmq_binding,
)

router = APIRouter(
    prefix="/permissions",
    dependencies=[Depends(require_permission(PERMISSION_MANAGE.code))],  # 访问权限管理接口自身需要"权限管理权限"
)


@router.get("/", response_model=PermissionListResponse)
async def list_permissions_endpoint(
    pagination: Annotated[tuple[int, int], Depends(permission_list_pagination)],
    keyword: str | None = Query(default=None, max_length=128, description="按权限编码或名称模糊检索"),
    db: AsyncSession = Depends(get_db),
):
    """分页查询权限列表"""
    page, page_size = pagination
    return await list_permissions(page=page, page_size=page_size, keyword=keyword, db=db)


@router.post("/", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission_endpoint(
    payload: PermissionCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建权限"""
    return await create_permission(payload=payload, db=db)


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission_endpoint(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
):
    """查询权限详情"""
    return await get_permission_detail(permission_id=permission_id, db=db)


@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission_endpoint(
    permission_id: int,
    payload: PermissionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新权限"""
    return await update_permission(permission_id=permission_id, payload=payload, db=db)


@router.delete("/{permission_id}", response_model=dict)
async def delete_permission_endpoint(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除权限"""
    await delete_permission(permission_id=permission_id, db=db)
    return {"detail": "Permission deleted successfully"}


@router.get("/{permission_id}/rabbitmq-bindings", response_model=RabbitMQPermissionBindingListResponse)
async def list_permission_rabbitmq_bindings_endpoint(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
):
    """查询指定权限的 RabbitMQ 权限绑定列表"""
    return await list_permission_rabbitmq_bindings(permission_id=permission_id, db=db)


@router.post(
    "/{permission_id}/rabbitmq-bindings",
    response_model=RabbitMQPermissionBindingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_permission_rabbitmq_binding_endpoint(
    permission_id: int,
    payload: RabbitMQPermissionBindingCreate,
    db: AsyncSession = Depends(get_db),
):
    """为指定权限创建 RabbitMQ 权限绑定"""
    return await create_permission_rabbitmq_binding(permission_id=permission_id, payload=payload, db=db)


@router.get("/{permission_id}/rabbitmq-bindings/{binding_id}", response_model=RabbitMQPermissionBindingResponse)
async def get_permission_rabbitmq_binding_endpoint(
    permission_id: int,
    binding_id: int,
    db: AsyncSession = Depends(get_db),
):
    """查询指定权限下的 RabbitMQ 权限绑定详情"""
    return await get_permission_rabbitmq_binding_detail(
        permission_id=permission_id,
        binding_id=binding_id,
        db=db,
    )


@router.put("/{permission_id}/rabbitmq-bindings/{binding_id}", response_model=RabbitMQPermissionBindingResponse)
async def update_permission_rabbitmq_binding_endpoint(
    permission_id: int,
    binding_id: int,
    payload: RabbitMQPermissionBindingUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新指定权限下的 RabbitMQ 权限绑定"""
    return await update_permission_rabbitmq_binding(
        permission_id=permission_id,
        binding_id=binding_id,
        payload=payload,
        db=db,
    )


@router.delete("/{permission_id}/rabbitmq-bindings/{binding_id}", response_model=dict)
async def delete_permission_rabbitmq_binding_endpoint(
    permission_id: int,
    binding_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除指定权限下的 RabbitMQ 权限绑定"""
    await delete_permission_rabbitmq_binding(permission_id=permission_id, binding_id=binding_id, db=db)
    return {"detail": "RabbitMQ permission binding deleted successfully"}
