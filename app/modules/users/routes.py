from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import UserCreate
from app.core.database import get_db
from app.modules.users.services import create_student

router = APIRouter(prefix="/users")


@router.post("/student", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_student_endpoint(new_user: UserCreate, db: AsyncSession = Depends(get_db)):
    """创建新用户"""
    try:
        created_user = await create_student(new_user, db)
        return {"message": "User created successfully", "user_id": created_user.user_id}
    except HTTPException as e:
        raise e
