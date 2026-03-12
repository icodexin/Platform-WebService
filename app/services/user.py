from fastapi import Depends, HTTPException, status
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import TokenTypeEnum
from app.core.db import get_db
from app.core.security import oauth2_scheme
from app.dao import UserDAO
from app.models.user import User
from app.schemas.user import (AdminResponse, StudentCreate, StudentProfile, StudentResponse, TeacherCreate,
                              TeacherProfile, TeacherResponse, UserCreate, UserOut, UserResponse)
from app.services.auth import verify_token


async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
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


async def get_current_user_entity(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = await verify_token(token, TokenTypeEnum.access, db=db)
    uid = int(payload.get("sub")) if payload else None
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await UserDAO(db).get_user_by_id(uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user(current_user: User = Depends(get_current_user_entity)) -> UserResponse:
    # 获取基础用户数据
    user_data = UserOut.model_validate(current_user)

    # 根据用户类型加载对应的 profile
    if current_user.user_type == "student" and current_user.student_profile:
        profile = current_user.student_profile
        profile_data = StudentProfile.model_validate(profile)
        return StudentResponse(**user_data.model_dump(), **profile_data.model_dump())
    elif current_user.user_type == "teacher" and current_user.teacher_profile:
        profile = current_user.teacher_profile
        profile_data = TeacherProfile.model_validate(profile)
        return TeacherResponse(**user_data.model_dump(), **profile_data.model_dump())
    elif current_user.user_type == "admin":
        return AdminResponse(**user_data.model_dump())
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User profile not found",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_activate_user(current_user: UserResponse = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def get_current_active_user_entity(current_user: User = Depends(get_current_user_entity)):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user
