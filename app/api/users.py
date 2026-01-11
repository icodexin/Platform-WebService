from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.services.user import create_user, get_current_activate_user

router = APIRouter(prefix="/users")

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(new_user: UserCreate, db: AsyncSession = Depends(get_db)):
    """创建新用户"""
    try:
        created_user = await create_user(new_user, db)
        return {"detail": "User created successfully"}
    except HTTPException as e:
        raise e

@router.get("/me", response_model=UserResponse)
async def read_current_user_endpoint(current_user: User = Depends(get_current_activate_user)):
    """获取当前登录用户的信息"""
    return current_user