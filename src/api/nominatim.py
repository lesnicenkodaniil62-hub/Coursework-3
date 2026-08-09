"""API-клиент для Nominatim (OpenStreetMap): геокодирование стран."""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple, cast

from src.api.base import BaseAPI
from src.api.mixins import RequestMixin

logger = logging.getLogger(__name__)


class NominatimAPI(RequestMixin, BaseAPI):
    """Клиент сервиса Nominatim для получения координат и bounding box стран."""

    NOMINATIM_URL: str = "https://nominatim.openstreetmap.org"
    REQUEST_DELAY: float = 1.1

    def __init__(self, timeout: int = 10, user_agent: str = "AeroplanesApp/1.0 (educational-project)") -> None:
        """Инициализирует клиент Nominatim."""
        super().__init__(base_url=self.NOMINATIM_URL, timeout=timeout, user_agent=user_agent)

    def _search(self, country_name: str) -> Optional[Dict[str, Any]]:
        """
        Выполняет запрос search и возвращает первый результат либо None.

        :param country_name: название страны для поиска
        :return: словарь с данными о стране или None
        """
        params: Dict[str, Any] = {"q": country_name.strip(), "format": "json", "limit": 1}
        data = self._make_request("search", params=params)
        time.sleep(self.REQUEST_DELAY)
        if isinstance(data, list) and data:
            # Используем cast для явного приведения типа
            return cast(Dict[str, Any], data[0])
        return None

    def get_coordinates(self, country_name: str) -> Optional[Tuple[float, float]]:
        """Получить географические координаты страны (широта, долгота)."""
        result = self._search(country_name)
        if result:
            try:
                return float(result["lat"]), float(result["lon"])
            except (KeyError, ValueError, TypeError) as exc:
                logger.error("Ошибка парсинга координат для %s: %s", country_name, exc)
        return None

    def get_bounding_box(self, country_name: str) -> Optional[Tuple[float, float, float, float]]:
        """Получить bounding box страны в порядке (south, north, west, east)."""
        result = self._search(country_name)
        if result:
            bbox = result.get("boundingbox")
            if isinstance(bbox, list) and len(bbox) == 4:
                try:
                    south, north, west, east = (float(x) for x in bbox)
                    return south, north, west, east
                except (ValueError, TypeError) as exc:
                    logger.error("Ошибка парсинга bbox для %s: %s", country_name, exc)
        return None

    def get_aeroplanes(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """Nominatim не предоставляет данные о самолётах. Возвращает пустой список."""
        return []
