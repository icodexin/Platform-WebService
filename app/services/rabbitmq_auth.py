from fnmatch import fnmatchcase

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import (
    RabbitMQAuthCheckEnum,
    RabbitMQPermissionLevelEnum,
    RabbitMQResourceTypeEnum,
)
from app.dao import RabbitMQPermissionBindingDAO, UserDAO
from app.models.rabbitmq_permission_binding import RabbitMQPermissionBinding
from app.services.auth import authenticate_user

ALLOW = "allow"
DENY = "deny"


def _match_glob(pattern: str | None, value: str | None) -> bool:
    """使用 shell-style wildcard 模式匹配字符串, None 被视为不匹配任何值。"""
    if pattern is None:
        return False
    if value is None:
        return False
    return fnmatchcase(value, pattern)


def _match_topic(pattern: str | None, routing_key: str | None) -> bool:
    """使用 AMQP topic wildcard 模式匹配 routing key, None 被视为不匹配任何值。"""
    if pattern is None or routing_key is None:
        return False

    pattern_parts = pattern.split(".") if pattern else []
    key_parts = routing_key.split(".") if routing_key else []

    def matches(pi: int, ki: int) -> bool:
        while pi < len(pattern_parts):
            token = pattern_parts[pi]
            if token == "#":
                if pi == len(pattern_parts) - 1:
                    return True
                return any(matches(pi + 1, next_ki) for next_ki in range(ki, len(key_parts) + 1))
            if ki >= len(key_parts):
                return False
            if token not in {"*", key_parts[ki]}:
                return False
            pi += 1
            ki += 1
        return ki == len(key_parts)

    return matches(0, 0)


async def _get_active_user_bindings(username: str, db: AsyncSession):
    """获取用户及其绑定的 RabbitMQ 权限"""
    user = await UserDAO(db).get_user_by_unified_id(username)
    if not user or not user.is_active:
        return None, []
    bindings = await RabbitMQPermissionBindingDAO(db).get_user_bindings(user.id)
    return user, bindings


def _collect_tags(bindings: list[RabbitMQPermissionBinding]) -> list[str]:
    """收集绑定中的 RabbitMQ 标签"""
    tags = {
        binding.rabbitmq_tag.value
        for binding in bindings
        if binding.check_type == RabbitMQAuthCheckEnum.user and binding.rabbitmq_tag
    }
    return sorted(tags)


def _binding_matches_resource(
    binding: RabbitMQPermissionBinding,
    vhost: str,
    resource: RabbitMQResourceTypeEnum,
    name: str,
    permission: RabbitMQPermissionLevelEnum,
) -> bool:
    if binding.check_type != RabbitMQAuthCheckEnum.resource:
        return False
    if not _match_glob(binding.vhost_pattern, vhost):
        return False
    if binding.permission_level != permission:
        return False
    if binding.resource_type and binding.resource_type != resource:
        return False
    pattern = binding.resource_name_pattern or "*"
    return _match_glob(pattern, name)


def _binding_matches_topic(
    binding: RabbitMQPermissionBinding,
    vhost: str,
    exchange_name: str,
    permission: RabbitMQPermissionLevelEnum,
    routing_key: str,
) -> bool:
    if binding.check_type != RabbitMQAuthCheckEnum.topic:
        return False
    if not _match_glob(binding.vhost_pattern, vhost):
        return False
    if binding.permission_level != permission:
        return False
    exchange_pattern = binding.resource_name_pattern or "*"
    if not _match_glob(exchange_pattern, exchange_name):
        return False
    topic_pattern = binding.routing_key_pattern or "#"
    return _match_topic(topic_pattern, routing_key)


async def authorize_user(username: str, password: str, db: AsyncSession) -> str:
    """校验用户身份并返回可选管理标签。"""
    # 1. 验证用户身份
    user = await authenticate_user(username, password, db)
    if not user or not user.is_active:
        return DENY

    # 2. 收集用户绑定的 RabbitMQ 标签
    bindings = await RabbitMQPermissionBindingDAO(db).get_user_bindings(user.id)
    tags = _collect_tags(bindings)
    if not tags:
        return ALLOW
    return f"{ALLOW} {' '.join(tags)}"


async def authorize_vhost(username: str, vhost: str, db: AsyncSession) -> str:
    """校验用户对指定 vhost 的访问权限。"""
    # 获取用户及其绑定的权限
    _, bindings = await _get_active_user_bindings(username, db)
    # 检查是否有任何绑定的权限允许访问该 vhost
    allowed = any(
        binding.check_type == RabbitMQAuthCheckEnum.vhost and _match_glob(binding.vhost_pattern, vhost)
        for binding in bindings
    )
    return ALLOW if allowed else DENY


async def authorize_resource(
    username: str,
    vhost: str,
    resource: str,
    name: str,
    permission: str,
    db: AsyncSession,
) -> str:
    """校验用户对指定 exchange/queue 的 configure|write|read 权限。"""
    # 获取用户及其绑定的权限
    _, bindings = await _get_active_user_bindings(username, db)
    try:
        resource_type = RabbitMQResourceTypeEnum(resource)
        permission_level = RabbitMQPermissionLevelEnum(permission)
    except ValueError:
        return DENY

    # 检查是否有任何绑定的权限允许访问该资源
    allowed = any(
        _binding_matches_resource(binding, vhost, resource_type, name, permission_level)
        for binding in bindings
    )
    return ALLOW if allowed else DENY


async def authorize_topic(
    username: str,
    vhost: str,
    exchange_name: str,
    permission: str,
    routing_key: str,
    db: AsyncSession,
) -> str:
    """校验用户对指定 topic exchange 上 routing key 级别权限。"""
    # 获取用户及其绑定的权限
    _, bindings = await _get_active_user_bindings(username, db)
    try:
        permission_level = RabbitMQPermissionLevelEnum(permission)
    except ValueError:
        return DENY

    # 检查是否有任何绑定的权限允许访问该 topic exchange 和 routing key
    allowed = any(
        _binding_matches_topic(binding, vhost, exchange_name, permission_level, routing_key)
        for binding in bindings
    )
    return ALLOW if allowed else DENY
