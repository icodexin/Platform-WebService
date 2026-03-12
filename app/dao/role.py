from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.permission import Permission
from app.models.role import Role


class RoleDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_roles(self, page: int, page_size: int, keyword: str | None = None):
        filters = []
        if keyword:
            pattern = f"%{keyword.strip()}%"
            filters.append(or_(Role.code.ilike(pattern), Role.name.ilike(pattern)))

        list_stmt = select(Role).options(
            selectinload(Role.permissions),
            selectinload(Role.users),
        )
        total_stmt = select(func.count()).select_from(Role)

        if filters:
            list_stmt = list_stmt.where(*filters)
            total_stmt = total_stmt.where(*filters)

        list_stmt = list_stmt.order_by(Role.created_at.desc(), Role.id.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size)

        result = await self.db.execute(list_stmt)
        total = await self.db.scalar(total_stmt)
        return result.scalars().all(), total or 0

    async def get_role_by_id(self, role_id: int):
        result = await self.db.execute(
            select(Role)
            .options(
                selectinload(Role.permissions),
                selectinload(Role.users),
            )
            .where(Role.id == role_id)
        )
        return result.scalars().first()

    async def get_role_by_code(self, code: str):
        result = await self.db.execute(
            select(Role)
            .options(
                selectinload(Role.permissions),
                selectinload(Role.users),
            )
            .where(Role.code == code)
        )
        return result.scalars().first()

    async def get_permissions_by_ids(self, permission_ids: list[int]) -> list[Permission]:
        if not permission_ids:
            return []

        result = await self.db.execute(
            select(Permission)
            .where(Permission.id.in_(permission_ids))
            .order_by(Permission.id.asc())
        )
        return result.scalars().all()

    async def create_role(self, code: str, name: str, permissions: list[Permission]):
        try:
            role = Role(code=code, name=name, permissions=permissions)
            self.db.add(role)
            await self.db.commit()
            await self.db.refresh(role)
            return await self.get_role_by_id(role.id)
        except Exception:
            await self.db.rollback()
            raise

    async def update_role(self, role: Role, permissions: list[Permission] | None = None, **changes):
        try:
            for field, value in changes.items():
                setattr(role, field, value)
            if permissions is not None:
                role.permissions = permissions
            await self.db.commit()
            await self.db.refresh(role)
            return await self.get_role_by_id(role.id)
        except Exception:
            await self.db.rollback()
            raise

    async def delete_role(self, role: Role):
        try:
            await self.db.delete(role)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
