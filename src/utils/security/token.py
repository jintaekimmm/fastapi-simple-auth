import secrets
from datetime import datetime, timedelta

from jose import jwt

from core.config import settings
from schemas import token


async def create_new_jwt_token(*, sub: str) -> token.JWTToken:
    """
    사용자에게 반환할 JWT 토큰을 생성한다
    """
    # token 발급 시간
    iat = int(datetime.now().timestamp())

    access_token: token.CreateToken = await create_access_token(sub=sub, iat=iat)
    refresh_token: token.CreateToken = await create_refresh_token()

    return token.JWTToken(
        token_type="Bearer",
        access_token=access_token.token,
        expires_in=access_token.expires_in,
        refresh_token=refresh_token.token,
        refresh_token_expires_in=refresh_token.expires_in,
        scope="",
        sub=sub,
        iat=iat,
    )


async def create_access_token(*, sub: str, iat: int = None) -> token.CreateToken:
    """
    AccessToken을 생성한다
    """
    return _create_token(
        token_type="access_token",
        expires_in=timedelta(minutes=settings.jwt_access_token_expire_minutes),
        sub=sub,
        iat=iat,
    )


def _create_token(
    token_type: str, expires_in: timedelta, sub: str, iat: int
) -> token.CreateToken:
    """
    Token을 생성한다
    """
    now = datetime.now()
    if not iat:
        iat = int(now.timestamp())

    payload = dict()
    exp = int((now + expires_in).timestamp())
    payload["iat"] = iat
    payload["exp"] = exp
    payload["sub"] = sub
    payload["type"] = token_type

    jwt_token = jwt.encode(
        payload, key=settings.jwt_access_secret_key, algorithm=settings.jwt_algorithm
    )

    return token.CreateToken(token=jwt_token, expires_in=exp)


async def create_refresh_token() -> token.CreateToken:
    """
    RefreshToken을 생성한다
    """

    random_token = secrets.token_hex(80)
    t = timedelta(minutes=settings.jwt_refresh_token_expire_minutes)
    exp = int((datetime.now() + t).timestamp())

    return token.CreateToken(token=random_token, expires_in=exp)
