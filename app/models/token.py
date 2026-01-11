import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enum import TokenTypeEnum
from app.core.db import Base

class TokenBlocklist(Base):
    """Token黑名单表"""
    __tablename__ = 'token_blocklist'

    jti: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, comment="JWT ID"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'), index=True, comment="用户ID"
    )
    token_type: Mapped[TokenTypeEnum] = mapped_column(
        Enum(TokenTypeEnum), nullable=False, comment="令牌类型"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="令牌过期时间"
    )
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, comment="令牌被撤销的时间"
    )
    revoked_reason: Mapped[str] = mapped_column(
        String(128), nullable=True, comment="令牌被撤销的原因"
    )
