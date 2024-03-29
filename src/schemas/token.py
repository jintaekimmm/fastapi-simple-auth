from datetime import datetime

from pydantic import BaseModel


class UserToken(BaseModel):
    """
    Authorization Header에서 토큰을 바인딩할 때 사용하는 스키마
    """

    iat: int
    exp: int
    sub: str
    type: str
    access_token: str | None


class CreateToken(BaseModel):
    """
    JWT Token 생성 함수에서 결과를 반환할 때 사용하는 스키마
    """

    token: str
    expires_in: int


class DefaultToken(BaseModel):
    """
    기본 Token 정보 스키마
    """

    access_token: str
    refresh_token: str


class JWTToken(DefaultToken):
    """
    JWT Token 스키마
    """

    token_type: str = "Bearer"
    access_token: str
    expires_in: int
    refresh_token: str
    refresh_token_expires_in: int
    scope: str
    sub: str
    iat: int


class TokenInsert(BaseModel):
    """
    Token 정보를 DB에 저장할 때 사용하는 스키마
    """

    user_id: int
    user_uuid: bytes
    access_token: str
    refresh_token: str
    refresh_token_key: str
    issued_at: datetime
    expires_at: datetime


class TokenUpdate(BaseModel):
    """
    갱신한 Token 정보를 DB에 저장할 때 사용하는 스키마
    """

    user_id: int
    access_token: str
    refresh_token: str
    refresh_token_key: str
    expires_at: datetime


class TokenAccessOnly(BaseModel):
    """
    JWT Token 스키마
    - refreshToken 정보를 제외한 스키마
    """

    token_type: str = "Bearer"
    access_token: str
    expires_in: int
    scope: str
    sub: str
    iat: int


class AuthToken(BaseModel):
    """
    Authorization Header에 사용할 token 스키마
    """

    iat: int
    exp: int
    sub: str
    access_token: str | None
