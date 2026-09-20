"""
logger_config.py
-----------------
Sets up a single shared logger used across every stage of the pipeline
(extract, validate, transform, load). Writes to both console and a
rotating log file so a full execution history is always on disk.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

import config


def get_logger(name: str = "etl_pipeline") -> logging.Logger:
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:  # avoid duplicate handlers on re-import
        return logger

    logger.setLevel(config.LOG_LEVEL)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        config.LOG_FILE, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
