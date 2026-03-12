import datetime as dt
import uuid

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import TokenTypeEnum
from app.models.token import TokenBlocklist


class TokenBlocklistDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(
        self,
        jti: uuid.UUID,
        user_id: int,
        token_type: TokenTypeEnum,
        expires_at: dt.datetime,
        revoked_reason: str = None
    ):
        try:
            token = TokenBlocklist(
                jti=jti,
                user_id=user_id,
                token_type=token_type,
                expires_at=expires_at,
                revoked_reason=revoked_reason
            )
            self.db.add(token)
            await self.db.commit()
            await self.db.refresh(token)
            return token
        except Exception as e:
            await self.db.rollback()
            raise e

    async def is_token_revoked(self, jti: str) -> bool:
        token = await self.db.get(TokenBlocklist, jti)
        return token is not None
    
    async def remove_expired_tokens(self):
        try:
            now = dt.datetime.now(dt.timezone.utc)
            stmt = delete(TokenBlocklist).where(TokenBlocklist.expires_at < now)
            await self.db.execute(stmt)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise e
