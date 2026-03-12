from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BuiltinPermission:
    code: str
    name: str


PERMISSION_MANAGE = BuiltinPermission(
    code="sys.permission.manage",
    name="权限管理",
)

USER_READ_SELF = BuiltinPermission(
    code="sys.user.read.self",
    name="读取当前用户",
)

USER_READ_ALL = BuiltinPermission(
    code="sys.user.read.all",
    name="读取全部用户",
)

USER_UPDATE_SELF = BuiltinPermission(
    code="sys.user.update.self",
    name="修改当前用户",
)

USER_UPDATE_ALL = BuiltinPermission(
    code="sys.user.update.all",
    name="修改全部用户",
)

USER_DEACTIVATE_SELF = BuiltinPermission(
    code="sys.user.deactivate.self",
    name="注销当前用户账号",
)

USER_DEACTIVATE_ALL = BuiltinPermission(
    code="sys.user.deactivate.all",
    name="注销全部用户账号",
)

USER_CREATE_ADMIN = BuiltinPermission(
    code="sys.user.create.admin",
    name="创建管理员用户",
)

MESSAGING_BROKER_MANAGE = BuiltinPermission(
    code="cap.messaging.broker.manage",
    name="消息代理管理",
)

BUILTIN_PERMISSIONS = (
    PERMISSION_MANAGE,
    USER_READ_SELF,
    USER_READ_ALL,
    USER_UPDATE_SELF,
    USER_UPDATE_ALL,
    USER_DEACTIVATE_SELF,
    USER_DEACTIVATE_ALL,
    USER_CREATE_ADMIN,
    MESSAGING_BROKER_MANAGE,
)

BUILTIN_PERMISSION_CODES = frozenset(permission.code for permission in BUILTIN_PERMISSIONS)
