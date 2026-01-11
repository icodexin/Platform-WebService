from fastapi import Depends, HTTPException, status
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.user import UserDAO
from app.schemas.user import StudentCreate, TeacherCreate, UserCreate

async def create_user(user: UserCreate, db: AsyncSession):
    user = TypeAdapter(UserCreate).validate_python(user)
    dao = UserDAO(db)

    existing_user = await dao.get_user_by_unified_id(user.unified_id)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已存在",
            headers={"X-Error": "User already exists"}
        )

    if isinstance(user, StudentCreate):
        new_user = await dao.create_student(user)
    elif isinstance(user, TeacherCreate):
        new_user = await dao.create_teacher(user)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户类型",
            headers={"X-Error": "Invalid user type"}
        )

    return new_user