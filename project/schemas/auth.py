from pydantic import BaseModel, validator, EmailStr


class SignUpBaseSchema(BaseModel):
    first_name: str
    last_name: str
    email: str
    email_key: str
    mobile: str
    mobile_key: str
    password: str


class SignupRequestSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    mobile: str
    password1: str
    password2: str

    @validator('mobile')
    def mobile_required_validator(cls, v):
        if not v:
            raise ValueError('value required')

        return v

    @validator('mobile')
    def mobile_cleaning(cls, v):
        return v.replace('-', '')

    @validator('email')
    def email_required_validator(cls, v):
        if not v:
            raise ValueError('value required')

        return v

    @validator('password1', 'password2')
    def password_required_validator(cls, v):
        if not v:
            raise ValueError('value required')

        return v

    @validator('password2')
    def passwords_match(cls, v, values):
        if 'password1' in values and v != values['password1']:
            raise ValueError('passwords do not match')

        return v

