from typing import Union

from fastapi import Cookie, HTTPException, status, Header
from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt
from pydantic import ValidationError

from internal.config import settings
from internal.logging import app_logger
from schemas.token import TokenUser, CookieTokenSchema

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid Token"
)

token_expired_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token Expired"
)


class AuthorizeCookieUser:
    def __call__(self,
                 access_token: Union[str, None] = Cookie(default=None),
                 refresh_token: Union[str, None] = Cookie(default=None)) -> TokenUser:

        if not access_token or not refresh_token:
            raise credentials_exception

        try:
            payload = jwt.decode(token=access_token,
                                 key=settings.jwt_access_secret_key,
                                 algorithms=[settings.jwt_algorithm])
            try:
                token_data = TokenUser(**payload, access_token=access_token, refresh_token=refresh_token)
                return token_data
            except ValidationError as e:
                app_logger.error(f'token validation error: {e}')
                raise credentials_exception
        except jwt.ExpiredSignatureError:
            raise token_expired_exception

        except jwt.JWTError as e:
            app_logger.error(f'token jwt error: {e}')
            raise credentials_exception


class AuthorizeTokenUser:
    def __call__(self, authorization: str = Header(None)) -> TokenUser:
        scheme, token = get_authorization_scheme_param(authorization)

        if scheme.lower() != "bearer" or not token:
            raise credentials_exception

        try:
            payload = jwt.decode(token=token,
                                 key=settings.jwt_access_secret_key,
                                 algorithms=[settings.jwt_algorithm])
            try:
                token_data = TokenUser(**payload, access_token=token)
                return token_data
            except ValidationError as e:
                app_logger.error(f'token validation error: {e}')
                raise credentials_exception

        except jwt.ExpiredSignatureError:
            raise token_expired_exception

        except jwt.JWTError as e:
            app_logger.error(f'token jwt error: {e}')
            raise credentials_exception


class AuthorizeTokenRefresh:
    def __call__(self, token: CookieTokenSchema) -> TokenUser:
        if not token.access_token or not token.refresh_token:
            raise credentials_exception

        try:
            payload = jwt.decode(token=token.access_token,
                                 key=settings.jwt_access_secret_key,
                                 algorithms=[settings.jwt_algorithm])
            try:
                token_data = TokenUser(**payload, access_token=token.access_token, refresh_token=token.refresh_token)
                return token_data
            except ValidationError as e:
                app_logger.error(f'token validation error: {e}')
                raise credentials_exception
        except jwt.ExpiredSignatureError:
            raise token_expired_exception

        except jwt.JWTError as e:
            app_logger.error(f'token jwt error: {e}')
            raise credentials_exception
