"""
Абстрактный базовый класс API-клиента.

Согласно ТЗ, абстрактный класс содержит ТОЛЬКО объявления методов без реализации.
Реализация HTTP-запросов вынесена в отдельный миксин (src/api/mixins.py).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class BaseAPI(ABC):
    """Контракт для всех API-клиентов проекта."""

    @abstractmethod
    def get_coordinates(self, country_name: str) -> Optional[Tuple[float, float]]:
        """Получить географические координаты страны (широта, долгота)."""

    @abstractmethod
    def get_bounding_box(self, country_name: str) -> Optional[Tuple[float, float, float, float]]:
        """Получить ограничивающий прямоугольник страны (south, north, west, east)."""

    @abstractmethod
    def get_aeroplanes(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """Получить список воздушных судов по заданным параметрам."""
