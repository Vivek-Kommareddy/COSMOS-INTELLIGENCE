"""Structured JSON logger for CloudWatch-compatible output."""
from __future__ import annotations

import json
import logging
import sys
import time
from contextlib import contextmanager
from typing import Any, Generator


class _JSONFormatter(logging.Formatter):
    """Emit each log record as a single JSON line (CloudWatch-friendly)."""

    _SKIP = frozenset(
        {
            "args", "created", "exc_info", "exc_text", "filename",
            "funcName", "levelname", "levelno", "lineno", "message",
            "module", "msecs", "msg", "name", "pathname", "process",
            "processName", "relativeCreated", "stack_info", "thread",
            "threadName", "asctime",
        }
    )

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        obj: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
        }
        # Attach any extra fields passed via logger.info(..., extra={...})
        for key, value in record.__dict__.items():
            if key not in self._SKIP:
                obj[key] = value
        if record.exc_info:
            obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(obj, default=str)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Return a logger that emits structured JSON to stdout.

    Calling this multiple times with the same name is safe; handlers are
    attached only once.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(_JSONFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


@contextmanager
def log_stage(logger: logging.Logger, stage: str) -> Generator[None, None, None]:
    """Context manager that logs start/complete/failed for a pipeline stage."""
    start = time.perf_counter()
    logger.info("stage_start", extra={"stage": stage})
    try:
        yield
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info("stage_complete", extra={"stage": stage, "elapsed_ms": elapsed_ms})
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.error(
            "stage_failed",
            extra={"stage": stage, "elapsed_ms": elapsed_ms, "error": str(exc)},
            exc_info=True,
        )
        raise
