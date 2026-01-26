"""Structured logging setup."""
import logging
import sys
from typing import Any


def hyperlink(url: str, text: str) -> str:
    """Create a clickable terminal hyperlink (OSC 8)."""
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"


# ANSI color codes
COLORS = {
    "DEBUG": "\033[90m",     # Gray
    "INFO": "\033[36m",      # Cyan
    "WARNING": "\033[33m",   # Yellow
    "ERROR": "\033[31m",     # Red
    "RESET": "\033[0m",
    "DIM": "\033[2m",
    "GREEN": "\033[32m",
    "RED": "\033[31m",
}


def colored(text: str, color: str) -> str:
    """Wrap text in ANSI color codes."""
    return f"{COLORS.get(color, '')}{text}{COLORS['RESET']}"


class StructuredFormatter(logging.Formatter):
    """Formatter that outputs structured key-value pairs with colors."""

    def format(self, record: logging.LogRecord) -> str:
        color = COLORS.get(record.levelname, "")
        reset = COLORS["RESET"]
        dim = COLORS["DIM"]

        # Base message with colored level
        base = f"{color}{record.levelname:<8}{reset} {dim}{record.name}:{reset} {record.getMessage()}"

        # Add any extra key-value pairs
        extras = []
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "taskName",
                "message",
            }:
                extras.append(f"{key}={value}")

        if extras:
            return f"{base} | {' '.join(extras)}"
        return base


class StructuredLogger(logging.Logger):
    """Logger that supports structured key-value logging."""

    def _log_with_extras(
        self,
        level: int,
        msg: str,
        args: tuple,
        exc_info: Any = None,
        extra: dict | None = None,
        **kwargs: Any,
    ) -> None:
        if extra is None:
            extra = {}
        extra.update(kwargs)
        super()._log(level, msg, args, exc_info=exc_info, extra=extra)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(logging.DEBUG):
            self._log_with_extras(logging.DEBUG, msg, args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(logging.INFO):
            self._log_with_extras(logging.INFO, msg, args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(logging.WARNING):
            self._log_with_extras(logging.WARNING, msg, args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(logging.ERROR):
            self._log_with_extras(logging.ERROR, msg, args, **kwargs)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    logging.setLoggerClass(StructuredLogger)
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger  # type: ignore
