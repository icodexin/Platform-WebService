from collections.abc import Callable

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import (
    RabbitMQAuthCheckEnum,
    RabbitMQResourceTypeEnum,
)
from app.common.permissions import BUILTIN_PERMISSION_CODES
from app.core.db import get_db
from app.dao import PermissionDAO, RabbitMQPermissionBindingDAO
from app.models.permission import Permission
from app.models.rabbitmq_permission_binding import RabbitMQPermissionBinding
from app.models.user import User
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


def serialize_rabbitmq_permission_binding(
    binding: RabbitMQPermissionBinding,
) -> RabbitMQPermissionBindingResponse:
    return RabbitMQPermissionBindingResponse(
        id=binding.id,
        permission_id=binding.permission_id,
        check_type=binding.check_type,
        vhost_pattern=binding.vhost_pattern,
        resource_type=binding.resource_type,
        resource_name_pattern=binding.resource_name_pattern,
        permission_level=binding.permission_level,
        routing_key_pattern=binding.routing_key_pattern,
        rabbitmq_tag=binding.rabbitmq_tag,
        created_at=binding.created_at,
        updated_at=binding.updated_at,
    )


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


async def list_permission_rabbitmq_bindings(
    permission_id: int,
    db: AsyncSession,
) -> RabbitMQPermissionBindingListResponse:
    await _get_permission_or_404(permission_id=permission_id, db=db)
    bindings = await RabbitMQPermissionBindingDAO(db).list_permission_bindings(permission_id=permission_id)
    return RabbitMQPermissionBindingListResponse(
        items=[serialize_rabbitmq_permission_binding(binding) for binding in bindings],
        total=len(bindings),
    )


async def get_permission_rabbitmq_binding_detail(
    permission_id: int,
    binding_id: int,
    db: AsyncSession,
) -> RabbitMQPermissionBindingResponse:
    binding = await _get_permission_binding_or_404(permission_id=permission_id, binding_id=binding_id, db=db)
    return serialize_rabbitmq_permission_binding(binding)


async def create_permission_rabbitmq_binding(
    permission_id: int,
    payload: RabbitMQPermissionBindingCreate,
    db: AsyncSession,
) -> RabbitMQPermissionBindingResponse:
    await _get_permission_or_404(permission_id=permission_id, db=db)
    binding_data = payload.model_dump()
    _validate_rabbitmq_binding_data(binding_data)
    binding = await RabbitMQPermissionBindingDAO(db).create_binding(
        permission_id=permission_id,
        **binding_data,
    )
    return serialize_rabbitmq_permission_binding(binding)


async def update_permission_rabbitmq_binding(
    permission_id: int,
    binding_id: int,
    payload: RabbitMQPermissionBindingUpdate,
    db: AsyncSession,
) -> RabbitMQPermissionBindingResponse:
    binding = await _get_permission_binding_or_404(permission_id=permission_id, binding_id=binding_id, db=db)
    changes = payload.model_dump(exclude_unset=True)
    merged_data = {
        "check_type": binding.check_type,
        "vhost_pattern": binding.vhost_pattern,
        "resource_type": binding.resource_type,
        "resource_name_pattern": binding.resource_name_pattern,
        "permission_level": binding.permission_level,
        "routing_key_pattern": binding.routing_key_pattern,
        "rabbitmq_tag": binding.rabbitmq_tag,
    }
    merged_data.update(changes)
    _validate_rabbitmq_binding_data(merged_data)
    updated_binding = await RabbitMQPermissionBindingDAO(db).update_binding(binding, **changes)
    return serialize_rabbitmq_permission_binding(updated_binding)


async def delete_permission_rabbitmq_binding(
    permission_id: int,
    binding_id: int,
    db: AsyncSession,
):
    binding = await _get_permission_binding_or_404(permission_id=permission_id, binding_id=binding_id, db=db)
    await RabbitMQPermissionBindingDAO(db).delete_binding(binding)


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


async def _get_permission_binding_or_404(
    permission_id: int,
    binding_id: int,
    db: AsyncSession,
) -> RabbitMQPermissionBinding:
    binding = await RabbitMQPermissionBindingDAO(db).get_binding_by_id(binding_id)
    if not binding or binding.permission_id != permission_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RabbitMQ 权限绑定不存在",
        )
    return binding


def _validate_rabbitmq_binding_data(data: dict) -> None:
    check_type = data["check_type"]
    vhost_pattern = data.get("vhost_pattern")
    resource_type = data.get("resource_type")
    resource_name_pattern = data.get("resource_name_pattern")
    permission_level = data.get("permission_level")
    routing_key_pattern = data.get("routing_key_pattern")
    rabbitmq_tag = data.get("rabbitmq_tag")

    if not vhost_pattern:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="vhost_pattern 不能为空",
        )

    if check_type == RabbitMQAuthCheckEnum.user:
        _ensure_fields_empty(
            {
                "resource_type": resource_type,
                "resource_name_pattern": resource_name_pattern,
                "permission_level": permission_level,
                "routing_key_pattern": routing_key_pattern,
            }
        )
        return

    if check_type == RabbitMQAuthCheckEnum.vhost:
        _ensure_fields_empty(
            {
                "resource_type": resource_type,
                "resource_name_pattern": resource_name_pattern,
                "permission_level": permission_level,
                "routing_key_pattern": routing_key_pattern,
                "rabbitmq_tag": rabbitmq_tag,
            }
        )
        return

    if check_type == RabbitMQAuthCheckEnum.resource:
        if permission_level is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="resource 类型绑定必须提供 permission_level",
            )
        if resource_name_pattern is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="resource 类型绑定必须提供 resource_name_pattern",
            )
        _ensure_fields_empty(
            {
                "routing_key_pattern": routing_key_pattern,
                "rabbitmq_tag": rabbitmq_tag,
            }
        )
        return

    if check_type == RabbitMQAuthCheckEnum.topic:
        if permission_level is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="topic 类型绑定必须提供 permission_level",
            )
        if resource_name_pattern is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="topic 类型绑定必须提供 resource_name_pattern",
            )
        if routing_key_pattern is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="topic 类型绑定必须提供 routing_key_pattern",
            )
        if rabbitmq_tag is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="topic 类型绑定不允许设置 rabbitmq_tag",
            )
        if resource_type not in (None, RabbitMQResourceTypeEnum.topic):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="topic 类型绑定的 resource_type 仅允许为空或 topic",
            )
        return

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="不支持的 RabbitMQ 绑定类型",
    )


def _ensure_fields_empty(fields: dict[str, object | None]) -> None:
    invalid_fields = [field_name for field_name, value in fields.items() if value is not None]
    if invalid_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前绑定类型不允许设置字段: {', '.join(invalid_fields)}",
        )


def _ensure_permission_mutable(permission: Permission):
    if permission.code in BUILTIN_PERMISSION_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统内置权限不允许修改或删除",
        )
