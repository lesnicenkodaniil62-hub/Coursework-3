from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import psycopg2
import pytest

from src.api.nominatim import NominatimAPI
from src.api.opensky import OpenSkyAPI
from src.database.populator import populate_airplanes, populate_countries


def test_populate_countries_success(nominatim_api: NominatimAPI) -> None:
    """Проверяет успешное заполнение таблицы countries."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # with psycopg2.connect(...) as conn:
    mock_conn.__enter__.return_value = mock_conn

    # with conn.cursor() as cur:
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Эмуляция RETURNING country_id
    mock_cursor.fetchone.return_value = [1]

    with patch("src.database.populator.psycopg2.connect", return_value=mock_conn):
        with patch.object(nominatim_api, "get_coordinates", return_value=(55.0, 37.0)):
            with patch.object(
                nominatim_api,
                "get_bounding_box",
                return_value=(41.0, 82.0, 19.0, 169.0),
            ):
                countries: List[str] = ["Russia"]
                result = populate_countries(nominatim_api, countries)

                assert "Russia" in result
                assert result["Russia"]["id"] == 1
                assert result["Russia"]["bbox"] == (41.0, 82.0, 19.0, 169.0)
                assert mock_cursor.execute.call_count == 1
                assert mock_conn.commit.call_count == 1


def test_populate_airplanes_success(opensky_api: OpenSkyAPI) -> None:
    """Проверяет успешное заполнение таблицы airplanes."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # with psycopg2.connect(...) as conn:
    mock_conn.__enter__.return_value = mock_conn

    # with conn.cursor() as cur:
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    countries_data: Dict[str, Dict[str, Any]] = {
        "Russia": {
            "id": 1,
            "bbox": (41.0, 82.0, 19.0, 169.0),
        }
    }

    mock_states: List[Dict[str, Any]] = [
        {
            "icao24": "abc123",
            "callsign": "TEST123",
            "origin_country": "Russia",
            "velocity": 200.0,
            "baro_altitude": 10000.0,
            "geo_altitude": 10000.0,
            "on_ground": False,
            "latitude": 55.0,
            "longitude": 37.0,
            "last_contact": 1600000000,
        }
    ]

    with patch("src.database.populator.psycopg2.connect", return_value=mock_conn):
        with patch.object(opensky_api, "get_aeroplanes", return_value=mock_states):
            added_count = populate_airplanes(
                opensky_api,
                countries_data,
                ["Russia"],
            )

            assert added_count == 1

            # 1 DELETE FROM airplanes + 1 INSERT самолёта
            assert mock_cursor.execute.call_count == 2
            assert mock_conn.commit.call_count == 1


def test_populate_countries_db_error(nominatim_api: NominatimAPI) -> None:
    """Строки 56-58: Ошибка БД при заполнении стран пробрасывает psycopg2.Error."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.Error("DB Error")

    with patch("src.database.populator.psycopg2.connect", return_value=mock_conn):
        with pytest.raises(psycopg2.Error):
            populate_countries(nominatim_api, ["Russia"])


def test_populate_airplanes_country_not_in_data(opensky_api: OpenSkyAPI) -> None:
    """Строки 89-90: Если страны нет в countries_data, она пропускается."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    countries_data: Dict[str, Dict[str, Any]] = {}

    with patch("src.database.populator.psycopg2.connect", return_value=mock_conn):
        added = populate_airplanes(opensky_api, countries_data, ["Russia"])
        assert added == 0


def test_populate_airplanes_no_bbox(opensky_api: OpenSkyAPI) -> None:
    """Строки 96-97: Если у страны нет bbox, она пропускается."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    countries_data: Dict[str, Dict[str, Any]] = {"Russia": {"id": 1, "bbox": None}}

    with patch("src.database.populator.psycopg2.connect", return_value=mock_conn):
        added = populate_airplanes(opensky_api, countries_data, ["Russia"])
        assert added == 0


def test_populate_airplanes_180_meridian(opensky_api: OpenSkyAPI) -> None:
    """
    Строки 103-106: Обработка 180-го меридиана (west > east).
    Должен использоваться фильтр по country, а не по bbox.
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    countries_data: Dict[str, Dict[str, Any]] = {
        "Russia": {"id": 1, "bbox": (41.0, 82.0, 170.0, -170.0)}  # west > east
    }

    with patch("src.database.populator.psycopg2.connect", return_value=mock_conn):
        with patch.object(opensky_api, "get_aeroplanes", return_value=[]) as mock_get_planes:
            populate_airplanes(opensky_api, countries_data, ["Russia"])
            mock_get_planes.assert_called_once_with(country="Russia")


def test_populate_airplanes_invalid_plane_skipped(opensky_api: OpenSkyAPI) -> None:
    """Строка 114: Невалидные самолеты (None из from_api_state) пропускаются."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    countries_data: Dict[str, Dict[str, Any]] = {"Russia": {"id": 1, "bbox": (41.0, 82.0, 19.0, 169.0)}}
    mock_states: List[Dict[str, Any]] = [{"callsign": "   "}]  # Пустой callsign -> None

    with patch("src.database.populator.psycopg2.connect", return_value=mock_conn):
        with patch.object(opensky_api, "get_aeroplanes", return_value=mock_states):
            added = populate_airplanes(opensky_api, countries_data, ["Russia"])
            assert added == 0
            # 1 DELETE, 0 INSERT
            assert mock_cursor.execute.call_count == 1


def test_populate_airplanes_db_error(opensky_api: OpenSkyAPI) -> None:
    """Строки 123-125: Ошибка БД при заполнении самолетов пробрасывает psycopg2.Error."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.Error("DB Error")

    countries_data: Dict[str, Dict[str, Any]] = {"Russia": {"id": 1, "bbox": (41.0, 82.0, 19.0, 169.0)}}

    with patch("src.database.populator.psycopg2.connect", return_value=mock_conn):
        with pytest.raises(psycopg2.Error):
            populate_airplanes(opensky_api, countries_data, ["Russia"])
