from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import UserTypeEnum
from app.common.permissions import USER_READ_ALL
from app.core import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services.permission import require_permission
from app.services.user import (
    ensure_can_deactivate_current_user,
    ensure_can_deactivate_user,
    ensure_can_read_current_user,
    create_user,
    deactivate_user,
    ensure_can_read_user,
    ensure_can_update_user,
    get_current_active_user_entity,
    get_current_user,
    get_optional_current_user_entity,
    get_user_detail,
    list_users,
    update_user,
    user_list_pagination,
)

router = APIRouter(prefix="/users")


@router.get("/", response_model=UserListResponse)
async def list_users_endpoint(
    pagination: Annotated[tuple[int, int], Depends(user_list_pagination)],
    keyword: str | None = Query(default=None, max_length=128, description="按统一身份ID或姓名模糊检索"),
    user_type: UserTypeEnum | None = Query(default=None, description="按用户类型筛选"),
    is_active: bool | None = Query(default=None, description="按账号状态筛选"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(USER_READ_ALL.code)),
):
    """分页查询用户列表"""
    page, page_size = pagination
    return await list_users(
        page=page,
        page_size=page_size,
        keyword=keyword,
        user_type=user_type,
        is_active=is_active,
        db=db,
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    new_user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user_entity),
):
    """创建新用户"""
    return await create_user(new_user, db=db, current_user=current_user)


@router.get("/me", response_model=UserResponse)
async def read_current_user_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_entity),
):
    """获取当前登录用户的信息"""
    await ensure_can_read_current_user(current_user=current_user, db=db)
    return await get_current_user(current_user=current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_entity),
):
    """获取用户详情"""
    await ensure_can_read_user(target_user_id=user_id, current_user=current_user, db=db)
    return await get_user_detail(user_id=user_id, db=db)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_entity),
):
    """更新用户"""
    await ensure_can_update_user(target_user_id=user_id, current_user=current_user, db=db)
    return await update_user(user_id=user_id, payload=payload, db=db, current_user=current_user)


@router.post("/me/deactivate", response_model=dict)
async def deactivate_current_user_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_entity),
):
    """注销当前用户账号"""
    await ensure_can_deactivate_current_user(current_user=current_user, db=db)
    await deactivate_user(user_id=current_user.id, db=db, current_user=current_user)
    return {"detail": "User account deactivated successfully"}


@router.post("/{user_id}/deactivate", response_model=dict)
async def deactivate_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_entity),
):
    """注销指定用户账号"""
    await ensure_can_deactivate_user(target_user_id=user_id, current_user=current_user, db=db)
    await deactivate_user(user_id=user_id, db=db, current_user=current_user)
    return {"detail": "User account deactivated successfully"}
