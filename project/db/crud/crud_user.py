from sqlalchemy import insert
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from schemas.auth import SignUpBaseSchema


class UserDAL:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_users(self):
        """
        모든 사용자 정보를 반환한다
        """
        q = select(User.id,
                   User.email,
                   User.mobile,
                   User.first_name,
                   User.last_name)

        users = await self.session.execute(q)

        return users.all()

    async def insert(self, sign_up: SignUpBaseSchema):
        q = insert(User).values(**sign_up.dict())

        await self.session.execute(q)
