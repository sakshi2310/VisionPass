"""Colored terminal logger for VisionPass development logs."""

from __future__ import annotations

import logging
import sys
from datetime import datetime

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


class ColorFormatter(logging.Formatter):
    LEVEL_COLORS = {
        "DEBUG": COLORS["GRAY"],
        "INFO": COLORS["GREEN"],
        "WARNING": COLORS["YELLOW"],
        "ERROR": COLORS["RED"],
        "CRITICAL": COLORS["RED"] + COLORS["BOLD"],
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelname, COLORS["RESET"])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = f"{color}[{record.levelname}]{COLORS['RESET']}"
        module = f"{COLORS['CYAN']}[{record.name}]{COLORS['RESET']}"
        message = f"{color}{record.getMessage()}{COLORS['RESET']}"
        return f"{COLORS['GRAY']}{timestamp}{COLORS['RESET']} {level} {module} {message}"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(ColorFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
    return logger
