"""Пакет утилит (логирование, форматированный вывод)."""

from src.utils.display import print_aeroplanes, print_avg_speed, print_countries_count
from src.utils.logger import setup_logging

__all__ = ["print_aeroplanes", "print_avg_speed", "print_countries_count", "setup_logging"]
