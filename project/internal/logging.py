import logging.config
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = f'{BASE_DIR}/logs'

if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s.%(msecs)03d %(levelname)s %(name)s %(funcName)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": f"{LOG_DIR}/apps-{datetime.now().strftime('%Y%m%d')}.log",
            "when": "midnight",
            "backupCount": 90,
            "formatter": "default",
        },
    },
    "loggers": {
        "gunicorn": {
            "propagate": False
        },
        "uvicorn": {
            "propagate": True
        },
        "uvicorn.access": {
            "propagate": True
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    }
}

app_logger = logging.getLogger('apps')
