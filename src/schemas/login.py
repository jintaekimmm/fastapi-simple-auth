from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from utils import validators


class LoginSchema(BaseModel):
    """
    로그인 API Request Body 스키마
    """

    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def val_email(cls, v):
        if not v:
            raise ValueError("Email은 필수로 입력해야 합니다")
        return v

    @field_validator("password")
    @classmethod
    def val_password(cls, v):
        if not v:
            raise ValueError("비밀번호는 필수로 입력해야 합니다")
        return validators.password_validator(v)


class LoginHistorySchema(BaseModel):
    """
    로그인 성공 정보를 담은 스키마
    """

    user_id: int
    login_time: datetime
    login_success: bool
    ip_address: str
