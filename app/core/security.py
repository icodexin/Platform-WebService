import uuid
from datetime import datetime, timedelta, timezone

from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import settings

pwd_context = PasswordHash((
    Argon2Hasher(),
))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)


def create_token(data: dict, token_type: str, expires_delta: timedelta, expire_at : datetime = None):
    """
    创建 JWT 令牌。
    :param data: 包含用户信息的字典
    :param token_type: 令牌类型（``access`` 或 ``refresh``）
    :param expires_delta: 时间增量，表示令牌的有效期
    :param expire_at: 可选的过期时间，如果提供则覆盖 ``expires_delta``
    :return: JWT 令牌字符串
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = expire_at if expire_at else now + expires_delta
    to_encode.update({
        "jti": str(uuid.uuid4()),
        "iat": now.timestamp(),
        "exp": expire.timestamp(),
        "type": token_type
    })
    return jwt.encode(to_encode, settings.TOKEN_KEY, algorithm=settings.ENCRYPTION_ALGORITHM)


def create_access_token(user_id: str, expires_delta: timedelta = None, expire_at: datetime = None):
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_token({"sub": user_id}, "access", expires_delta, expire_at)


def create_refresh_token(user_id: str, expires_delta: timedelta = None, expire_at: datetime = None):
    if expires_delta is None:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_token({"sub": user_id}, "refresh", expires_delta, expire_at)
