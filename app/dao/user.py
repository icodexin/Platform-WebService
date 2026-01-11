from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.role import Role
from app.models.user import StudentProfile, TeacherProfile, User
from app.models.user_role import UserRole
from app.schemas.user import StudentCreate, TeacherCreate


class UserDAO:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_id(self, id: int):
        return await self.db.get(User, id)
    
    async def get_user_by_unified_id(self, unified_id: str):
        result = await self.db.execute(
            select(User).filter(User.unified_id == unified_id)
        )
        return result.scalars().first()
    
    async def get_role_by_code(self, role_code: str):
        result = await self.db.execute(
            select(Role).filter(Role.code == role_code)
        )
        return result.scalars().first()
    
    async def create_student(self, student: StudentCreate):
        try:
            # 1. 创建用户
            user = User(**student.get_user_data())
            self.db.add(user)
            await self.db.flush()  # 确保 user.id 可用

            # 2. 创建学生档案
            profile = StudentProfile(user_id=user.id, **student.get_profile_data())
            self.db.add(profile)

            # 3. 分配学生角色
            role = await self.get_role_by_code("student")
            if not role:
                raise ValueError("学生角色不存在")
            user_role = UserRole(user_id=user.id, role_id=role.id)
            self.db.add(user_role)

            # 4. 提交事务
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception as e:
            await self.db.rollback()
            raise e
    
    async def create_teacher(self, teacher: TeacherCreate):
        try:
            # 1. 创建用户
            user = User(**teacher.get_user_data())
            self.db.add(user)
            await self.db.flush()  # 确保 user.id 可用

            # 2. 创建教师档案
            profile = TeacherProfile(user_id=user.id, **teacher.get_profile_data())
            self.db.add(profile)

            # 3. 分配教师角色
            role = await self.get_role_by_code("teacher")
            if not role:
                raise ValueError("教师角色不存在")
            user_role = UserRole(user_id=user.id, role_id=role.id)
            self.db.add(user_role)

            # 4. 提交事务
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception as e:
            await self.db.rollback()
            raise e