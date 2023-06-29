from typing import Optional

from pydantic import BaseModel, EmailStr, validator

from core.responses import DefaultJSONResponse
from schemas.responses import DefaultResponse
from utils import validators


class RegisterRequestSchema(BaseModel):
    """
    회원가입 API Request Body 스키마
    """

    name: str
    email: EmailStr
    mobile: str | None
    password1: str
    password2: str

    @validator("email")
    def email_required_validator(cls, v):
        if not v:
            raise ValueError("Email은 필수로 입력해야 합니다")
        return v

    @validator("mobile")
    def mobile_cleaning_validator(cls, v):
        """
        '-' 하이픈 문자열을 모두 삭제하고 반환한다
        """
        if v:
            return v.replace("-", "")

    @validator("password1", "password2")
    def password_required_validator(cls, v):
        if not v:
            raise ValueError("비밀번호는 필수로 입력해야 합니다")
        return v

    @validator("password2")
    def password_match_validator(cls, v, values):
        if "password1" in values and v != values["password1"]:
            raise ValueError("비밀번호가 일치하지 않습니다")
        return v

    _name_validator = validator("name", allow_reuse=True)(validators.name_validator)
    _password_validator = validator("password1", allow_reuse=True)(
        validators.password_validator
    )
    _mobile_validator = validator("mobile", allow_reuse=True)(
        validators.mobile_validator
    )


class RegisterInsertSchema(BaseModel):
    """
    회원가입 정보를 DB에 Insert할 때 사용하는 스키마
    """

    name: str
    email: str
    email_key: str
    uuid: bytes
    mobile: str | None
    mobile_key: str | None
    password: str
    is_active: int = 0


class RegisterResponseSchema(DefaultResponse):
    """
    회원가입 결과를 반환할 때 사용하는 스키마
    """

    id: int
