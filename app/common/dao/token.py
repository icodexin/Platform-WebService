from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.common.entity import TokenBlocklist


class TokenBlocklistDAO:
    @staticmethod
    async def add_to_blocklist(db: AsyncSession, jti: str, user_id: str, token_type: str, expires_at: datetime,
                               revoked_reason: str = None):
        try:
            token = TokenBlocklist(
                jti=jti,
                user_id=user_id,
                token_type=token_type,
                expires_at=expires_at,
                revoked_reason=revoked_reason
            )
            db.add(token)
            await db.commit()
            await db.refresh(token)
            return token
        except Exception as e:
            await db.rollback()
            raise e

    @staticmethod
    async def is_token_revoked(db: AsyncSession, jti: str):
        token = await db.get(TokenBlocklist, jti)
        return token is not None

    @staticmethod
    async def remove_expired_tokens(db: AsyncSession):
        """
        删除所有已过期的令牌。
        :param db: 数据库会话
        """
        try:
            now = datetime.now()
            stmt = delete(TokenBlocklist).where(TokenBlocklist.expires_at < now)
            await db.execute(stmt)
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise e