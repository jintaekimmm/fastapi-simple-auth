from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator


class CreateTokenPartSchema(BaseModel):
    token: str
    expires_in: str


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str


class CreateTokenSchema(TokenSchema):
    token_type: str = 'Bearer'
    access_token: str
    expires_in: str
    refresh_token: str
    refresh_token_expires_in: str
    scope: str
    sub: str
    iat: str


class InsertTokenSchema(BaseModel):
    user_id: int
    access_token: str
    refresh_token: str
    refresh_token_key: str
    issued_at: datetime
    expires_at: datetime


class UpdateTokenSchema(BaseModel):
    user_id: int
    old_access_token: str
    new_access_token: str
    refresh_token: str
    refresh_token_key: str
    expires_at: datetime


class TokenRefreshRequestSchema(TokenSchema):
    @validator('access_token', 'refresh_token')
    def require_validator(cls, v):
        if not v:
            raise ValueError('value required')
        return v


class CookieTokenSchema(TokenSchema):
    @validator('access_token', 'refresh_token')
    def require_validator(cls, v):
        if not v:
            raise ValueError('value required')
        return v


class TokenUser(BaseModel):
    iat: str
    exp: str
    sub: str
    type: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
