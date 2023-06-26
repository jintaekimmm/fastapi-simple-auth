from fastapi import Depends, Body, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from loguru import logger
from pydantic import ValidationError

from core.config import settings
from core.exceptions import TokenCredentialsException, TokenExpiredException
from schemas.token import UserToken

auth_scheme = HTTPBearer(auto_error=False)


def _get_authorization_scheme_param(authorization: HTTPAuthorizationCredentials) -> tuple[str, str]:
    if not authorization:
        return '', ''

    return authorization.scheme, authorization.credentials


class AuthorizeToken:
    def __call__(self, authorization: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> UserToken:
        scheme, token = _get_authorization_scheme_param(authorization)

        if scheme.lower() != "bearer" or not token or token == 'null':
            raise TokenCredentialsException()

        try:
            payload = jwt.decode(token=token,
                                 key=settings.jwt_access_secret_key,
                                 algorithms=[settings.jwt_algorithm])
            try:
                token_data = UserToken(**payload, access_token=token)

                return token_data
            except ValidationError as e:
                logger.error(f'token validation error: {e}')
                logger.exception(e)
                raise TokenCredentialsException()

        except jwt.ExpiredSignatureError as e:
            logger.exception(e)
            raise TokenExpiredException()

        except jwt.JWTError as e:
            logger.exception(e)
            raise TokenCredentialsException()


class AuthorizeRefreshToken:
    def __call__(self, refresh_token: str = Body(..., embed=True)):
        if not refresh_token:
            raise TokenCredentialsException()

        return refresh_token


class AuthorizeRefreshCookie:
    def __call__(self, refresh_token: str | None = Cookie(default=None, alias='refresh_token')) -> str:
        if not refresh_token:
            raise TokenCredentialsException()

        return refresh_token
