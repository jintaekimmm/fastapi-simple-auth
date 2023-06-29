from abc import ABCMeta

from pydantic import BaseModel


class ResponseSchemaABC(BaseModel, metaclass=ABCMeta):
    """
    기본 Response format에 필요한 추상화 스키마
    """

    message: str
    success: bool


class DefaultResponse(ResponseSchemaABC):
    """
    기본 Response Format을 위한 스키마
    """

    pass


class ErrorResponse(ResponseSchemaABC):
    """
    Error Response Format을 위한 스키마
    """

    error_code: int
