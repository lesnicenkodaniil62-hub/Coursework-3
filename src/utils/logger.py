"""Модуль настройки логирования приложения (только в файл)."""

import logging
from pathlib import Path


def setup_logging(level: int = logging.INFO) -> None:
    """
    Настраивает логирование ТОЛЬКО в файл logs/app.log.
    Консольный вывод отключен для чистоты пользовательских данных.
    """
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("psycopg2").setLevel(logging.WARNING)

    root_logger.info("=" * 70)
    root_logger.info("Система мониторинга воздушного пространства запущена")
    root_logger.info("Лог-файл: %s", log_file.absolute())
    root_logger.info("=" * 70)
