from pydantic import BaseModel, EmailStr, field_validator
from pydantic_core.core_schema import FieldValidationInfo

from schemas.responses import DefaultResponse
from utils import validators


class RegisterRequest(BaseModel):
    """
    회원가입 API Request Body 스키마
    """

    name: str
    email: EmailStr
    mobile: str | None
    password1: str
    password2: str

    @field_validator("name")
    @classmethod
    def val_name(cls, v: str):
        if not v:
            raise ValueError("이름은 필수로 입력해야 합니다")
        return validators.name_validator(v)

    @field_validator("email")
    @classmethod
    def val_email(cls, v: str):
        if not v:
            raise ValueError("Email은 필수로 입력해야 합니다")
        return v

    @field_validator("mobile")
    @classmethod
    def val_mobile(cls, v: str):
        """
        '-' 하이픈 문자열을 모두 삭제하고 반환한다
        """
        if v:
            return validators.mobile_validator(v.replace("-", ""))

    @field_validator("password1", "password2")
    @classmethod
    def val_password1_password2(cls, v: str):
        if not v:
            raise ValueError("비밀번호는 필수로 입력해야 합니다")
        return validators.password_validator(v)

    @field_validator("password2", mode="after")
    @classmethod
    def val_password_check(cls, v: str, info: FieldValidationInfo):
        pwd1 = info.data.get("password1", None)
        pwd2 = v

        if pwd1 is not None and pwd2 is not None and pwd1 != pwd2:
            raise ValueError("비밀번호가 일치하지 않습니다")
        return v


class RegisterInsert(BaseModel):
    """
    회원가입 정보를 DB에 저장할 때 사용하는 스키마
    """

    name: str
    email: str | None
    email_key: str | None
    uuid: bytes
    mobile: str | None
    mobile_key: str | None
    password: str | None
    provider_id: str
    is_active: int = 0


class RegisterResponse(DefaultResponse):
    """
    회원가입 결과를 반환할 때 사용하는 스키마
    """

    id: int


class OAuthUserInsert(BaseModel):
    """
    OAuth 외부 유저 정보를 DB에 저장할 때 사용하는 스키마
    """

    user_id: int
    provider_id: str
    sub: str
    name: str
    nickname: str | None = None
    profile_picture: str | None = None
    given_name: str | None = None
    family_name: str | None = None
