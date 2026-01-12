import sys
import uuid
from datetime import datetime

from fastapi import Depends
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
