import os

from fastapi import FastAPI, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.staticfiles import StaticFiles

from core.exceptions import TokenCredentialsException, TokenExpiredException
from core.responses import DefaultJSONResponse, ErrorJSONResponse
from app.api import auth, token, oauth


def create_app() -> FastAPI:
    # Environment에 따른 설정 적용
    env = os.environ.get("ENV", "production")

    if env == "production":
        # Swagger Docs
        openapi_url = None
    else:
        openapi_url = "/openapi.json"

    app = FastAPI(
        openapi_url=openapi_url, swagger_ui_parameters={"defaultModelsExpandDepth": -1}
    )

    app.mount("/static", StaticFiles(directory="static"), name="static")

    set_routes(app)
    set_middlewares(app)
    set_custom_exception(app)

    return app


def set_routes(app: FastAPI) -> None:
    """Routes Initializing"""

    @app.get("/")
    async def root():
        return DefaultJSONResponse(message="ok", success=True)

    @app.get("/health")
    async def health_check():
        return DefaultJSONResponse(message="ok", success=True)

    app.include_router(router=auth.router)
    app.include_router(router=token.router)
    app.include_router(router=oauth.google.router, prefix="/oauth")
    app.include_router(router=oauth.naver.router, prefix="/oauth")


def set_middlewares(app: FastAPI) -> None:
    """Middleware Initializing"""

    origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )


def set_custom_exception(app: FastAPI) -> None:
    """
    Set Custom Exception Handlers

    Token Exception에 대한 JSON Response handler
    """

    @app.exception_handler(TokenCredentialsException)
    async def token_credentials_exception_handlers(
        request: Request, exc: TokenCredentialsException
    ):
        return ErrorJSONResponse(
            message=exc.message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=1401,
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(TokenExpiredException)
    async def token_expired_exception_handler(
        request: Request, exc: TokenExpiredException
    ):
        return ErrorJSONResponse(
            message=exc.message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=1401,
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """
        RequestValidation Handler

        HTTP Status 422(UNPROCESSABLE_ENTITY)의 error logging과 response message 설정을 위한 exception handler
        """

        logger.error(f"validation error: {exc.errors()}")

        async def parse_error_message(err: dict) -> str:
            try:
                if "error" in err.get("msg", "").split(",")[0]:
                    new_error_msg = "".join(err.get("msg", "").split(",")[1:])
                else:
                    new_error_msg = err["msg"]
            except:
                new_error_msg = err["msg"]

            return new_error_msg

        errors = [
            {"field": error["loc"][-1], "message": await parse_error_message(error)}
            for error in exc.errors()
        ]

        return ErrorJSONResponse(
            message=errors,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=1422,
        )
