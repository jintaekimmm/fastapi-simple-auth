from typing import Any, Optional, Dict

from starlette.background import BackgroundTask
from starlette.responses import JSONResponse


class CustomJSONResponse(JSONResponse):
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
    return CustomJSONResponse(message='사용자를 찾을 수 없습니다',
                                  status_code=status.HTTP_404_NOT_FOUND)
    """
    def __init__(
            self,
            message: Any,
            status_code: int = 200,
            code: Optional[int] = None,
            headers: Optional[Dict[str, str]] = None,
            media_type: Optional[str] = None,
            background: Optional[BackgroundTask] = None
    ) -> None:
        if code:
            _code = f'{code:04d}'
        else:
            _code = f'{status_code:04d}'

        content = {
            'message': message,
            'code': _code,
        }
        super().__init__(content, status_code, headers, media_type, background)
