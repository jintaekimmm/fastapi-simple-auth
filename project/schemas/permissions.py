from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, validator


class PermissionBaseSchema(BaseModel):
    id: int
    name: str
    slug: str
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


class PermissionListResponseSchema(BaseModel):
    data: List[PermissionBaseSchema] = []

    class Config:
        orm_mode = True


class PermissionCreateUpdateRequestSchema(BaseModel):
    name: str
    slug: Optional[str]
    content: Optional[str] = ''

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
