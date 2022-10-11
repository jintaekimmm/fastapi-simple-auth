from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CreateTokenPartSchema(BaseModel):
    token: str
    expires_in: str


class CreateTokenSchema(BaseModel):
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


class CookieTokenSchema(BaseModel):
    access_token: str
    refresh_token: str


class TokenUser(BaseModel):
    iat: str
    exp: str
    sub: str
    type: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
