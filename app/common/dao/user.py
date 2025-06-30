from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.common.entity import UserModel, RoleModel, UserRole
from app.common.schemas import UserCreate
from app.core.security import get_password_hash


class UserDAO:
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate, role_id: int, create_by: str = "sys_service"):
        try:
            hashed_password = get_password_hash(user_data.password)
            new_user = UserModel(
                **user_data.model_dump(exclude={"password"}), hashed_password=hashed_password,
                created_by=create_by, updated_by=create_by
            )
            user_role = UserRole(user_id=new_user.user_id, role_id=role_id, created_by=create_by, updated_by=create_by)
            db.add(new_user)
            db.add(user_role)
            await db.commit()
            await db.refresh(new_user)
            await db.refresh(user_role)
            return new_user
        except Exception as e:
            await db.rollback()
            raise e

    @staticmethod
    async def update_login_info(db: AsyncSession, user_id: str, last_login_ip: str, last_login_at: datetime):
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.user_id == user_id)
                .values(last_login_ip=last_login_ip, last_login_at=last_login_at, updated_by="sys_service")
                .execution_options(synchronize_session="fetch")
            )
            await db.execute(stmt)
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise e

    @staticmethod
    async def get_user_by_user_id(db: AsyncSession, user_id: str):
        return await db.get(UserModel, user_id)

    @staticmethod
    async def get_role_by_role_name(db: AsyncSession, role_name: str):
        result = await db.execute(
            select(RoleModel).filter(RoleModel.role_name == role_name)
        )
        return result.scalars().first()

    @staticmethod
    async def get_role_by_user_id(db: AsyncSession, user_id: str):
        result = await db.execute(
            select(RoleModel).join(UserRole).filter(UserRole.user_id == user_id)
        )
        return result.scalars().first()
