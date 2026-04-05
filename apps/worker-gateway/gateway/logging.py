"""
Structured JSON logging for the worker gateway.
"""

import json
import logging
import sys

from .config import settings


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "ts": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_obj["exc"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging() -> logging.Logger:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logging.root.handlers = [handler]
    logging.root.setLevel(settings.log_level.upper())
    return logging.getLogger("worker-gateway")


logger = setup_logging()
