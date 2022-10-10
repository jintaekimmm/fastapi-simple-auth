from pydantic import BaseModel, validator, EmailStr


class LoginRequestSchema(BaseModel):
    email: EmailStr
    password: str

    @validator('email', 'password')
    def require_validator(cls, v):
        if not v:
            raise ValueError('value required')
        return v
