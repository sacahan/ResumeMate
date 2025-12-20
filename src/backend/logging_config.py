"""Logging configuration for ResumeMate.

Provides a single place to configure logging handlers/formatters.
- Console: colorized, compact, includes source line number.
- File: detailed, rotated, configured via environment variables.
"""

from __future__ import annotations

import logging
import os
from logging.config import dictConfig
from pathlib import Path

LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
)


class ColorFormatter(logging.Formatter):
    """彩色日誌格式化器，用於控制台輸出"""

    RESET = "\x1b[0m"
    DIM = "\x1b[38;5;245m"
    LOGGER_COLOR = "\x1b[38;5;141m"
    LOCATION_COLOR = "\x1b[38;5;244m"
    SEPARATOR_COLOR = "\x1b[38;5;242m"
    MESSAGE_COLOR = "\x1b[38;5;255m"

    LEVEL_COLORS = {
        "DEBUG": "\x1b[38;5;245m",
        "INFO": "\x1b[38;5;39m",
        "WARNING": "\x1b[38;5;220m",
        "ERROR": "\x1b[38;5;196m",
        "CRITICAL": "\x1b[48;5;196m\x1b[38;5;15m",
    }

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, datefmt=self.datefmt or LOG_DATE_FORMAT)
        level = record.levelname
        name = record.name
        location = f"{record.filename}:{record.lineno}"
        msg = record.getMessage()

        level_color = self.LEVEL_COLORS.get(record.levelname, "")
        sep = f" {self.SEPARATOR_COLOR}|{self.RESET} "

        line = (
            f"{self.DIM}{timestamp}{self.RESET}"
            f"{sep}{level_color}{level}{self.RESET}"
            f"{sep}{self.LOGGER_COLOR}{name}{self.RESET}"
            f"{sep}{self.LOCATION_COLOR}{location}{self.RESET}"
            f"{sep}{self.MESSAGE_COLOR}{msg}{self.RESET}"
        )

        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            exc_color = level_color or self.DIM
            line = f"{line}\n{exc_color}{exc_text}{self.RESET}"

        return line


def _parse_level(level: str, default: int) -> int:
    """解析日誌級別字串"""
    if not level:
        return default
    return logging._nameToLevel.get(level.upper(), default)


def configure_logging(
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    log_file: str | None = None,
    log_file_max_bytes: int = 10 * 1024 * 1024,  # 10MB
    log_file_backup_count: int = 5,
) -> None:
    """配置日誌系統

    Args:
        console_level: 控制台日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        file_level: 檔案日誌級別
        log_file: 日誌檔案路徑，None 則不寫入檔案
        log_file_max_bytes: 單個日誌檔案最大大小
        log_file_backup_count: 保留的舊日誌檔案數量
    """

    console_log_level = _parse_level(console_level, logging.INFO)
    file_log_level = _parse_level(file_level, logging.DEBUG)

    handlers: dict[str, dict] = {
        "console": {
            "class": "logging.StreamHandler",
            "level": console_log_level,
            "formatter": "console",
            "stream": "ext://sys.stdout",
        }
    }

    root_handlers = ["console"]

    if log_file:
        log_path = Path(log_file).expanduser()
        if not log_path.is_absolute():
            log_path = Path(os.getcwd()) / log_path

        log_path.parent.mkdir(parents=True, exist_ok=True)

        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": file_log_level,
            "formatter": "file",
            "filename": str(log_path),
            "maxBytes": log_file_max_bytes,
            "backupCount": log_file_backup_count,
            "encoding": "utf-8",
        }
        root_handlers.append("file")

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {
                "()": "src.backend.logging_config.ColorFormatter",
                "format": LOG_FORMAT,
                "datefmt": LOG_DATE_FORMAT,
            },
            "file": {
                "format": LOG_FORMAT,
                "datefmt": LOG_DATE_FORMAT,
            },
        },
        "handlers": handlers,
        "root": {
            "level": logging.DEBUG,
            "handlers": root_handlers,
        },
        "loggers": {
            # Gradio 相關日誌
            "gradio": {
                "level": console_log_level,
                "handlers": root_handlers,
                "propagate": False,
            },
            # OpenAI Agents SDK 相關日誌
            "agents": {
                "level": console_log_level,
                "handlers": root_handlers,
                "propagate": False,
            },
            # LiteLLM 相關日誌 - 設定為 WARNING 以關閉 DEBUG 輸出
            "litellm": {
                "level": logging.WARNING,  # 只顯示 WARNING 以上的日誌
                "handlers": root_handlers,
                "propagate": False,
            },
            "LiteLLM": {
                "level": logging.WARNING,  # LiteLLM 使用大寫的 logger 名稱
                "handlers": root_handlers,
                "propagate": False,
            },
        },
    }

    dictConfig(config)
