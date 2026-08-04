"""Colored terminal logger for VisionPass development logs."""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from typing import Literal

COLORS = {
    "RESET": "\033[0m",
    "BOLD": "\033[1m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "CYAN": "\033[96m",
    "MAGENTA": "\033[95m",
    "BLUE": "\033[94m",
    "WHITE": "\033[97m",
    "GRAY": "\033[90m",
}

Tone = Literal["green", "yellow", "red", "blue", "gray"]

TONE_COLORS: dict[Tone, str] = {
    "green": COLORS["GREEN"],
    "yellow": COLORS["YELLOW"],
    "red": COLORS["RED"],
    "blue": COLORS["BLUE"],
    "gray": COLORS["GRAY"],
}

TONE_SYMBOLS: dict[Tone, str] = {
    "green": "✓",
    "yellow": "⚠",
    "red": "✗",
    "blue": "ℹ",
    "gray": "•",
}


class ColorFormatter(logging.Formatter):
    LEVEL_TONES: dict[str, Tone] = {
        "DEBUG": "gray",
        "INFO": "blue",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red",
    }

    def format(self, record: logging.LogRecord) -> str:
        tone_name = getattr(record, "tone", None) or self.LEVEL_TONES.get(record.levelname, "blue")
        tone = TONE_COLORS.get(tone_name, COLORS["BLUE"])
        symbol = getattr(record, "symbol", None) or TONE_SYMBOLS.get(tone_name, "•")
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = record.getMessage()
        line = f"[{timestamp}] {symbol} {message}"
        if record.levelno >= logging.ERROR and record.exc_info:
            return f"{tone}{line}{COLORS['RESET']}\n{self.formatException(record.exc_info)}"
        return f"{tone}{line}{COLORS['RESET']}"


def configure_logging(debug: bool = False) -> None:
    def build_handler() -> logging.Handler:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(ColorFormatter())
        return handler

    def configure_named_logger(name: str, level: int, *, replace_handlers: bool = True) -> None:
        named_logger = logging.getLogger(name)
        if replace_handlers:
            named_logger.handlers.clear()
        named_logger.addHandler(build_handler())
        named_logger.setLevel(level)
        named_logger.propagate = False

    root = logging.getLogger()
    if getattr(root, "_visionpass_configured", False):
        root.setLevel(logging.DEBUG if debug else logging.INFO)
        return

    root.handlers.clear()
    root.addHandler(build_handler())
    root.setLevel(logging.DEBUG if debug else logging.INFO)
    root._visionpass_configured = True  # type: ignore[attr-defined]

    logging.captureWarnings(True)
    configure_named_logger("uvicorn", logging.DEBUG if debug else logging.INFO)
    configure_named_logger("uvicorn.error", logging.DEBUG if debug else logging.INFO)
    configure_named_logger("uvicorn.access", logging.INFO)
    configure_named_logger("fastapi", logging.DEBUG if debug else logging.INFO)

    if not debug:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)


def _log_with_tone(logger: logging.Logger, level: int, message: str, *, tone: Tone, symbol: str) -> None:
    logger.log(level, message, extra={"tone": tone, "symbol": symbol})


def log_system(logger: logging.Logger, message: str) -> None:
    _log_with_tone(logger, logging.INFO, message, tone="blue", symbol="ℹ")


def log_success(logger: logging.Logger, message: str) -> None:
    _log_with_tone(logger, logging.INFO, message, tone="green", symbol="✓")


def log_warning(logger: logging.Logger, message: str) -> None:
    _log_with_tone(logger, logging.WARNING, message, tone="yellow", symbol="⚠")


def log_error(logger: logging.Logger, message: str, *, exc_info: bool | BaseException | tuple | None = None) -> None:
    logger.error(message, extra={"tone": "red", "symbol": "✗"}, exc_info=exc_info)


def log_debug(logger: logging.Logger, message: str) -> None:
    _log_with_tone(logger, logging.DEBUG, message, tone="gray", symbol="•")
