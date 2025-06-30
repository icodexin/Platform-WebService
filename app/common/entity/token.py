import uuid

from sqlalchemy import Column, String, DateTime, UUID, Enum, ForeignKey, TypeDecorator
from sqlalchemy.dialects.mysql import BINARY

from app.core.database import Base


class BinaryUUIDType(TypeDecorator):
    impl = BINARY(16)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value.bytes
        return uuid.UUID(value).bytes

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(bytes=value)


class TokenBlocklist(Base):
    __tablename__ = "token_blocklist"
    jti = Column(BinaryUUIDType, primary_key=True, index=True)  # 唯一标识
    user_id = Column(String(20), ForeignKey("users.user_id", ondelete='CASCADE', onupdate='CASCADE'))  # 用户ID
    token_type = Column(Enum("access", "refresh", name="token_type_enum"), nullable=False)  # 令牌类型
    expires_at = Column(DateTime, index=True, nullable=False)  # 令牌过期时间
    revoked_reason = Column(String(255), nullable=True)  # 撤销原因
