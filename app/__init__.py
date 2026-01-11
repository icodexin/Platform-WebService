# 确保所有模型在应用启动时被导入，以便 SQLAlchemy 能够正确识别关系
from app.models import (
    User,
    StudentProfile,
    TeacherProfile,
    Role,
    Permission,
    UserRole,
    RolePermission,
)
