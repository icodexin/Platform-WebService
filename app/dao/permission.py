from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user_role import UserRole


class PermissionDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_permissions(self, user_id: int):
        result = await self.db.execute(
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id)
            .distinct()
        )
        return result.scalars().all()

    async def user_has_permission(self, user_id: int, permission_code: str) -> bool:
        result = await self.db.execute(
            select(Permission.id)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id, Permission.code == permission_code)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def list_permissions(self, page: int, page_size: int, keyword: str | None = None):
        filters = []
        if keyword:
            # code 和 name 字段模糊匹配, 使用 ILIKE 实现不区分大小写的模糊搜索
            pattern = f"%{keyword.strip()}%"
            filters.append(or_(Permission.code.ilike(pattern), Permission.name.ilike(pattern)))

        # 查询当前页的数据
        list_stmt = select(Permission).options(selectinload(Permission.roles))
        # 查询总记录数
        total_stmt = select(func.count()).select_from(Permission)

        if filters:
            list_stmt = list_stmt.where(*filters)
            total_stmt = total_stmt.where(*filters)

        # 优先按照创建时间倒序, 如果创建时间相同则按照 ID 倒序, 确保分页时数据顺序稳定
        list_stmt = list_stmt.order_by(Permission.created_at.desc(), Permission.id.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size)

        result = await self.db.execute(list_stmt)
        total = await self.db.scalar(total_stmt)
        return result.scalars().all(), total or 0

    async def get_permission_by_id(self, permission_id: int):
        result = await self.db.execute(
            select(Permission)
            .options(selectinload(Permission.roles))
            .where(Permission.id == permission_id)
        )
        return result.scalars().first()

    async def get_permission_by_code(self, code: str):
        result = await self.db.execute(
            select(Permission)
            .options(selectinload(Permission.roles))
            .where(Permission.code == code)
        )
        return result.scalars().first()

    async def create_permission(self, code: str, name: str):
        try:
            permission = Permission(code=code, name=name)
            self.db.add(permission)
            await self.db.commit()
            await self.db.refresh(permission)
            return await self.get_permission_by_id(permission.id)
        except Exception:
            await self.db.rollback()
            raise

    async def update_permission(self, permission: Permission, **changes):
        try:
            for field, value in changes.items():
                setattr(permission, field, value)
            await self.db.commit()
            await self.db.refresh(permission)
            return await self.get_permission_by_id(permission.id)
        except Exception:
            await self.db.rollback()
            raise

    async def delete_permission(self, permission: Permission):
        try:
            await self.db.delete(permission)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
