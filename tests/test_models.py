from typing import Any, Dict, Optional

import pytest

from src.models.aeroplane import Aeroplane


def test_from_api_state_valid(sample_api_state: Dict[str, Any]) -> None:
    """Проверяет корректное создание объекта из валидного словаря."""
    plane = Aeroplane.from_api_state(sample_api_state)
    assert plane is not None
    assert plane.callsign == "TEST123"  # Проверяем, что сработал strip()
    assert plane.icao24 == "abc123"


@pytest.mark.parametrize(
    "velocity, expected_velocity",
    [
        (100.0, 100.0),
        (-50.0, 0.0),  # Отрицательная скорость должна стать 0.0
        (None, None),
    ],
)
def test_velocity_correction(
    sample_api_state: Dict[str, Any], velocity: Optional[float], expected_velocity: Optional[float]
) -> None:
    """Проверяет коррекцию отрицательной скорости."""
    sample_api_state["velocity"] = velocity
    plane = Aeroplane.from_api_state(sample_api_state)
    assert plane is not None
    assert plane.velocity == expected_velocity


@pytest.mark.parametrize(
    "baro_alt, geo_alt, expected_altitude",
    [
        (1000.0, 1000.0, 1000.0),  # Оба валидны
        (-10.0, -10.0, 0.0),  # Отрицательная высота должна стать 0.0
        (None, None, None),  # Обе высоты None -> результат None (Исправляет ошибку)
        (None, 500.0, 500.0),  # baro_alt None, но есть geo_alt -> берется geo_alt
    ],
)
def test_altitude_correction(
    sample_api_state: Dict[str, Any],
    baro_alt: Optional[float],
    geo_alt: Optional[float],
    expected_altitude: Optional[float],
) -> None:
    """Проверяет коррекцию высоты с учетом приоритета baro_altitude и geo_altitude."""
    sample_api_state["baro_altitude"] = baro_alt
    sample_api_state["geo_altitude"] = geo_alt
    plane = Aeroplane.from_api_state(sample_api_state)
    assert plane is not None
    assert plane.altitude == expected_altitude


@pytest.mark.parametrize(
    "latitude, expected_latitude",
    [
        (45.0, 45.0),
        (-100.0, None),  # Некорректная широта сбрасывается в None
        (None, None),
    ],
)
def test_latitude_correction(
    sample_api_state: Dict[str, Any], latitude: Optional[float], expected_latitude: Optional[float]
) -> None:
    """Проверяет сброс некорректной широты."""
    sample_api_state["latitude"] = latitude
    plane = Aeroplane.from_api_state(sample_api_state)
    assert plane is not None
    assert plane.latitude == expected_latitude


@pytest.mark.parametrize(
    "longitude, expected_longitude",
    [
        (45.0, 45.0),
        (200.0, None),  # Некорректная долгота сбрасывается в None
        (None, None),
    ],
)
def test_longitude_correction(
    sample_api_state: Dict[str, Any], longitude: Optional[float], expected_longitude: Optional[float]
) -> None:
    """Проверяет сброс некорректной долготы (добавлено для полного покрытия)."""
    sample_api_state["longitude"] = longitude
    plane = Aeroplane.from_api_state(sample_api_state)
    assert plane is not None
    assert plane.longitude == expected_longitude


def test_empty_callsign_returns_none(sample_api_state: Dict[str, Any]) -> None:
    """Самолёт с пустым позывным должен возвращать None."""
    sample_api_state["callsign"] = "   "
    plane = Aeroplane.from_api_state(sample_api_state)
    assert plane is None


def test_to_db_tuple(sample_aeroplane: Aeroplane) -> None:
    """Проверяет формирование кортежа для вставки в БД."""
    country_id = 42
    db_tuple = sample_aeroplane.to_db_tuple(country_id)

    assert isinstance(db_tuple, tuple)
    assert len(db_tuple) == 10
    assert db_tuple[3] == country_id  # airspace_country_id на 4-й позиции
    assert db_tuple[1] == "TEST123"  # callsign


def test_empty_callsign_raises_value_error() -> None:
    """
    Строка 35: Прямой вызов конструктора с пустым callsign вызывает ValueError.
    (В from_api_state это перехватывается и возвращается None, но __post_init__ падает).
    """
    with pytest.raises(ValueError, match="callsign не может быть пустым"):
        Aeroplane(
            icao24="abc",
            callsign="   ",
            origin_country="X",
            velocity=None,
            altitude=None,
            on_ground=False,
            latitude=None,
            longitude=None,
            last_contact=None,
        )


def test_from_api_state_invalid_data_returns_none(sample_api_state: Dict[str, Any]) -> None:
    """
    Строки 86-88: Невалидные данные (например, строка вместо int) вызывают исключение,
    которое перехватывается, и метод возвращает None.
    """
    sample_api_state["last_contact"] = "not_an_int"  # Вызовет ValueError при int()
    plane = Aeroplane.from_api_state(sample_api_state)
    assert plane is None
