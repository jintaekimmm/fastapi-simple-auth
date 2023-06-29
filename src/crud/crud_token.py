from sqlalchemy import select, insert, delete, update

from crud.abstract import DalABC
import models
import schemas


class TokenDAL(DalABC):
    async def get(self, refresh_token_key: str) -> models.JWTToken:
        """
        refreshToken으로 저장된 토큰 정보를 조회한다

        :param refresh_token_key: SHA-256으로 해싱된 refreshToken 값이다
        :return:
        """

        q = select(models.JWTToken).where(
            models.JWTToken.refresh_token_key == refresh_token_key
        )

        result = await self.session.execute(q)
        return result.scalars().first()

    async def insert_token(self, new_token: schemas.TokenInsertSchema) -> None:
        """
        생성된 Token 정보를 DB에 저장한다

        :param new_token: 새로 생성된 JWT Token 정보를 담고 있는 스키마
        :return:
        """
        q = insert(models.JWTToken).values(**new_token.dict())

        await self.session.execute(q)

    async def exists(self, user_id: int, access_token: str) -> bool:
        """
        사용자 AccessToken이 존재하는지 확인하고 결과를 반환한다

        :param user_id: 사용자 Id 번호로 JWT Token에 저장된 sub claim를 전달 받는다
        :param access_token: JWT Token의 accessToken이다
        :return: 토큰 정보가 존재한다면 'True'를 반환하고, 그렇지 않다면 'False'를 반환한다
        """

        exists_criteria = (
            select(models.JWTToken)
            .where(models.JWTToken.user_id == user_id)
            .where(models.JWTToken.access_token == access_token)
            .exists()
        )

        q = select(models.JWTToken).where(exists_criteria)

        result = await self.session.execute(q)
        return bool(result.all())

    async def delete(self, user_id: int, access_token: str) -> None:
        """
        저장된 사용자 accessToken 정보를 삭제한다

        :param user_id: 사용자 Id 번호로 JWT Token에 저장된 sub claim를 전달 받는다
        :param access_token: JWT Token의 accessToken이다
        :return:
        """

        q = (
            delete(models.JWTToken)
            .where(models.JWTToken.user_id == user_id)
            .where(models.JWTToken.access_token == access_token)
            .execution_options(synchronize_session="fetch")
        )

        await self.session.execute(q)

    async def update(self, update_token):
        """
        새로 생성한 Token 정보를 업데이트한다

        :param update_token: 새로 갱신한 accessToken, refreshToken과 만료일자가 포함된 데이터
        :return:
        """

        q = (
            update(models.JWTToken)
            .where(
                models.JWTToken.user_id == update_token.user_id,
                models.JWTToken.refresh_token_key == update_token.refresh_token_key,
            )
            .values(
                access_token=update_token.access_token,
                refresh_token=update_token.refresh_token,
                refresh_token_key=update_token.refresh_token_key,
                expires_at=update_token.expires_at,
            )
            .execution_options(synchronize_session="fetch")
        )

        await self.session.execute(q)
