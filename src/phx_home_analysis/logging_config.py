"""
Centralized Logging Configuration for PHX Home Analysis.

Provides a unified logging setup with:
- Console handler with optional color support
- File handler for persistent logs
- JSON-formatted output option
- Consistent formatters across all modules

Usage:
    from phx_home_analysis.logging_config import setup_logging
    import logging

    setup_logging()  # Basic setup
    setup_logging(level=logging.DEBUG, log_file="analysis.log")  # With file output
    setup_logging(json_format=True)  # JSON output

    logger = logging.getLogger(__name__)
    logger.info("Analysis started")
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Default log format
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Color codes for console output (ANSI escape sequences)
COLORS = {
    "DEBUG": "\033[36m",     # Cyan
    "INFO": "\033[32m",      # Green
    "WARNING": "\033[33m",   # Yellow
    "ERROR": "\033[31m",     # Red
    "CRITICAL": "\033[35m",  # Magenta
    "RESET": "\033[0m",      # Reset
}


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds color to log level names for console output."""

    def __init__(self, fmt: str = DEFAULT_FORMAT, datefmt: str = DEFAULT_DATE_FORMAT):
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        # Save original level name
        original_levelname = record.levelname

        # Apply color if terminal supports it
        if sys.stdout.isatty():
            color = COLORS.get(record.levelname, "")
            reset = COLORS["RESET"]
            record.levelname = f"{color}{record.levelname}{reset}"

        # Format the message
        result = super().format(record)

        # Restore original level name
        record.levelname = original_levelname

        return result


class JSONFormatter(logging.Formatter):
    """Formatter that outputs log records as JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields if any
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)


def setup_logging(
    level: int = logging.INFO,
    log_file: str | None = None,
    json_format: bool = False,
    colored_console: bool = True,
    logger_name: str | None = None,
) -> logging.Logger:
    """Configure centralized logging for the application.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
            Default: logging.INFO
        log_file: Path to log file. If provided, logs will also be written to file.
            Default: None (console only)
        json_format: If True, output logs in JSON format.
            Default: False
        colored_console: If True, use colored output for console.
            Default: True
        logger_name: Specific logger to configure. If None, configures root logger.
            Default: None (root logger)

    Returns:
        The configured logger instance.

    Example:
        # Basic setup
        setup_logging()

        # Debug level with file output
        setup_logging(level=logging.DEBUG, log_file="logs/app.log")

        # JSON format for structured logging
        setup_logging(json_format=True, log_file="logs/app.json")
    """
    # Get the logger to configure
    logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()

    # Set the logging level
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Choose formatter based on options
    if json_format:
        console_formatter = JSONFormatter()
    elif colored_console:
        console_formatter = ColoredFormatter()
    else:
        console_formatter = logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT)

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Create file handler if log_file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)

        # Use JSON formatter for file if json_format is True, otherwise plain text
        if json_format:
            file_formatter = JSONFormatter()
        else:
            file_formatter = logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT)

        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger if configuring a specific logger
    if logger_name:
        logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    This is a convenience function that returns a logger configured
    to work with the centralized logging setup.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        Configured logger instance.

    Example:
        logger = get_logger(__name__)
        logger.info("Processing started")
    """
    return logging.getLogger(name)


# Convenience function for scripts that need simple setup
def setup_script_logging(
    script_name: str,
    level: int = logging.INFO,
    log_dir: str = "logs",
) -> logging.Logger:
    """Convenience function for setting up logging in standalone scripts.

    Creates a logger with both console and file output, with the log file
    named after the script and dated.

    Args:
        script_name: Name of the script (used for log file naming).
        level: Logging level. Default: logging.INFO
        log_dir: Directory for log files. Default: "logs"

    Returns:
        Configured logger instance.

    Example:
        logger = setup_script_logging("deal_sheets")
        logger.info("Generating deal sheets...")
    """
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = f"{log_dir}/{script_name}_{timestamp}.log"

    return setup_logging(level=level, log_file=log_file)
