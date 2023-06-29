from typing import Any

from starlette.responses import JSONResponse
from starlette.background import BackgroundTask


class DefaultJSONResponse(JSONResponse):
    """
    JSONResponse을 좀 더 편하게 사용하기 위한 커스텀 Response 클래스

    - 기존의 사용하던 JSONResponse 구문을 다음과 같이 줄여서 사용한다
    - 'message'와 'code'를 고정으로 사용하는 경우에만 이 클래스를 사용한다
    - 'code' 값이 없는 경우에는 'status_code'를 'code' 값으로 사용한다

    [기존]
    return JSONResponse({'message': '사용자를 찾을 수 없습니다',
                         'code': await str_status_code(status.HTTP_404_NOT_FOUND)},
                          status_code=status.HTTP_404_NOT_FOUND)
    [신규]
    return DefaultJSONResponse(message='success',
                               success=True,
                               status_code=status.HTTP_200_OK)
    """

    def __init__(
        self,
        message: Any,
        success: bool = True,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> None:
        content = {
            "success": success,
            "message": message,
        }

        super().__init__(content, status_code, headers, media_type, background)


class ErrorJSONResponse(JSONResponse):
    """
    JSONResponse을 좀 더 편하게 사용하기 위한 커스텀 Response 클래스

    - 기존의 사용하던 JSONResponse 구문을 다음과 같이 줄여서 사용한다
    - 'message'와 'code'를 고정으로 사용하는 경우에만 이 클래스를 사용한다
    - 'code' 값이 없는 경우에는 'status_code'를 'code' 값으로 사용한다

    [기존]
    return JSONResponse({'message': '사용자를 찾을 수 없습니다',
                             'code': await str_status_code(status.HTTP_404_NOT_FOUND)},
                            status_code=status.HTTP_404_NOT_FOUND)
    [신규]
    return ErrorJSONResponse(message='사용자를 찾을 수 없습니다',
                             error_code=404,
                             status_code=status.HTTP_404_NOT_FOUND)
    """

    def __init__(
        self,
        message: Any,
        success: bool = False,
        status_code: int = 200,
        error_code: int | None = None,
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> None:
        content = {
            "success": success,
            "message": message,
            "error_code": error_code,
        }

        super().__init__(content, status_code, headers, media_type, background)
