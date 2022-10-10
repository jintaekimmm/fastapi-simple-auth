from datetime import datetime

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
    refresh_token: str
    refresh_token_key: str
    issued_at: datetime
    expires_at: datetime
