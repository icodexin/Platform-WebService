from fastapi import Depends, HTTPException, Query, status
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import TokenTypeEnum, UserTypeEnum
from app.core.db import get_db
from app.core.security import oauth2_scheme, optional_oauth2_scheme
from app.dao import PermissionDAO, UserDAO
from app.models.user import User
from app.schemas.user import (
    AdminCreate,
    AdminResponse,
    StudentProfile,
    StudentResponse,
    TeacherProfile,
    TeacherResponse,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.services.auth import verify_token
from app.common.permissions import (
    USER_CREATE_ADMIN,
    USER_DEACTIVATE_ALL,
    USER_DEACTIVATE_SELF,
    USER_READ_ALL,
    USER_READ_SELF,
    USER_UPDATE_ALL,
    USER_UPDATE_SELF,
)


def user_list_pagination(
    page: int = Query(default=1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
):
    return page, page_size


def serialize_user(user: User) -> UserResponse:
    base_data = {
        "id": user.id,
        "user_type": user.user_type,
        "unified_id": user.unified_id,
        "name": user.name,
        "gender": user.gender,
        "birthdate": user.birthdate,
        "is_active": user.is_active,
        "roles": [role.code for role in user.roles],
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }

    if user.user_type == UserTypeEnum.student and user.student_profile:
        profile_data = StudentProfile.model_validate(user.student_profile).model_dump()
        return StudentResponse(**base_data, **profile_data)
    if user.user_type == UserTypeEnum.teacher and user.teacher_profile:
        profile_data = TeacherProfile.model_validate(user.teacher_profile).model_dump()
        return TeacherResponse(**base_data, **profile_data)
    if user.user_type == UserTypeEnum.admin:
        return AdminResponse(**base_data)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="User profile not found",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def list_users(
    page: int,
    page_size: int,
    keyword: str | None,
    user_type: UserTypeEnum | None,
    is_active: bool | None,
    db: AsyncSession,
) -> UserListResponse:
    users, total = await UserDAO(db).list_users(
        page=page,
        page_size=page_size,
        keyword=keyword,
        user_type=user_type,
        is_active=is_active,
    )
    return UserListResponse(
        items=[serialize_user(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
    )


async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = None,
) -> UserResponse:
    validated_user = TypeAdapter(UserCreate).validate_python(user)
    if isinstance(validated_user, AdminCreate):
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="创建管理员用户需要先登录",
                headers={"WWW-Authenticate": "Bearer"},
            )
        await _ensure_permission(
            current_user=current_user,
            db=db,
            permission_code=USER_CREATE_ADMIN.code,
            detail="无权限创建管理员用户",
        )

    return await _create_user_record(validated_user, db)


async def _create_user_record(user: UserCreate, db: AsyncSession) -> UserResponse:
    dao = UserDAO(db)

    existing_user = await dao.get_user_by_unified_id(user.unified_id)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已存在",
            headers={"X-Error": "User already exists"},
        )

    new_user = await dao.create_user(user)
    return serialize_user(new_user)


async def get_user_detail(user_id: int, db: AsyncSession) -> UserResponse:
    user = await _get_user_or_404(user_id=user_id, db=db)
    return serialize_user(user)


async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession,
    current_user: User | None = None,
) -> UserResponse:
    dao = UserDAO(db)
    user = await _get_user_or_404(user_id=user_id, db=db)

    user_changes = payload.get_user_data()
    if "unified_id" in user_changes and user_changes["unified_id"] != user.unified_id:
        duplicated_user = await dao.get_user_by_unified_id(user_changes["unified_id"])
        if duplicated_user and duplicated_user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="统一身份ID已存在",
            )

    if current_user and current_user.id == user.id and "is_active" in user_changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前用户不能通过更新接口修改账号状态，请使用账号注销接口",
        )

    profile_changes = _extract_profile_changes(payload=payload, user=user)
    updated_user = await dao.update_user(user=user, user_changes=user_changes, profile_changes=profile_changes)
    return serialize_user(updated_user)


async def deactivate_user(user_id: int, db: AsyncSession, current_user: User | None = None):
    user = await _get_user_or_404(user_id=user_id, db=db)
    if current_user and current_user.id == user.id:
        await UserDAO(db).deactivate_user(user)
        return
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="注销账号需要先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    await UserDAO(db).deactivate_user(user)


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


