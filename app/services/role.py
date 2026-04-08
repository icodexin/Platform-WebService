from fastapi import HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao import RoleDAO
from app.models.role import Role
from app.schemas.role import (
    RoleCreate,
    RoleListResponse,
    RolePermissionBindingUpdate,
    RolePermissionSummary,
    RoleResponse,
    RoleUpdate,
)

BUILTIN_ROLE_CODES = frozenset({"admin", "teacher", "student"})
ADMIN_ROLE_CODE = "admin"


def serialize_role(role: Role) -> RoleResponse:
    permissions = [
        RolePermissionSummary.model_validate(permission)
        for permission in sorted(role.permissions, key=lambda item: item.id)
    ]
    return RoleResponse(
        id=role.id,
        code=role.code,
        name=role.name,
        permissions=permissions,
        permission_count=len(role.permissions),
        user_count=len(role.users),
        is_system=role.code in BUILTIN_ROLE_CODES,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


def role_list_pagination(
    page: int = Query(default=1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
):
    return page, page_size


async def list_roles(
    page: int,
    page_size: int,
    keyword: str | None,
    db: AsyncSession,
) -> RoleListResponse:
    roles, total = await RoleDAO(db).list_roles(page=page, page_size=page_size, keyword=keyword)
    return RoleListResponse(
        items=[serialize_role(role) for role in roles],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_role_detail(role_id: int, db: AsyncSession) -> RoleResponse:
    role = await _get_role_or_404(role_id=role_id, db=db)
    return serialize_role(role)


async def create_role(payload: RoleCreate, db: AsyncSession) -> RoleResponse:
    dao = RoleDAO(db)
    existing_role = await dao.get_role_by_code(payload.code)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色编码已存在",
        )

    permissions = await _resolve_permissions(permission_ids=payload.permission_ids, db=db)
    created_role = await dao.create_role(code=payload.code, name=payload.name, permissions=permissions)
    return serialize_role(created_role)


async def update_role(role_id: int, payload: RoleUpdate, db: AsyncSession) -> RoleResponse:
    dao = RoleDAO(db)
    role = await _get_role_or_404(role_id=role_id, db=db)
    updates = payload.model_dump(exclude_unset=True, exclude={"permission_ids"})
    if updates:
        _ensure_role_basic_fields_mutable(role)
        if "code" in updates and updates["code"] != role.code:
            duplicated_role = await dao.get_role_by_code(updates["code"])
            if duplicated_role and duplicated_role.id != role.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="角色编码已存在",
                )

    permissions = None
    if payload.permission_ids is not None:
        _ensure_role_permission_bindings_mutable(role)
        permissions = await _resolve_permissions(permission_ids=payload.permission_ids, db=db)

    updated_role = await dao.update_role(role=role, permissions=permissions, **updates)
    return serialize_role(updated_role)


async def delete_role(role_id: int, db: AsyncSession):
    role = await _get_role_or_404(role_id=role_id, db=db)
    _ensure_role_deletable(role)
    if role.users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色已绑定用户，请先解除绑定后再删除",
        )

    await RoleDAO(db).delete_role(role)


async def _get_role_or_404(role_id: int, db: AsyncSession) -> Role:
    role = await RoleDAO(db).get_role_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在",
        )
    return role


async def _resolve_permissions(permission_ids: list[int], db: AsyncSession):
    normalized_ids = list(dict.fromkeys(permission_ids))
    permissions = await RoleDAO(db).get_permissions_by_ids(normalized_ids)
    if len(permissions) != len(normalized_ids):
        existing_ids = {permission.id for permission in permissions}
        missing_ids = [permission_id for permission_id in normalized_ids if permission_id not in existing_ids]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"权限不存在: {missing_ids}",
        )
    return permissions


async def get_role_permission_bindings(role_id: int, db: AsyncSession) -> RoleResponse:
    role = await _get_role_or_404(role_id=role_id, db=db)
    return serialize_role(role)


async def update_role_permission_bindings(
    role_id: int,
    payload: RolePermissionBindingUpdate,
    db: AsyncSession,
) -> RoleResponse:
    role = await _get_role_or_404(role_id=role_id, db=db)
    _ensure_role_permission_bindings_mutable(role)
    permissions = await _resolve_permissions(permission_ids=payload.permission_ids, db=db)
    updated_role = await RoleDAO(db).update_role(role=role, permissions=permissions)
    return serialize_role(updated_role)


def _ensure_role_basic_fields_mutable(role: Role):
    if role.code in BUILTIN_ROLE_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统内置角色不允许修改基础信息",
        )


def _ensure_role_permission_bindings_mutable(role: Role):
    if role.code == ADMIN_ROLE_CODE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="管理员内置角色不允许修改权限绑定",
        )


def _ensure_role_deletable(role: Role):
    if role.code in BUILTIN_ROLE_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统内置角色不允许删除",
        )
