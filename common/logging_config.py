"""
Logging configuration and logger implementation.

Proporciona un sistema de logging centralizado, injectable y fácilmente
configurable para cambiar estilos, niveles y formatos.
"""

from enum import Enum
from typing import Optional, Dict
from datetime import datetime
from pathlib import Path
from .constants import TIMESTAMP_FORMAT, DATETIME_FORMAT


class LogLevel(str, Enum):
    """Log levels enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ANSIColors:
    """ANSI color codes for terminal output."""

    RESET = '\033[0m'
    CYAN = '\033[0;36m'      # Info
    GREEN = '\033[0;32m'     # Success
    YELLOW = '\033[0;33m'    # Warning
    RED = '\033[0;31m'       # Error
    GRAY = '\033[0;90m'      # Debug

    @classmethod
    def get_color(cls, level: LogLevel) -> str:
        """
        Get ANSI color code for a log level.

        Args:
            level: The log level.

        Returns:
            ANSI color code string.
        """
        color_map: Dict[LogLevel, str] = {
            LogLevel.DEBUG: cls.GRAY,
            LogLevel.INFO: cls.CYAN,
            LogLevel.SUCCESS: cls.GREEN,
            LogLevel.WARNING: cls.YELLOW,
            LogLevel.ERROR: cls.RED,
        }
        return color_map.get(level, cls.CYAN)


class Logger:
    """
    Centralized logger for the application.

    Proporciona métodos para logging con colores ANSI, timestamp y
    persistencia en archivos cuando sea necesario.
    """

    def __init__(
        self,
        use_colors: bool = True,
        min_level: LogLevel = LogLevel.DEBUG,
    ) -> None:
        """
        Initialize the logger.

        Args:
            use_colors: Whether to use ANSI colors in output.
            min_level: Minimum log level to display.
        """
        self.use_colors = use_colors
        self.min_level = min_level
        self._error_dump_dir: Optional[Path] = None

    def set_error_dump_dir(self, directory: Path) -> None:
        """
        Set the directory for error dumps.

        Args:
            directory: Path to the error dump directory.
        """
        self._error_dump_dir = directory

    def _format_message(
        self,
        level: LogLevel,
        message: str,
    ) -> str:
        """
        Format a log message with level and timestamp.

        Args:
            level: The log level.
            message: The message to format.

        Returns:
            Formatted message string.
        """
        if self.use_colors:
            color = ANSIColors.get_color(level)
            reset = ANSIColors.RESET
            return f"{color}[{level.value}]{reset} {message}"
        else:
            return f"[{level.value}] {message}"

    def _should_log(self, level: LogLevel) -> bool:
        """
        Determine if a message should be logged based on level.

        Args:
            level: The log level to check.

        Returns:
            True if the message should be logged.
        """
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.SUCCESS: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
        }
        return level_order.get(level, 1) >= level_order.get(self.min_level, 1)

    def debug(self, message: str) -> None:
        """Log a debug message."""
        if self._should_log(LogLevel.DEBUG):
            print(self._format_message(LogLevel.DEBUG, message))

    def info(self, message: str) -> None:
        """Log an info message."""
        if self._should_log(LogLevel.INFO):
            print(self._format_message(LogLevel.INFO, message))

    def success(self, message: str) -> None:
        """Log a success message."""
        if self._should_log(LogLevel.SUCCESS):
            print(self._format_message(LogLevel.SUCCESS, message))

    def warning(self, message: str) -> None:
        """Log a warning message."""
        if self._should_log(LogLevel.WARNING):
            print(self._format_message(LogLevel.WARNING, message))

    def error(self, message: str) -> None:
        """Log an error message."""
        if self._should_log(LogLevel.ERROR):
            print(self._format_message(LogLevel.ERROR, message))

    def section(self, title: str) -> None:
        """
        Log a section header.

        Args:
            title: The section title.
        """
        print()
        separator = "═" * 70
        if self.use_colors:
            color = ANSIColors.CYAN
            reset = ANSIColors.RESET
            print(f"{color}{separator}{reset}")
            print(f"{color}  {title}{reset}")
            print(f"{color}{separator}{reset}")
        else:
            print(separator)
            print(f"  {title}")
            print(separator)

    def dump_error(
        self,
        error_message: str,
        exception: Optional[Exception] = None,
    ) -> Path:
        """
        Save error dump to file.

        Args:
            error_message: The error message.
            exception: Optional exception object with traceback.

        Returns:
            Path to the error dump file.

        Raises:
            RuntimeError: If error dump directory not configured.
        """
        if not self._error_dump_dir:
            raise RuntimeError("Error dump directory not configured")

        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
        error_file = self._error_dump_dir / f"error_dump_{timestamp}.log"

        try:
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(
                    f"=== ERROR DUMP - "
                    f"{datetime.now().isoformat()} ===\n\n"
                )
                f.write(f"Error Message: {error_message}\n\n")

                if exception:
                    import traceback
                    f.write(f"Exception Type: {type(exception).__name__}\n")
                    f.write(f"Exception Message: {str(exception)}\n\n")
                    f.write("Full Traceback:\n")
                    f.write(traceback.format_exc())
                    f.write("\n")

                f.write("=== END ERROR DUMP ===\n")

            self.debug(f"Error dump guardado en: {error_file}")
            return error_file

        except Exception as log_err:
            self.error(f"Error al guardar dump de error: {log_err}")
            self.error(f"Error original: {error_message}")
            if exception:
                self.error(f"Excepción original: {exception}")
            raise


# Global logger instance
_logger: Optional[Logger] = None


def get_logger() -> Logger:
    """
    Get the global logger instance.

    Returns:
        The global Logger instance.
    """
    global _logger
    if _logger is None:
        _logger = Logger(use_colors=True)
    return _logger


def initialize_logger(
    use_colors: bool = True,
    min_level: LogLevel = LogLevel.DEBUG,
    error_dump_dir: Optional[Path] = None,
) -> Logger:
    """
    Initialize the global logger.

    Args:
        use_colors: Whether to use ANSI colors.
        min_level: Minimum log level to display.
        error_dump_dir: Directory for error dumps.

    Returns:
        The initialized Logger instance.
    """
    global _logger
    _logger = Logger(use_colors=use_colors, min_level=min_level)
    if error_dump_dir:
        _logger.set_error_dump_dir(error_dump_dir)
    return _logger
