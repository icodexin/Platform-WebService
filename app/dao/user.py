from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.enums import UserTypeEnum
from app.models.role import Role
from app.models.user import StudentProfile, TeacherProfile, User
from app.models.user_role import UserRole
from app.schemas.user import AdminCreate, StudentCreate, TeacherCreate, UserCreate


class UserDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, uid: int):
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.roles),
                selectinload(User.student_profile),
                selectinload(User.teacher_profile),
            )
            .where(User.id == uid)
        )
        return result.scalars().first()

    async def get_user_by_unified_id(self, unified_id: str):
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.roles),
                selectinload(User.student_profile),
                selectinload(User.teacher_profile),
            )
            .where(User.unified_id == unified_id)
        )
        return result.scalars().first()

    async def get_role_by_code(self, role_code: str):
        result = await self.db.execute(select(Role).where(Role.code == role_code))
        return result.scalars().first()

    async def get_roles_by_ids(self, role_ids: list[int]):
        if not role_ids:
            return []
        result = await self.db.execute(
            select(Role).where(Role.id.in_(role_ids)).order_by(Role.id.asc())
        )
        return result.scalars().all()

    async def get_user_roles(self, user_id: int):
        result = await self.db.execute(select(Role).join(UserRole).where(UserRole.user_id == user_id))
        return result.scalars().all()

    async def list_users(
        self,
        page: int,
        page_size: int,
        keyword: str | None = None,
        user_type: UserTypeEnum | None = None,
        is_active: bool | None = None,
    ):
        # 构建动态过滤条件
        filters = []
        normalized_keyword = keyword.strip() if keyword else None
        if normalized_keyword:
            pattern = f"%{normalized_keyword}%"
            filters.append(or_(User.unified_id.ilike(pattern), User.name.ilike(pattern)))
        if user_type is not None:
            filters.append(User.user_type == user_type)
        if is_active is not None:
            filters.append(User.is_active == is_active)

        # 当前页数据查询
        list_stmt = select(User).options(
            selectinload(User.roles),
            selectinload(User.student_profile),
            selectinload(User.teacher_profile),
        )
        # 总记录数查询
        total_stmt = select(func.count()).select_from(User)

        if filters:
            list_stmt = list_stmt.where(*filters)
            total_stmt = total_stmt.where(*filters)

        # 优先按照创建时间倒序, 如果创建时间相同则按照 ID 倒序, 确保分页时数据顺序稳定
        list_stmt = list_stmt.order_by(User.created_at.desc(), User.id.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size)

        result = await self.db.execute(list_stmt)
        total = await self.db.scalar(total_stmt)
        return result.scalars().all(), total or 0

    async def create_user(self, user: UserCreate):
        try:
            # 1. 创建 User 实例并保存到数据库
            new_user = User(**user.get_user_data())
            self.db.add(new_user)
            await self.db.flush()
            user_id = new_user.id
            
            # 2. 根据用户类型创建对应的扩展资料
            if isinstance(user, StudentCreate):
                self.db.add(StudentProfile(user_id=user_id, **user.get_profile_data()))
            elif isinstance(user, TeacherCreate):
                self.db.add(TeacherProfile(user_id=user_id, **user.get_profile_data()))
            elif isinstance(user, AdminCreate):
                pass
            else:
                raise ValueError("不支持的用户类型")

            # 3. 为用户分配默认角色
            role = await self.get_role_by_code(user.user_type.value)
            if not role:
                raise ValueError("用户角色不存在")
            self.db.add(UserRole(user_id=user_id, role_id=role.id))

            await self.db.commit()
            return await self.get_user_by_id(user_id)
        except Exception:
            await self.db.rollback()
            raise

    async def update_user(self, user: User, user_changes: dict, profile_changes: dict):
        try:
            user_id = user.id
            for field, value in user_changes.items():
                setattr(user, field, value)

            if profile_changes:
                if user.user_type == UserTypeEnum.student:
                    profile = user.student_profile
                elif user.user_type == UserTypeEnum.teacher:
                    profile = user.teacher_profile
                else:
                    profile = None

                if profile is None:
                    raise ValueError("当前用户类型不存在可更新的扩展资料")
                for field, value in profile_changes.items():
                    setattr(profile, field, value)

            await self.db.commit()
            return await self.get_user_by_id(user_id)
        except Exception:
            await self.db.rollback()
            raise

    async def deactivate_user(self, user: User):
        try:
            user.is_active = False
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def replace_user_roles(self, user: User, roles: list[Role]):
        try:
            user_id = user.id
            user.roles = roles
            await self.db.commit()
            return await self.get_user_by_id(user_id)
        except Exception:
            await self.db.rollback()
            raise
