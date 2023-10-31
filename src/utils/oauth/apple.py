import pathlib
from dataclasses import dataclass
from datetime import datetime, timedelta

import aiohttp
from jose import jwt
from loguru import logger

from core.config import Settings
from utils.oauth.profile import UserProfile

BASE_DIR = pathlib.Path(__file__).parent.parent.parent


@dataclass
class AppleUserProfile(UserProfile):
    async def mapping_data(self, body: dict):
        """
        프로필 데이터를 바인당한다
        """

        self.id = body.get("sub", "")
        self.email = body.get("email", None)
        # Apple Login에서 sub, email 외에는 제공받지 않는다
        self.nickname = body.get("nickname", None)
        self.gender = body.get("gender", None)
        self.age = body.get("age", None)
        self.birthday = body.get("birthday", None)
        self.profile_image = body.get("profile_image", None)
        self.name = body.get("name", None)
        self.mobile = body.get("mobile", None)


class AppleOAuthClient:
    """Apple OAuth 인증을 위한 클래스"""

    def __init__(
        self, code: str, settings: Settings, http_session: aiohttp.ClientSession
    ):
        self.__code = code
        self.__http = http_session
        self.__aud = "https://appleid.apple.com"
        self.__settings = settings
        self.__auth_key_file = f"{BASE_DIR}/{settings.apple_auth_key_file}"
        self.__auth_key = None
        self.__token_url = "https://appleid.apple.com/auth/oauth2/v2/token"

    async def __load_auth_key(self) -> None:
        """
        Auth Key를 읽어온다
        """
        with open(self.__auth_key_file, "r") as f:
            self.__auth_key = f.read()

    async def __generate_client_secret(self) -> str:
        """
        Client Secret JWT를 생성한다
        """

        if not self.__auth_key:
            await self.__load_auth_key()

        now = datetime.now()
        iat = int(now.timestamp())
        expires_in = timedelta(minutes=15)
        exp = int((now + expires_in).timestamp())

        header = dict()
        header["kid"] = self.__settings.apple_key_id

        payload = dict()
        payload["iss"] = self.__settings.apple_team_id
        payload["iat"] = iat
        payload["exp"] = exp
        payload["sub"] = self.__settings.apple_client_id
        payload["aud"] = self.__aud

        jwt_token = jwt.encode(
            payload, key=self.__auth_key, algorithm="ES256", headers=header
        )

        return jwt_token

    async def __validate_tokens(
        self, grant_type: str = "authorization_code"
    ) -> dict | None:
        """
        Authorization grant code를 검증한다
        """

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        form_data = aiohttp.FormData()
        form_data.add_field("client_id", self.__settings.apple_client_id)
        form_data.add_field("client_secret", await self.__generate_client_secret())
        form_data.add_field("code", self.__code)
        form_data.add_field("grant_type", grant_type)
        form_data.add_field("redirect_uri", self.__settings.apple_redirect_uri)

        async with self.__http.post(
            url=self.__token_url, headers=headers, data=form_data
        ) as response:
            resp = await response.json()

            if response.status != 200:
                logger.error(
                    f"Failed to get Apple validate token. status: {response.status} error: {repr(resp)}"
                )

                return None

            return resp

    async def login(self) -> AppleUserProfile:
        """
        Apple OAuth 로그인을 처리하고, 사용자 프로필 정보를 반환한다
        """

        profile = AppleUserProfile()

        # OAuth Authoization code를 검증한다
        resp = await self.__validate_tokens()
        if not resp:
            return profile

        # ID Token에서 사용자 프로필 정보를 파싱한다
        id_token = resp.get("id_token")
        user_token = jwt.get_unverified_claims(id_token)

        await profile.mapping_data(user_token)

        return profile
