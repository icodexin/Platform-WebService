from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BuiltinPermission:
    code: str
    name: str


PERMISSION_MANAGE = BuiltinPermission(
    code="sys.permission.manage",
    name="权限管理",
)

MESSAGING_BROKER_MANAGE = BuiltinPermission(
    code="cap.messaging.broker.manage",
    name="消息代理管理",
)

BUILTIN_PERMISSIONS = (
    PERMISSION_MANAGE,
    MESSAGING_BROKER_MANAGE,
)

BUILTIN_PERMISSION_CODES = frozenset(permission.code for permission in BUILTIN_PERMISSIONS)
