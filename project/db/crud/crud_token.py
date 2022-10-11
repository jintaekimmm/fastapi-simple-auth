from datetime import datetime

from sqlalchemy import delete, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.token import Token
from schemas.token import InsertTokenSchema


class RefreshTokenDAL:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self,
                  user_id: int,
                  access_token: str) -> Token:
        """
        사용자 refreshToken을 조회한다
        """
        q = select(Token) \
            .where(Token.user_id == user_id) \
            .where(Token.access_token == access_token)
        result = await self.session.execute(q)

        return result.scalars().first()

    async def exists(self,
                     user_id: int,
                     access_token: str) -> bool:
        """
        사용자 refreshToken이 존재하는지 조회한다
        """
        exists_criteria = (
            select(Token.user_id).
            where(Token.user_id == user_id).
            where(Token.access_token == access_token).
            exists()
        )
        q = select(Token.user_id).where(exists_criteria)
        result = await self.session.execute(q)

        return bool(result.all())

    async def delete(self,
                     user_id: int,
                     access_token: str) -> None:
        """
        사용자의 refreshToken을 삭제한다
        """
        q = delete(Token) \
            .where(Token.user_id == user_id) \
            .where(Token.access_token == access_token) \
            .execution_options(synchronize_session="fetch")

        await self.session.execute(q)

    async def insert(self, refresh_token: InsertTokenSchema):
        q = insert(Token).values(**refresh_token.dict())

        await self.session.execute(q)

    async def update(self,
                     user_id: int,
                     old_access_token: str,
                     new_access_token: str,
                     expires_at: datetime):
        """
        사용자의 token 정보를 업데이트한다
         - refreshToken 'expires_at'을 현재시간 기준으로 업데이트
         - accessToken 값을 신규로 token 값으로 업데이트
        """
        q = update(Token) \
            .where(Token.user_id == user_id,
                   Token.access_token == old_access_token) \
            .values(access_token=new_access_token,
                    expires_at=expires_at) \
            .execution_options(synchronize_session="fetch")

        await self.session.execute(q)
