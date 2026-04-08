from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.permissions import ROLE_MANAGE
from app.core import get_db
from app.schemas.role import (
    RoleCreate,
    RoleListResponse,
    RolePermissionBindingUpdate,
    RoleResponse,
    RoleUpdate,
)
from app.services.permission import require_permission
from app.services.role import (
    create_role,
    delete_role,
    get_role_detail,
    get_role_permission_bindings,
    list_roles,
    role_list_pagination,
    update_role,
    update_role_permission_bindings,
)

router = APIRouter(
    prefix="/roles",
    dependencies=[Depends(require_permission(ROLE_MANAGE.code))],
)


@router.get("/", response_model=RoleListResponse)
async def list_roles_endpoint(
    pagination: Annotated[tuple[int, int], Depends(role_list_pagination)],
    keyword: str | None = Query(default=None, max_length=128, description="按角色编码或名称模糊检索"),
    db: AsyncSession = Depends(get_db),
):
    """分页查询角色列表"""
    page, page_size = pagination
    return await list_roles(page=page, page_size=page_size, keyword=keyword, db=db)


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role_endpoint(
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建角色"""
    return await create_role(payload=payload, db=db)


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role_endpoint(
    role_id: int,
    db: AsyncSession = Depends(get_db),
):
    """查询角色详情"""
    return await get_role_detail(role_id=role_id, db=db)


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role_endpoint(
    role_id: int,
    payload: RoleUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新角色"""
    return await update_role(role_id=role_id, payload=payload, db=db)


@router.delete("/{role_id}", response_model=dict)
async def delete_role_endpoint(
    role_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除角色"""
    await delete_role(role_id=role_id, db=db)
    return {"detail": "Role deleted successfully"}


@router.get("/{role_id}/permissions", response_model=RoleResponse)
async def get_role_permission_bindings_endpoint(
    role_id: int,
    db: AsyncSession = Depends(get_db),
):
    """查询角色当前绑定的权限列表"""
    return await get_role_permission_bindings(role_id=role_id, db=db)


@router.put("/{role_id}/permissions", response_model=RoleResponse)
async def update_role_permission_bindings_endpoint(
    role_id: int,
    payload: RolePermissionBindingUpdate,
    db: AsyncSession = Depends(get_db),
):
    """整体覆盖角色的权限绑定"""
    return await update_role_permission_bindings(role_id=role_id, payload=payload, db=db)
