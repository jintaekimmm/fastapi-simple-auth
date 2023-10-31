import logging
import os
import pathlib
from functools import lru_cache

from pydantic_settings import BaseSettings
from fastapi.templating import Jinja2Templates

log = logging.getLogger("uvicorn")
BASE_DIR = pathlib.Path(__file__).parent.parent
TEMPLATES = Jinja2Templates(directory=f"{BASE_DIR}/html")


class Settings(BaseSettings):
    env: str = os.environ.get("ENV", "production")
    log_level: str = os.environ.get("LOG_LEVEL", "INFO")

    ####################
    # Database info
    ####################
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    ####################
    # encryption info
    ####################
    password_secret_key: str
    index_hash_key: str
    aes_encrypt_key: str

    jwt_algorithm: str = "HS256"
    jwt_access_secret_key: str
    jwt_refresh_secret_key: str
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_minutes: int = 10080

    ####################
    # OAuth: Google
    ####################
    google_client_id: str | None = None
    google_client_secret: str | None = None

    ####################
    # OAuth: Naver
    ####################
    naver_client_id: str | None = None
    naver_client_secret: str | None = None
    naver_callback_url: str | None = None

    ####################
    # OAuth: Kakao
    ####################
    kakao_rest_api_key: str | None = None
    kakao_client_secret: str | None = None
    kakao_redirect_uri: str | None = None

    ####################
    # OAuth: Apple
    ####################
    apple_team_id: str | None = None
    apple_client_id: str | None = None
    apple_key_id: str | None = None
    apple_redirect_uri: str | None = None
    apple_auth_key_file: str | None = None


class LocalSettings(Settings):
    class Config:
        env_file = f"{BASE_DIR}/.env.local"


class DevelopmentSettings(Settings):
    class Config:
        env_file = f"{BASE_DIR}/.env.dev"


class ProductionSettings(Settings):
    class Config:
        env_file = f"{BASE_DIR}/.env"


class TestingSettings(Settings):
    class Config:
        env_file = f"{BASE_DIR}/.env.test"


@lru_cache
def get_settings() -> BaseSettings:
    settings_cls_dict = {
        "local": LocalSettings,
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "testing": TestingSettings,
    }

    env = os.environ.get("ENV", "production")
    settings_cls = settings_cls_dict[env]

    return settings_cls()


settings = get_settings()
