from dataclasses import dataclass
from urllib import parse

import aiohttp
from loguru import logger

from core.config import settings
from helper.random import generate_random_state


@dataclass
class NaverUserProfile:
    """Naver 사용자의 프로필 정보를 담는 클래스"""

    id: str = ""
    email: str = ""
    nickname: str = ""
    gender: str = ""
    age: str = ""
    birthday: str = ""
    profile_image: str = ""
    name: str = ""
    mobile: str = ""

    async def mapping_data(self, body: dict):
        """
        프로필 데이터를 바인딩한다
        """

        self.id = body.get("id", "")
        self.email = body.get("email", None)
        self.nickname = body.get("nickname", None)
        self.gender = body.get("gender", None)
        self.age = body.get("age", None)
        self.birthday = body.get("birthday", None)
        self.profile_image = body.get("profile_image", None)
        self.name = body.get("name", None)
        self.mobile = body.get("mobile", None)


def get_login_url() -> str:
    """
    네이버 로그인 URL을 생성하여 반환한다
    """

    state = generate_random_state()

    url = (
        f"https://nid.naver.com/oauth2.0/authorize?response_type=code"
        f"&client_id={settings.naver_client_id}"
        f"&redirect_uri={parse.quote(settings.naver_callback_url)}"
        f"&state={state}"
    )

    return url


def _get_access_token_request_url(
    client_id: str, client_secret: str, code: str, state: str
):
    """
    네이버 accessToken을 발급받기 위한 요청 URL 주소를 생성하여 반환한다
    """

    url = (
        f"https://nid.naver.com/oauth2.0/token?client_id={client_id}"
        f"&client_secret={client_secret}"
        f"&grant_type=authorization_code"
        f"&state={state}"
        f"&code={code}"
    )

    return url


def _get_profile_request_url() -> str:
    """
    네이버 사용자 프로필 정보를 조회하기 위한 URL을 생성하여 반환한다
    """

    url = "https://openapi.naver.com/v1/nid/me"

    return url


class NaverOAuthClient:
    """네이버 OAuth 인증을 위한 클래스"""

    def __init__(
        self,
        code: str,
        state: str,
        http_session: aiohttp.ClientSession,
        client_id: str,
        client_secret: str,
    ):
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__http = http_session
        self.__access_token = ""
        self.__token_type = ""
        self.__code = code
        self.__state = state

    async def __get_access_token(self) -> bool:
        """
        네이버 AccessToken을 요청한다
        """

        url = _get_access_token_request_url(
            client_id=self.__client_id,
            client_secret=self.__client_secret,
            code=self.__code,
            state=self.__state,
        )

        async with self.__http.get(url=url) as response:
            resp = await response.json()

            if response.status != 200:
                logger.error(
                    f"Failed to request access token for Naver OAuth authentication. status: {response.status} error: {repr(resp)}"
                )
                return False

            self.__access_token = resp.get("access_token", "")
            self.__token_type = resp.get("token_type", "")

        if not self.__access_token or not self.__token_type:
            logger.error(
                f"Failed to request access token for Naver OAuth authentication. status: {response.status} error: {repr(resp)}"
            )
            return False

        return True

    async def __get_profile(self) -> NaverUserProfile:
        """
        네이버 사용자 프로필을 요청한다
        """

        profile = NaverUserProfile()

        headers = {"Authorization": f"{self.__token_type} {self.__access_token}"}

        url = _get_profile_request_url()

        async with (self.__http.get(url=url, headers=headers) as response):
            resp = await response.json()

            if response.status != 200:
                logger.error(
                    f"Failed to get NAVER user profile. status: {response.status} error: {repr(resp)}"
                )
                return profile

            body = resp.get("response", {})

            if not body or not body.get("id", None):
                logger.error(
                    f"Failed to get NAVER user profile. status: {response.status} error: {repr(resp)}"
                )
                return profile

            await profile.mapping_data(body)

        return profile

    async def login(self) -> NaverUserProfile:
        """
        Naver OAuth 로그인을 처리하고, 사용자 프로필 정보를 반환한다
        """
        profile = NaverUserProfile()

        # OAuth AccessToken을 요청한다
        if not await self.__get_access_token():
            return profile

        # 요청받은 accessToken으로 사용자의 프로필 정보를 요청한다
        profile = await self.__get_profile()

        return profile
