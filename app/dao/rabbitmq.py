from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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

    async def list_permission_bindings(self, permission_id: int):
        result = await self.db.execute(
            select(RabbitMQPermissionBinding)
            .options(selectinload(RabbitMQPermissionBinding.permission))
            .where(RabbitMQPermissionBinding.permission_id == permission_id)
            .order_by(RabbitMQPermissionBinding.created_at.asc(), RabbitMQPermissionBinding.id.asc())
        )
        return result.scalars().all()

    async def get_binding_by_id(self, binding_id: int):
        result = await self.db.execute(
            select(RabbitMQPermissionBinding)
            .options(selectinload(RabbitMQPermissionBinding.permission))
            .where(RabbitMQPermissionBinding.id == binding_id)
        )
        return result.scalars().first()

    async def create_binding(self, **data):
        try:
            binding = RabbitMQPermissionBinding(**data)
            self.db.add(binding)
            await self.db.commit()
            await self.db.refresh(binding)
            return await self.get_binding_by_id(binding.id)
        except Exception:
            await self.db.rollback()
            raise

    async def update_binding(self, binding: RabbitMQPermissionBinding, **changes):
        try:
            for field, value in changes.items():
                setattr(binding, field, value)
            await self.db.commit()
            await self.db.refresh(binding)
            return await self.get_binding_by_id(binding.id)
        except Exception:
            await self.db.rollback()
            raise

    async def delete_binding(self, binding: RabbitMQPermissionBinding):
        try:
            await self.db.delete(binding)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
