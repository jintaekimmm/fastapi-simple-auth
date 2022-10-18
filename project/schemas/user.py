from typing import List

from pydantic import validator, BaseModel


class UserAssignedRoleRequestSchema(BaseModel):
    role: str

    @validator('role')
    def role_required_validator(cls, v):
        if not v:
            raise ValueError('value required')
        return v


class UserRolesSchema(BaseModel):
    user_id: int
    role_id: int

    @validator('user_id', 'role_id')
    def required_validator(cls, v):
        if not v:
            raise ValueError('value required')
        return v


class UserAssignedRoleUpdateSchema(BaseModel):
    roles: List[str]

    @validator('roles')
    def roles_required_validator(cls, v):
        if not v or len(v) <= 0:
            raise ValueError('value required')
        return v
