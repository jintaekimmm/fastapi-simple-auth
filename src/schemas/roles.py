from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, validator

from schemas.permissions import PermissionNameSchema, PermissionBaseSchema
from schemas.response import DefaultResponse


class RoleBaseSchema(BaseModel):
    id: Optional[int]
    name: str
    slug: Optional[str]
    content: Optional[str] = ''
    created_at: datetime
    updated_at: datetime

    @validator('content')
    def fill_empty_string_content(cls, v):
        if not v:
            return ''
        return v

    class Config:
        orm_mode = True


class RoleListResponseSchema(BaseModel):
    data: List[RoleBaseSchema]


class RoleCreateUpdateRequestSchema(BaseModel):
    name: str
    slug: Optional[str]
    content: Optional[str] = ''
    permissions: List[PermissionNameSchema] = []

    @validator('name')
    def name_required_validator(cls, v):
        if not v:
            raise ValueError('value required')
        return v

    @validator('content')
    def fill_empty_string_content(cls, v):
        if not v:
            return ''
        return v

    class Config:
        orm_mode = True


class RolePermissionSchema(BaseModel):
    id: Optional[int]
    role_id: int
    permission_id: int

    @validator('role_id', 'permission_id')
    def required_validator(cls, v):
        if not v:
            raise ValueError('value required')
        return v


class RolesAndPermissionResponseSchema(RoleBaseSchema):
    permissions: List[PermissionBaseSchema]

    class Config:
        orm_mode = True
        fields = {
            'slug': {
                'exclude': True
            }
        }


class UserHasRoleSchema(BaseModel):
    result: bool

class UserHashRoleResponseSchema(DefaultResponse):
    data: UserHasRoleSchema


class UserHasPermissionSchema(BaseModel):
    result: bool


class UserHasPermissionResponseSchema(DefaultResponse):
    data: UserHasPermissionSchema
