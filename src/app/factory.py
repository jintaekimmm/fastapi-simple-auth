import os

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.api import user, signup, auth, roles, permissions
from app.core.exception import TokenCredentialsException, TokenExpiredException
from app.core.responses import CustomJSONResponse


def create_app() -> FastAPI:
    """ FastAPI App Factory """
    env = os.environ.get('ENV', 'production')

    if env == 'production':
        openapi_url = None
    else:
        openapi_url = "/openapi.json"

    app = FastAPI(openapi_url=openapi_url,
                  swagger_ui_parameters={"defaultModelsExpandDepth": -1})

    # set routes
    initial_route(app)
    # set middlewares
    initial_middlewares(app)
    # set custom exception handlers
    custom_exception(app)
    # set event handlers
    event_handler(app)

    return app


def initial_route(app: FastAPI) -> None:
    """ Routes initializing """

    app.include_router(auth.router)
    app.include_router(signup.router)
    app.include_router(user.router)
    app.include_router(roles.router)
    app.include_router(permissions.router)


def initial_middlewares(app: FastAPI) -> None:
    """ Middlewares initializing """
    origins = ['*']
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def custom_exception(app: FastAPI) -> None:
    """ Custom Exception Handlers """

    @app.exception_handler(TokenCredentialsException)
    async def token_credentials_exception_handlers(request: Request, exc: TokenCredentialsException):
        return CustomJSONResponse(message=exc.message,
                                  status_code=status.HTTP_401_UNAUTHORIZED,
                                  headers={'WWW-Authenticate': 'Bearer'})

    @app.exception_handler(TokenExpiredException)
    async def token_expired_exception_handler(request: Request, exc: TokenExpiredException):
        return CustomJSONResponse(message=exc.message,
                                  status_code=status.HTTP_401_UNAUTHORIZED,
                                  headers={'WWW-Authenticate': 'Bearer'})


def event_handler(app: FastAPI) -> None:
    """ Event Handlers """

    @app.on_event('startup')
    async def startup():
        pass

    @app.on_event('shutdown')
    async def shutdown():
        pass

