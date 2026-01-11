# 导入所有模型以确保 SQLAlchemy 能够正确识别它们
from app.models.user import User, StudentProfile, TeacherProfile
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission
from app.models.token import TokenBlocklist

__all__ = [
    "User",
    "StudentProfile", 
    "TeacherProfile",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "TokenBlocklist",
]
