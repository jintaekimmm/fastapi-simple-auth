from sqlalchemy import select, insert, func
from sqlalchemy.engine import cursor

from crud.abstract import DalABC
import models
import schemas


class UserDAL(DalABC):
    async def get_by_user_id(self, user_id: int) -> models.User:
        """
        사용자 Id로 사용자를 검색하여 결과를 반환한다

        :param user_id: 사용자 Id 이다
        :return: 사용자 User 데이터를 반환한다
        """

        q = select(models.User).where(models.User.id == user_id)

        result = await self.session.execute(q)
        return result.scalars().first()

    async def get_by_email(self, email_key: str) -> models.User:
        """
        이메일 주소로 사용자를 검색하여 결과를 반환한다

        :param: email_key: 이메일 주소를 SHA-256으로 변환한 해시값
        :return: 사용자 User 데이터를 반환한다
        """

        q = select(models.User).where(models.User.email_key == email_key)

        result = await self.session.execute(q)
        return result.scalars().first()

    async def exists_email(self, email_key: str) -> bool:
        """
        Email 주소가 등록되어 있는지 확인한 후, 존재 여부를 반환한다

        :param email_key: 이메일 주소를 SHA-256으로 변환한 해시값
        :return: email 주소가 등록되어 있다면 True, 없다면 False를 반환한다
        """

        exists_criteria = (
            select(models.User.email_key)
            .where(models.User.email_key == email_key)
            .exists()
        )

        q = select(models.User.id).where(exists_criteria)

        result = await self.session.execute(q)
        return bool(result.all())

    async def exists_mobile(self, mobile_key: str) -> bool:
        """
        핸드폰 번호가 등록되어 있는지 확인한 후, 존재 여부를 반환한다

        :param mobile_key: 핸드폰 번호를 SHA-256으로 변환한 해시값
        :return: 핸드폰 번호가 등록되어 있다면 True, 없다면 False를 반환한다
        """

        exists_criteria = (
            select(models.User.mobile_key)
            .where(models.User.mobile_key == mobile_key)
            .exists()
        )

        q = select(models.User.id).where(exists_criteria)

        result = await self.session.execute(q)
        return bool(result.all())

    async def insert_user(
        self, new_user: schemas.UserInsertSchema
    ) -> cursor.CursorResult:
        """
        회원가입 정보를 테이블에 저장한다

        :param new_user: 회원가입 정보가 포함된 스키마 정보
        :return:
        """

        q = insert(models.User).values(**new_user.dict())

        result = await self.session.execute(q)
        return result


class UserLoginHistoryDAL(DalABC):
    async def insert_login_history(
        self, login_history: schemas.LoginHistorySchema
    ) -> None:
        """
        로그인 접속 기록을 DB에 저장한다
        """

        _login_dict = login_history.dict()
        _login_dict["ip_address"] = func.inet6_aton(_login_dict.get("ip_address"))

        q = insert(models.UserLoginHistory).values(**_login_dict)

        await self.session.execute(q)


class SocialUserAccountDAL(DalABC):
    async def get_user(self, provider_id: str, sub: str) -> models.User:
        """
        OAuth 사용자의 계정 정보를 조회하여 반환한다
        """

        q = (
            select(models.User)
            .join(
                models.SocialUserAccount,
                models.SocialUserAccount.user_id == models.User.id,
            )
            .where(models.SocialUserAccount.provider_id == provider_id)
            .where(models.SocialUserAccount.sub == sub)
        )

        result = await self.session.execute(q)
        return result.scalars().first()

    async def exists_user(self, provider_id: str, sub: str) -> bool:
        """
        OAuth와 연동된 계정이 존재하는지 확인한다
        """

        exists_criteria = (
            select(models.SocialUserAccount.id)
            .where(models.SocialUserAccount.provider_id == provider_id)
            .where(models.SocialUserAccount.sub == sub)
            .exists()
        )

        q = select(models.SocialUserAccount.id).where(exists_criteria)

        result = await self.session.execute(q)
        return bool(result.all())

    async def insert_user(self, new_user: schemas.OAuthUserInsertSchema):
        """
        OAuth 연동 계정 정보를 저장한다
        """

        q = insert(models.SocialUserAccount).values(**new_user.dict())

        result = await self.session.execute(q)
