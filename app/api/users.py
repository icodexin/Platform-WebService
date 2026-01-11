from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.services.user import create_user

router = APIRouter(prefix="/users")

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(new_user: dict, db: AsyncSession = Depends(get_db)):
    """创建新用户"""
    try:
        created_user = await create_user(new_user, db)
        return {"message": "User created successfully"}
    except HTTPException as e:
        raise e