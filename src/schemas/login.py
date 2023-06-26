from datetime import datetime

from pydantic import BaseModel, EmailStr, validator

from utils import validators


class LoginSchema(BaseModel):
    """
    로그인 API Request Body 스키마
    """

    email: EmailStr
    password: str

    @validator('email')
    def email_required_validator(cls, v):
        if not v:
            raise ValueError('Email은 필수로 입력해야 합니다')
        return v

    @validator('password')
    def password_required_validator(cls, v):
        if not v:
            raise ValueError('비밀번호는 필수로 입력해야 합니다')
        return v

    _password_validator = validator('password', allow_reuse=True)(validators.password_validator)


class LoginHistorySchema(BaseModel):
    """
    로그인 성공 정보를 담은 스키마
    """

    user_id: int
    login_time: datetime
    login_success: bool
    ip_address: str
