"""Модель воздушного судна с валидацией данных и коррекцией отрицательных значений."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class Aeroplane:
    """Модель воздушного судна."""

    icao24: str
    callsign: str
    origin_country: str
    velocity: Optional[float]
    altitude: Optional[float]
    on_ground: bool
    latitude: Optional[float]
    longitude: Optional[float]
    last_contact: Optional[int]

    def __post_init__(self) -> None:
        """Выполняет валидацию и коррекцию данных после инициализации."""
        self.validate_and_correct()

    def validate_and_correct(self) -> None:
        """
        Проверяет и корректирует все атрибуты.
        Отрицательная высота и скорость автоматически устанавливаются в 0.0.
        Некорректные координаты сбрасываются в None.
        """
        if not self.callsign or not self.callsign.strip():
            raise ValueError("callsign не может быть пустым")

        if self.velocity is not None and self.velocity < 0:
            logger.warning(
                "Самолет %s: отрицательная скорость %.2f м/с, устанавливаем в 0.0", self.callsign, self.velocity
            )
            self.velocity = 0.0

        if self.altitude is not None and self.altitude < 0:
            logger.warning(
                "Самолет %s: отрицательная высота %.2f м, устанавливаем в 0.0", self.callsign, self.altitude
            )
            self.altitude = 0.0

        if self.latitude is not None and not (-90 <= self.latitude <= 90):
            logger.warning("Самолет %s: некорректная широта %.6f, устанавливаем в None", self.callsign, self.latitude)
            self.latitude = None

        if self.longitude is not None and not (-180 <= self.longitude <= 180):
            logger.warning(
                "Самолет %s: некорректная долгота %.6f, устанавливаем в None", self.callsign, self.longitude
            )
            self.longitude = None

    @classmethod
    def from_api_state(cls, state: Dict[str, Any]) -> Optional["Aeroplane"]:
        """
        Создаёт объект Aeroplane из словаря, полученного от OpenSky API.

        :param state: словарь с данными о воздушном судне
        :return: объект Aeroplane либо None, если запись некорректна
        """
        try:
            callsign = str(state.get("callsign") or "").strip()
            if not callsign:
                return None

            velocity_raw = state.get("velocity")
            altitude_raw = state.get("baro_altitude") or state.get("geo_altitude")

            return cls(
                icao24=str(state.get("icao24") or ""),
                callsign=callsign,
                origin_country=str(state.get("origin_country") or ""),
                velocity=float(velocity_raw) if velocity_raw is not None else None,
                altitude=float(altitude_raw) if altitude_raw is not None else None,
                on_ground=bool(state.get("on_ground", False)),
                latitude=float(state["latitude"]) if state.get("latitude") is not None else None,
                longitude=float(state["longitude"]) if state.get("longitude") is not None else None,
                last_contact=int(state["last_contact"]) if state.get("last_contact") is not None else None,
            )
        except (ValueError, TypeError, KeyError) as exc:
            logger.warning("Не удалось преобразовать запись в Aeroplane: %s", exc)
            return None

    def to_db_tuple(self, airspace_country_id: int) -> Tuple:
        """
        Возвращает кортеж значений для вставки в таблицу airplanes.

        :param airspace_country_id: ID страны, в воздушном пространстве которой находится судно
        :return: кортеж параметров для SQL-запроса
        """
        return (
            self.icao24,
            self.callsign,
            self.origin_country,
            airspace_country_id,
            self.velocity,
            self.altitude,
            self.on_ground,
            self.latitude,
            self.longitude,
            self.last_contact,
        )
