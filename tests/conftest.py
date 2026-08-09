from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest

from src.api.nominatim import NominatimAPI
from src.api.opensky import OpenSkyAPI
from src.database.manager import DBManager
from src.models.aeroplane import Aeroplane


@pytest.fixture
def sample_api_state() -> Dict[str, Any]:
    """Возвращает валидный словарь с данными о самолёте от OpenSky API."""
    return {
        "icao24": "abc123",
        "callsign": "TEST123 ",
        "origin_country": "TestCountry",
        "time_position": 1600000000,
        "last_contact": 1600000000,
        "longitude": 10.5,
        "latitude": 20.5,
        "baro_altitude": 1000.0,
        "on_ground": False,
        "velocity": 250.5,
        "heading": 90.0,
        "vertical_rate": 0.0,
        "sensors": [],
        "geo_altitude": 1000.0,
        "squawk": "1234",
        "spi": False,
        "position_source": "ADS-B",
    }


@pytest.fixture
def sample_aeroplane(sample_api_state: Dict[str, Any]) -> Aeroplane:
    """Возвращает валидный объект Aeroplane на основе фикстуры."""
    plane = Aeroplane.from_api_state(sample_api_state)
    assert plane is not None, "Не удалось создать Aeroplane из sample_api_state"
    return plane


@pytest.fixture
def nominatim_api() -> NominatimAPI:
    """Фикстура для NominatimAPI."""
    return NominatimAPI()


@pytest.fixture
def opensky_api() -> OpenSkyAPI:
    """Фикстура для OpenSkyAPI."""
    return OpenSkyAPI()


@pytest.fixture
def mock_db_manager() -> DBManager:
    """Фикстура для DBManager с тестовыми параметрами подключения."""
    db_params: Dict[str, Any] = {
        "dbname": "testdb",
        "user": "testuser",
        "password": "testpass",
        "host": "localhost",
    }
    return DBManager(db_params=db_params)


@pytest.fixture
def mock_db_connection(mock_db_manager: DBManager) -> Generator[MagicMock, None, None]:
    """
    Фикстура для мока подключения к БД.

    Патчит DBManager._connect, чтобы менеджер использовал mock_conn.
    Это важно, потому что DBManager использует closing(...),
    а не конструкцию with psycopg2.connect(...) as conn.
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # conn.cursor(...) as cur -> cur должен быть mock_cursor
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    with patch.object(mock_db_manager, "_connect") as mock_connect:
        mock_connect.return_value = mock_conn
        yield mock_cursor
