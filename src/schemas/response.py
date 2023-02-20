from abc import ABCMeta

from pydantic import BaseModel, validator


class DefaultResponseABC(BaseModel, metaclass=ABCMeta):
    code: str
    message: str

    @validator('code', pre=True, always=True)
    def int_to_str(cls, v):
        if not isinstance(v, str):
            return str(v)
        return v


class DefaultResponse(DefaultResponseABC):
    pass


class ErrorResponse(DefaultResponseABC):
    pass
