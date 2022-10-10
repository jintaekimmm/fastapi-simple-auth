from datetime import timedelta, datetime

from jose import jwt

from app.core.security.encryption import Hasher
from internal.config import settings
from models.user import User
from schemas.token import CreateTokenSchema, CreateTokenPartSchema


async def authenticate(user: User, login_password: str) -> bool:
    """
    사용자 로그인 인증
    """
    if not user:
        return False

    if not Hasher.verify_password(login_password, user.password):
        return False

    return True


def get_jwt_key(token_type: str) -> str:
    if token_type == 'access_token':
        return settings.jwt_access_secret_key
    elif token_type == 'refresh_token':
        return settings.jwt_refresh_secret_key


async def create_new_jwt_token(*, sub: str) -> CreateTokenSchema:
    """
    사용자에게 반환할 JWT 토큰을 생성한다
    """
    # token 발급 시간
    iat = str(int(datetime.now().timestamp()))

    access_token = await create_access_token(sub=sub, iat=iat)
    refresh_token = await create_refresh_token(sub=sub, iat=iat)

    return CreateTokenSchema(
        token_type='Bearer',
        access_token=access_token.token,
        expires_in=access_token.expires_in,
        refresh_token=refresh_token.token,
        refresh_token_expires_in=refresh_token.expires_in,
        scope="",
        sub=sub,
        iat=iat
    )


async def create_access_token(*, sub: str, iat: str) -> CreateTokenPartSchema:
    """
    AccessToken을 생성한다
    """
    return _create_token(token_type='access_token',
                         expires_in=timedelta(minutes=settings.jwt_access_token_expire_minutes),
                         sub=sub,
                         iat=iat)


async def create_refresh_token(*, sub: str, iat: str) -> CreateTokenPartSchema:
    """
    RefreshToken을 생성한다
    """
    return _create_token(token_type='refresh_token',
                         expires_in=timedelta(minutes=settings.jwt_refresh_token_expire_minutes),
                         sub=sub,
                         iat=iat)


def _create_token(token_type: str,
                  expires_in: timedelta,
                  sub: str,
                  iat: str) -> CreateTokenPartSchema:
    """
    Token을 생성한다
    """
    now = datetime.now()
    if not iat:
        iat = str(int(now.timestamp()))

    payload = dict()
    exp = str(int((now + expires_in).timestamp()))
    payload['iat'] = iat
    payload['exp'] = exp
    payload['sub'] = sub
    payload['type'] = token_type

    jwt_token = jwt.encode(payload, key=get_jwt_key(token_type), algorithm=settings.jwt_algorithm)

    return CreateTokenPartSchema(token=jwt_token, expires_in=exp)
