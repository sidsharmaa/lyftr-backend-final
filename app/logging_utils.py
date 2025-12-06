import logging
import json
import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """
    Custom formatter to output logs as structured JSON objects.
    Adheres to requirements: one JSON line per request.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_object: Dict[str, Any] = {
            "ts": datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }

        if hasattr(record, "props"):
            log_object.update(record.props)
        else:
            standard_attrs = {
                'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                'funcName', 'levelname', 'levelno', 'lineno', 'module',
                'msecs', 'message', 'msg', 'name', 'pathname', 'process',
                'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName'
            }
            for key, value in record.__dict__.items():
                if key not in standard_attrs and not key.startswith('_'):
                    log_object[key] = value

        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_object)

def setup_logger(log_level: str):
    """
    Configures the root logger to use the JSONFormatter.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)

    if logger.handlers:
        logger.handlers = []

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    logging.getLogger("uvicorn.access").disabled = True