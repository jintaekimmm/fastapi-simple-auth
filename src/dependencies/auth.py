from typing import Union, Tuple

from fastapi import Cookie, Header, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt
from loguru import logger
from pydantic import ValidationError

from app.core.exception import TokenCredentialsException, TokenExpiredException
from internal.config import settings
from schemas.token import TokenUser, TokenRefreshRequestSchema


auth_scheme = HTTPBearer(auto_error=False)

def _get_authorization_scheme_param(authorization: HTTPAuthorizationCredentials) -> Tuple[str, str]:
    if not authorization:
        return '', ''

    return authorization.scheme, authorization.credentials


class AuthorizeCookieUser:
    def __call__(self,
                 access_token: Union[str, None] = Cookie(default=None),
                 refresh_token: Union[str, None] = Cookie(default=None)) -> TokenUser:

        if not access_token or not refresh_token:
            raise TokenCredentialsException()

        try:
            payload = jwt.decode(token=access_token,
                                 key=settings.jwt_access_secret_key,
                                 algorithms=[settings.jwt_algorithm])
            try:
                token_data = TokenUser(**payload, access_token=access_token, refresh_token=refresh_token)
                return token_data
            except ValidationError as e:
                logger.exception(e)
                raise TokenCredentialsException()
        except jwt.ExpiredSignatureError:
            raise TokenExpiredException()

        except jwt.JWTError as e:
            logger.exception(e)
            raise TokenCredentialsException()


class AuthorizeRefreshCookieUser:
    def __call__(self,
                 access_token: Union[str, None] = Cookie(default=None),
                 refresh_token: Union[str, None] = Cookie(default=None)) -> TokenUser:

        if not access_token or not refresh_token:
            raise TokenCredentialsException()

        try:
            # refreshToken에서는 accessToken의 만료를 체크하지 않는다
            options = {
                "verify_exp": False,
            }
            payload = jwt.decode(token=access_token,
                                 key=settings.jwt_access_secret_key,
                                 algorithms=[settings.jwt_algorithm],
                                 options=options)
            try:
                token_data = TokenUser(**payload, access_token=access_token, refresh_token=refresh_token)
                return token_data
            except ValidationError as e:
                logger.exception(e)
                raise TokenCredentialsException()
        except jwt.ExpiredSignatureError:
            raise TokenExpiredException()

        except jwt.JWTError as e:
            logger.exception(e)
            raise TokenCredentialsException()

class AuthorizeTokenUser:
    def __call__(self, authorization: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> TokenUser:
        scheme, token = _get_authorization_scheme_param(authorization)

        if scheme.lower() != "bearer" or not token:
            raise TokenCredentialsException()

        try:
            payload = jwt.decode(token=token,
                                 key=settings.jwt_access_secret_key,
                                 algorithms=[settings.jwt_algorithm])
            try:
                token_data = TokenUser(**payload, access_token=token)
                return token_data
            except ValidationError as e:
                logger.exception(e)
                raise TokenCredentialsException()

        except jwt.ExpiredSignatureError:
            raise TokenExpiredException()

        except jwt.JWTError as e:
            logger.exception(e)
            raise TokenCredentialsException()


class AuthorizeTokenRefresh:
    def __call__(self, token: TokenRefreshRequestSchema) -> TokenUser:
        if not token.access_token or not token.refresh_token:
            raise TokenCredentialsException()

        try:
            # refreshToken에서는 accessToken의 만료를 체크하지 않는다
            options = {
                "verify_exp": False,
            }
            payload = jwt.decode(token=token.access_token,
                                 key=settings.jwt_access_secret_key,
                                 algorithms=[settings.jwt_algorithm],
                                 options=options)
            try:
                token_data = TokenUser(**payload, access_token=token.access_token, refresh_token=token.refresh_token)
                return token_data
            except ValidationError as e:
                logger.exception(e)
                raise TokenCredentialsException()
        except jwt.ExpiredSignatureError:
            raise TokenExpiredException()

        except jwt.JWTError as e:
            logger.exception(e)
            raise TokenCredentialsException()
