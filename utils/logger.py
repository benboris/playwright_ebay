"""
Logger Setup - הגדרת לוגינג אחיד לכל הפרויקט.
"""
import logging
import os
from datetime import datetime


def setup_logger(log_dir: str = "reports/logs", level: int = logging.INFO) -> logging.Logger:
    """
    Configure root logger with console and rotating file handlers.
    Returns the root logger.
    """
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"test_run_{timestamp}.log")

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)-20s │ %(message)s",
        datefmt="%H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(fmt)

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(console_handler)
    root.addHandler(file_handler)

    logging.getLogger("playwright").setLevel(logging.WARNING)
    root.info(f"Logger initialised – log file: {log_file}")
    return root
