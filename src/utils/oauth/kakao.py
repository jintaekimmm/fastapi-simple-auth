from dataclasses import dataclass

import aiohttp
from loguru import logger

from core.config import settings
from utils.oauth.profile import UserProfile
from utils.random import generate_random_state


@dataclass
class KakaoUserProfile(UserProfile):
    async def mapping_data(self, body: dict):
        """
        프로필 데이터를 바인당한다
        """
        kakao_account = body.get("kakao_account", {})
        kakao_profile = kakao_account.get("profile", {})

        self.id = str(body.get("id", ""))
        self.nickname = kakao_profile.get("nickname", None)
        self.profile_image = kakao_profile.get("profile_image_url", None)
        self.email = kakao_account.get("email", None)
        self.gender = kakao_account.get("gender", None)
        self.age = kakao_account.get("age_range", None)
        self.birthday = kakao_account.get("birthday", None)
        self.name = kakao_account.get("name", None)
        self.mobile = kakao_account.get("phone_number", None)

        # 이름은 필수 값이므로, 만약 이름이 존재하지 않는다면 id(sub) 값을 문자열로 대체하여 저장한다
        if not self.name:
            self.name = str(self.id)


def get_login_url() -> str:
    """
    카카오 로그인 URL을 생성하여 반환한다
    """

    # state = generate_random_state()
    state = None

    url = (
        f"https://kauth.kakao.com/oauth/authorize?response_type=code"
        f"&client_id={settings.kakao_rest_api_key}"
        f"&redirect_uri={settings.kakao_redirect_uri}"
    )

    if state:
        url += f"&state={state}"

    return url


def _get_access_token_request_url() -> str:
    """
    카카오 accessToken을 발급받기 위해 Token 요청 URL 주소를 생성하여 반환한다
    """

    url = "https://kauth.kakao.com/oauth/token"

    return url


def _get_access_token_headers() -> dict:
    """
    카카오 accessToken 요청 시 사용할 헤더 정보를 생성하여 반환한다
    """

    headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}

    return headers


def _get_profile_request_url() -> str:
    """
    카카오 사용자 프로필 정보를 조회하기 위한 URL을 생성하여 반환한다
    """

    url = "https://kapi.kakao.com/v2/user/me"

    return url


def _get_profile_headers(token_type: str, access_token: str) -> dict:
    """
    카카오 프로필 요청 시 사용할 헤더 정보를 생성하여 반환한다
    """
    headers = {
        "Authorization": f"{token_type} {access_token}",
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
    }

    return headers


class KakaoOAuthClient:
    """카카오 OAuth 인증을 위한 클래스"""

    def __init__(
        self,
        code: str,
        state: str,
        http_session: aiohttp.ClientSession,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ):
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__redirect_uri = redirect_uri
        self.__http = http_session
        self.__access_token = ""
        self.__refresh_token = ""
        self.__token_type = ""
        self.__id_token = ""
        self.__code = code
        self.__state = state

    async def __get_access_token(self) -> bool:
        """
        카카오 AccessToken을 요청한다
        """

        url = _get_access_token_request_url()
        headers = _get_access_token_headers()

        data = {
            "grant_type": "authorization_code",
            "client_id": self.__client_id,
            "client_secret": self.__client_secret,
            "code": self.__code,
            "redirect_uri": self.__redirect_uri,
        }

        async with self.__http.post(url=url, headers=headers, data=data) as response:
            resp = await response.json()

            if response.status != 200:
                logger.error(
                    f"Failed to request access token for Kakao OAuth authentication. status: {response.status} error: {repr(resp)}"
                )
                return False

            self.__access_token = resp.get("access_token", "")
            self.__refresh_token = resp.get("refresh_token", "")
            self.__token_type = resp.get("token_type", "")
            self.__id_token = resp.get("id_token", "")

        if not self.__access_token or not self.__refresh_token:
            logger.error(
                f"Failed to request access token for Kakao OAuth authentication. status: {response.status}. error: {repr(resp)}"
            )
            return False

        return True

    async def __get_profile(self):
        """
        카카오 사용자 프로필을 요청한다
        """

        profile = KakaoUserProfile()

        headers = _get_profile_headers(
            token_type=self.__token_type, access_token=self.__access_token
        )

        url = _get_profile_request_url()

        async with self.__http.get(url, headers=headers) as response:
            resp = await response.json()

            if response.status != 200:
                logger.error(
                    f"Failed to get Kakao user profile. status: {response.status} error: {repr(resp)}"
                )
                return None

            body = resp

            if not body or not body.get("id", None):
                logger.error(
                    f"Failed to get Kakao user profile. status: {response.status} error: {repr(resp)}"
                )
                return None

            await profile.mapping_data(body)

        return profile

    async def login(self) -> KakaoUserProfile:
        """
        Kakao OAuth 로그인을 처리하고, 사용자 프로필 정보를 반환한다
        """

        profile = KakaoUserProfile()

        # OAuth AccessToken을 요청한다
        if not await self.__get_access_token():
            return profile

        # 요청받은 accessToken으로 사용자의 프로필 정보를 요청한다
        profile = await self.__get_profile()

        return profile