async def get_optional_current_user_entity(
    token: str | None = Depends(optional_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    可选地解析当前登录用户，允许请求不带 token, 不带 token 时返回 None.
    但如果带了 token, 就仍然会严格校验；无效 token、找不到用户、用户已停用, 都会报错
    """
    if token is None:
        return None

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

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user(current_user: User = Depends(get_current_user_entity)) -> UserResponse:
    return serialize_user(current_user)


async def get_current_active_user(current_user: UserResponse = Depends(get_current_user)):
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


async def _get_user_or_404(user_id: int, db: AsyncSession) -> User:
    user = await UserDAO(db).get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return user


async def ensure_can_read_user(target_user_id: int, current_user: User, db: AsyncSession):
    await _ensure_user_scope_permission(
        target_user_id=target_user_id,
        current_user=current_user,
        db=db,
        self_permission_code=USER_READ_SELF.code,
        all_permission_code=USER_READ_ALL.code,
        detail="无权限读取该用户信息",
    )


async def ensure_can_update_user(target_user_id: int, current_user: User, db: AsyncSession):
    await _ensure_user_scope_permission(
        target_user_id=target_user_id,
        current_user=current_user,
        db=db,
        self_permission_code=USER_UPDATE_SELF.code,
        all_permission_code=USER_UPDATE_ALL.code,
        detail="无权限修改该用户信息",
    )


def _extract_profile_changes(payload: UserUpdate, user: User) -> dict:
    student_changes = payload.get_student_profile_data()
    teacher_changes = payload.get_teacher_profile_data()

    if user.user_type == UserTypeEnum.student:
        if teacher_changes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学生用户不允许更新教师资料字段",
            )
        return student_changes

    if user.user_type == UserTypeEnum.teacher:
        if student_changes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="教师用户不允许更新学生资料字段",
            )
        return teacher_changes

    if student_changes or teacher_changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="管理员用户不存在扩展资料字段",
        )
    return {}


async def ensure_can_read_current_user(current_user: User, db: AsyncSession):
    await _ensure_user_scope_permission(
        target_user_id=current_user.id,
        current_user=current_user,
        db=db,
        self_permission_code=USER_READ_SELF.code,
        all_permission_code=USER_READ_ALL.code,
        detail="无权限读取当前用户信息",
    )


async def ensure_can_deactivate_current_user(current_user: User, db: AsyncSession):
    await _ensure_user_scope_permission(
        target_user_id=current_user.id,
        current_user=current_user,
        db=db,
        self_permission_code=USER_DEACTIVATE_SELF.code,
        all_permission_code=USER_DEACTIVATE_ALL.code,
        detail="无权限注销当前用户账号",
    )


async def ensure_can_deactivate_user(target_user_id: int, current_user: User, db: AsyncSession):
    await _ensure_user_scope_permission(
        target_user_id=target_user_id,
        current_user=current_user,
        db=db,
        self_permission_code=USER_DEACTIVATE_SELF.code,
        all_permission_code=USER_DEACTIVATE_ALL.code,
        detail="无权限注销该用户账号",
    )


async def _ensure_user_scope_permission(
    target_user_id: int,
    current_user: User,
    db: AsyncSession,
    self_permission_code: str,
    all_permission_code: str,
    detail: str,
):
    """
    确保当前用户要么是操作对象自己，要么拥有全局权限
    """
    if current_user.id != target_user_id:
        await _ensure_permission(
            current_user=current_user,
            db=db,
            permission_code=all_permission_code,
            detail=detail,
        )
        return

    has_all_permission = await PermissionDAO(db).user_has_permission(
        user_id=current_user.id,
        permission_code=all_permission_code,
    )
    if has_all_permission:
        return

    await _ensure_permission(
        current_user=current_user,
        db=db,
        permission_code=self_permission_code,
        detail=detail,
    )


async def _ensure_permission(
    current_user: User,
    db: AsyncSession,
    permission_code: str,
    detail: str,
):
    has_permission = await PermissionDAO(db).user_has_permission(
        user_id=current_user.id,
        permission_code=permission_code,
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
