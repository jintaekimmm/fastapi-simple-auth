import sys
import logging

from loguru import logger
from gunicorn.glogging import Logger

from core.config import settings

LOG_LEVEL = logging.getLevelName(settings.log_level)
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} {level} {name}:{function}:{line} {message}"


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


class GunicornLogger(Logger):
    def setup(self, cfg) -> None:
        handler = InterceptHandler()

        # Add log handler to logger and set log level
        self.error_log.addHandler(handler)
        self.error_log.setLevel(LOG_LEVEL)
        self.access_log.addHandler(handler)
        self.access_log.setLevel(LOG_LEVEL)

        # Configure logger before gunicorn starts logging
        logger.configure(
            handlers=[
                {"sink": sys.stdout, "level": settings.log_level, "format": LOG_FORMAT}
            ]
        )
        logger.add(
            "logs/apps_{time:YYYY-MM-DD}.log",
            rotation="00:00",
            format=LOG_FORMAT,
            level=settings.log_level,
        )


def configure_logger() -> None:
    # intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(LOG_LEVEL)

    # remove every other logger's handlers
    # and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # Configure logger (again) if gunicorn is not used
    logger.configure(
        handlers=[
            {"sink": sys.stdout, "level": settings.log_level, "format": LOG_FORMAT}
        ]
    )
    logger.add(
        "logs/apps_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        format=LOG_FORMAT,
        level=settings.log_level,
    )
