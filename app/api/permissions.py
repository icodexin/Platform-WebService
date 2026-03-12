from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.permissions import PERMISSION_MANAGE
from app.core import get_db
from app.schemas.permission import PermissionCreate, PermissionListResponse, PermissionResponse, PermissionUpdate
from app.services.permission import (
    create_permission,
    delete_permission,
    get_permission_detail,
    list_permissions,
    permission_list_pagination,
    require_permission,
    update_permission,
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
