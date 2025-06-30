from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import UserCreate
from app.core.database import get_db
from app.common.dao import UserDAO


async def create_student(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await UserDAO.get_user_by_user_id(db, user_data.user_id)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
            headers={"X-Error": "Username already exists"}
        )

    new_user = await UserDAO.create_user(db, user_data, 3)
    return new_user

