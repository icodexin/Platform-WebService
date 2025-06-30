from datetime import datetime

from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dao import UserDAO, TokenBlocklistDAO
from app.core.config import settings
from app.core.database.base import get_db
from app.core.security import verify_password, oauth2_scheme


async def verify_token(token: str, token_type: str, verify_revoked: bool = True, db: AsyncSession = Depends(get_db)):
    """
    解码并验证 JWT 令牌的有效性和类型。
    :param token: JWT 令牌字符串
    :param token_type: 期望的令牌类型（"access" 或 "refresh"）
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
        # 如果需要，检查令牌是否被撤销
        if verify_revoked and await TokenBlocklistDAO.is_token_revoked(db, payload.get("jti")):
            return None

        return payload
    except JWTError as e:
        print(e)
        return None


async def revoke_token(jti: str, user_id: str, token_type: str, expires_at: datetime, revoked_reason: str = None,
                       db: AsyncSession = Depends(get_db)):
    """
    撤销令牌。
    :param jti: JWT ID，用于唯一标识令牌
    :param user_id: 用户 ID
    :param token_type: 令牌类型（"access" 或 "refresh"）
    :param expires_at: 令牌过期时间
    :param revoked_reason: 撤销原因
    :param db: 数据库会话
    :return: 被撤销的令牌实体
    """
    return await TokenBlocklistDAO.add_to_blocklist(db, jti, user_id, token_type, expires_at, revoked_reason)


async def authenticate_user(user_id: str, password: str, db: AsyncSession = Depends(get_db)):
    """
    验证用户凭据。
    :param user_id: 用户 ID（学号或工号）
    :param password: 用户密码
    :param db: 数据库会话
    :return: 用户实体或 None
    """
    user = await UserDAO.get_user_by_user_id(db, user_id)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def update_login_info(user_id: str, last_login_ip: str, last_login_time: datetime, db: AsyncSession = Depends(get_db)):
    """
    更新用户的最后登录信息。
    :param user_id: 用户 ID
    :param last_login_ip: 最后登录 IP 地址
    :param last_login_time: 最后登录时间
    :param db: 数据库会话
    :return: 更新后的用户实体
    """
    return await UserDAO.update_login_info(db, user_id, last_login_ip, last_login_time)


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    payload = await verify_token(token, "access", db=db)
    if not payload:
        raise credentials_exception

    user = await UserDAO.get_user_by_user_id(db, payload["sub"])
    if not user:
        raise credentials_exception

    return user
