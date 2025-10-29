"""Logging configuration for PO File Translator — cross-platform UTF-8 safe"""
import logging
import sys
import os
from datetime import datetime

# ==========================================================
#  UTF-8 SAFE CONSOLE FIX (Windows / Linux / VS Code)
# ==========================================================
def _ensure_utf8_console():
    """Force UTF-8 output on all supported systems"""
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    # Force fallback for old Windows consoles
    os.environ["PYTHONIOENCODING"] = "utf-8"

_ensure_utf8_console()


# ==========================================================
#  COLORED FORMATTER
# ==========================================================
class ColoredFormatter(logging.Formatter):
    """Colorized output for console logs"""

    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


# ==========================================================
#  LOGGER FACTORY
# ==========================================================
def setup_logger(name="po_translator", level=logging.DEBUG, log_file=None):
    """Setup a UTF-8-safe, colored logger with optional file output"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger  # Avoid duplicates

    # --- Console handler (UTF-8 safe) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    try:
        # Ensure UTF-8 encoding on Windows logging stream
        if hasattr(console_handler.stream, "reconfigure"):
            console_handler.stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

    console_format = ColoredFormatter(
        "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # --- Optional file handler ---
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            "%(asctime)s %(levelname)-8s [%(name)s] %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def get_logger(name="po_translator"):
    """Get a preconfigured logger"""
    return logging.getLogger(name)
