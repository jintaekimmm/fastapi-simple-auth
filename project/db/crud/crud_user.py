from sqlalchemy import insert
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from schemas.signup import SignUpBaseSchema


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

    async def get_user_from_email(self, email_ley: str) -> User:
        """
        이메일로 사용자를 조회한다
        암호화된 이메일로 검색할 수 없으니, blind index를 통해 이메일을 검색한다
        """
        q = select(User).where(User.email_key == email_ley)
        result = await self.session.execute(q)

        return result.scalars().first()

    async def insert(self, sign_up: SignUpBaseSchema):
        """
        신규 사용자 정보를 저장한다
        """
        q = insert(User).values(**sign_up.dict())

        await self.session.execute(q)

    async def exists_email(self, email_key: str) -> bool:
        """
        이메일이 존재하는지 조회한다
        암호화된 이메일을 검색 할 수 없으니, blind index를 통해 이메일을 검색한다
        """
        exists_criteria = (
            select(User.email_key).
            where(User.email_key == email_key).
            exists()
        )
        q = select(User.id).where(exists_criteria)
        result = await self.session.execute(q)

        return bool(result.all())

    async def exists_mobile(self, mobile_key: str) -> bool:
        """
        핸드폰 번호가 존재하는지 조회한다
        암호화된 핸드폰 번호를 검색할 수 없으니, blind index를 통해 핸드폰 번호를 검색한다
        """
        exists_criteria = (
            select(User.mobile_key).
            where(User.mobile_key == mobile_key).
            exists()
        )
        q = select(User.id).where(exists_criteria)
        result = await self.session.execute(q)

        return bool(result.all())
