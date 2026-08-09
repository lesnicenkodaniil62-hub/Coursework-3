"""API-клиент для OpenSky Network: данные о воздушных судах в реальном времени."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.api.base import BaseAPI
from src.api.mixins import RequestMixin

logger = logging.getLogger(__name__)


class OpenSkyAPI(RequestMixin, BaseAPI):
    """Клиент сервиса OpenSky Network для получения состояний воздушных судов."""

    OPENSKY_URL: str = "https://opensky-network.org/api"

    STATE_KEYS: List[str] = [
        "icao24",
        "callsign",
        "origin_country",
        "time_position",
        "last_contact",
        "longitude",
        "latitude",
        "baro_altitude",
        "on_ground",
        "velocity",
        "heading",
        "vertical_rate",
        "sensors",
        "geo_altitude",
        "squawk",
        "spi",
        "position_source",
    ]

    def __init__(self, timeout: int = 15, user_agent: str = "AeroplanesApp/1.0") -> None:
        """Инициализирует клиент OpenSky."""
        super().__init__(base_url=self.OPENSKY_URL, timeout=timeout, user_agent=user_agent)

    def get_coordinates(self, country_name: str) -> Optional[Tuple[float, float]]:
        """OpenSky не предоставляет геокодирование. Возвращает None."""
        return None

    def get_bounding_box(self, country_name: str) -> Optional[Tuple[float, float, float, float]]:
        """OpenSky не предоставляет bounding box. Возвращает None."""
        return None

    def get_aeroplanes(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Получить самолёты. Поддерживает фильтрацию по стране или bounding box.

        :param kwargs: 'country' — имя страны, либо 'bbox' — (south, north, west, east)
        :return: список словарей с данными о воздушных судах
        """
        params: Dict[str, Any] = {}
        if "country" in kwargs:
            params["country"] = kwargs["country"]
        elif "bbox" in kwargs:
            south, north, west, east = kwargs["bbox"]
            params["lamin"] = south
            params["lamax"] = north
            params["lomin"] = west
            params["lomax"] = east

        data = self._make_request("states/all", params=params)
        if isinstance(data, dict) and "states" in data:
            return self._parse_states(data["states"])
        return []

    def _parse_states(self, raw_states: Optional[List[List[Any]]]) -> List[Dict[str, Any]]:
        """Преобразует сырой ответ OpenSky (список списков) в список словарей."""
        if not raw_states:
            return []
        parsed: List[Dict[str, Any]] = []
        for state in raw_states:
            if isinstance(state, list) and len(state) >= len(self.STATE_KEYS):
                parsed.append(dict(zip(self.STATE_KEYS, state)))
        return parsed
