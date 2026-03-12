from collections.abc import Callable

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.permissions import BUILTIN_PERMISSION_CODES
from app.core.db import get_db
from app.dao import PermissionDAO
from app.models.permission import Permission
from app.models.user import User
from app.schemas.permission import (
    PermissionCreate,
    PermissionListResponse,
    PermissionResponse,
    PermissionUpdate,
)
from app.services.user import get_current_active_user_entity


def serialize_permission(permission: Permission) -> PermissionResponse:
    return PermissionResponse(
        id=permission.id,
        code=permission.code,
        name=permission.name,
        role_count=len(permission.roles),
        is_system=permission.code in BUILTIN_PERMISSION_CODES,
        created_at=permission.created_at,
        updated_at=permission.updated_at,
    )


def permission_list_pagination(
    page: int = Query(default=1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
):
    return page, page_size


async def list_permissions(
    page: int,
    page_size: int,
    keyword: str | None,
    db: AsyncSession,
) -> PermissionListResponse:
    permissions, total = await PermissionDAO(db).list_permissions(
        page=page,
        page_size=page_size,
        keyword=keyword,
    )
    return PermissionListResponse(
        items=[serialize_permission(permission) for permission in permissions],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_permission_detail(permission_id: int, db: AsyncSession) -> PermissionResponse:
    permission = await _get_permission_or_404(permission_id=permission_id, db=db)
    return serialize_permission(permission)


async def create_permission(payload: PermissionCreate, db: AsyncSession) -> PermissionResponse:
    dao = PermissionDAO(db)
    existing_permission = await dao.get_permission_by_code(payload.code)
    if existing_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="权限编码已存在",
        )

    created_permission = await dao.create_permission(code=payload.code, name=payload.name)
    return serialize_permission(created_permission)


async def update_permission(
    permission_id: int,
    payload: PermissionUpdate,
    db: AsyncSession,
) -> PermissionResponse:
    dao = PermissionDAO(db)
    permission = await _get_permission_or_404(permission_id=permission_id, db=db)
    _ensure_permission_mutable(permission)

    updates = payload.model_dump(exclude_unset=True)
    if "code" in updates and updates["code"] != permission.code:
        duplicated_permission = await dao.get_permission_by_code(updates["code"])
        if duplicated_permission and duplicated_permission.id != permission.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="权限编码已存在",
            )

    updated_permission = await dao.update_permission(permission, **updates)
    return serialize_permission(updated_permission)


async def delete_permission(permission_id: int, db: AsyncSession):
    permission = await _get_permission_or_404(permission_id=permission_id, db=db)
    _ensure_permission_mutable(permission)
    if permission.roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="权限已绑定角色，请先解除绑定后再删除",
        )

    await PermissionDAO(db).delete_permission(permission)


def require_permission(permission_code: str) -> Callable:
    async def dependency(
        current_user: User = Depends(get_current_active_user_entity),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        has_permission = await PermissionDAO(db).user_has_permission(
            user_id=current_user.id,
            permission_code=permission_code,
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问该接口",
            )
        return current_user

    return dependency


async def _get_permission_or_404(permission_id: int, db: AsyncSession) -> Permission:
    permission = await PermissionDAO(db).get_permission_by_id(permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在",
        )
    return permission


def _ensure_permission_mutable(permission: Permission):
    if permission.code in BUILTIN_PERMISSION_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统内置权限不允许修改或删除",
        )
