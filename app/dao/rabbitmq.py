from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rabbitmq_permission_binding import RabbitMQPermissionBinding
from app.models.role_permission import RolePermission
from app.models.user_role import UserRole


class RabbitMQPermissionBindingDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_bindings(self, user_id: int):
        result = await self.db.execute(
            select(RabbitMQPermissionBinding)
            .join(RolePermission, RolePermission.permission_id == RabbitMQPermissionBinding.permission_id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id)
            .distinct()
        )
        return result.scalars().all()
