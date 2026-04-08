import sys
import uuid
from datetime import datetime

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import TokenTypeEnum
from app.core import get_db, settings
from app.core.security import verify_password
from app.dao import TokenBlocklistDAO, UserDAO


async def authenticate_user(unified_id: str, password: str, db: AsyncSession = Depends(get_db)):
    """
    验证用户凭据
    :param unified_id: 统一身份ID (学号/工号)
    :param password: 用户密码
    :param db: 数据库会话
    :return: 用户实体或 None
    """
    user = await UserDAO(db).get_user_by_unified_id(unified_id)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def normalize_bearer_token(token: str | None) -> str:
    """兼容 ``Bearer <token>`` 和原始 token 两种输入格式。"""
    candidate = (token or "").strip()
    if not candidate:
        return ""
    if candidate.lower().startswith("bearer "):
        return candidate[7:].strip()
    return candidate


def looks_like_jwt(token: str | None) -> bool:
    """做轻量格式判断，避免把普通密码直接送进 JWT 解码逻辑。"""
    candidate = normalize_bearer_token(token)
    parts = candidate.split(".")
    return len(parts) == 3 and all(parts)


async def authenticate_user_by_access_token(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    使用 access token 解析并返回当前用户。
    仅在 token 看起来像 JWT 时才尝试解码。
    """
    normalized_token = normalize_bearer_token(token)
    if not looks_like_jwt(normalized_token):
        return None

    payload = await verify_token(normalized_token, TokenTypeEnum.access, db=db)
    if not payload:
        return None

    subject = payload.get("sub")
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        return None

    user = await UserDAO(db).get_user_by_id(user_id)
    if not user or not user.is_active:
        return None
    return user


def ensure_user_is_active(user) -> None:
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_active_user_by_id(user_id: int | str, db: AsyncSession):
    user = await UserDAO(db).get_user_by_id(int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    ensure_user_is_active(user)
    return user


async def verify_token(
    token: str,
    token_type: TokenTypeEnum,
    verify_revoked: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    解码并验证 JWT 令牌的有效性和类型
    :param token: JWT 令牌字符串
    :param token_type: 期望的令牌类型 (``access`` 或 ``refresh``)
    :param verify_revoked: 是否检查令牌是否被撤销
    :param db: 数据库会话
    :return: 解码后的 JWT 负载
    """
    try:
        # 解码 JWT 令牌
        payload = jwt.decode(token, settings.TOKEN_KEY, algorithms=[settings.ENCRYPTION_ALGORITHM])
        # 检查令牌类型
        if payload.get("type") != token_type:
            return None
        # 检查令牌是否被撤销
        if verify_revoked and await TokenBlocklistDAO(db).is_token_revoked(payload.get("jti")):
            return None

        return payload
    except JWTError as e:
        print(e, file=sys.stderr)
        return None


async def revoke_token(
    jti: str | uuid.UUID,
    user_id: int | str,
    token_type: TokenTypeEnum,
    expires_at: datetime,
    revoked_reason: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    撤销令牌
    :param jti: JWT ID, 用于唯一标识令牌
    :param user_id: 用户 ID
    :param token_type: 令牌类型 (``access`` 或 ``refresh``)
    :param expires_at: 令牌过期时间
    :param revoked_reason: 撤销原因
    :param db: 数据库会话
    :return: 被撤销的令牌实体
    """
    return await TokenBlocklistDAO(db).add(uuid.UUID(jti), int(user_id), token_type, expires_at, revoked_reason)
