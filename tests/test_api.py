from typing import Any, Dict, List
from unittest.mock import patch

from src.api.nominatim import NominatimAPI
from src.api.opensky import OpenSkyAPI


def test_nominatim_get_coordinates_success(nominatim_api: NominatimAPI) -> None:
    """Успешное получение координат от Nominatim."""
    mock_data: List[Dict[str, Any]] = [{"lat": "55.75", "lon": "37.61"}]

    with patch.object(nominatim_api, "_make_request", return_value=mock_data):
        coords = nominatim_api.get_coordinates("Russia")
        assert coords == (55.75, 37.61)


def test_nominatim_get_coordinates_empty_response(nominatim_api: NominatimAPI) -> None:
    """Пустой ответ от API должен возвращать None."""
    with patch.object(nominatim_api, "_make_request", return_value=[]):
        coords = nominatim_api.get_coordinates("Atlantis")
        assert coords is None


def test_nominatim_get_bounding_box_success(nominatim_api: NominatimAPI) -> None:
    """Успешное получение bounding box."""
    mock_data: List[Dict[str, Any]] = [{"boundingbox": ["41.1", "82.2", "19.6", "169.0"]}]

    with patch.object(nominatim_api, "_make_request", return_value=mock_data):
        bbox = nominatim_api.get_bounding_box("Russia")
        assert bbox == (41.1, 82.2, 19.6, 169.0)


def test_opensky_get_aeroplanes_success(opensky_api: OpenSkyAPI) -> None:
    """Успешное получение списка самолётов от OpenSky."""
    mock_data: Dict[str, Any] = {
        "states": [
            [
                "abc123",
                "TEST123",
                "TestCountry",
                1600000000,
                1600000000,
                10.5,
                20.5,
                1000.0,
                False,
                250.5,
                90.0,
                0.0,
                [],
                1000.0,
                "1234",
                False,
                "ADS-B",
            ]
        ]
    }

    with patch.object(opensky_api, "_make_request", return_value=mock_data):
        planes = opensky_api.get_aeroplanes(country="TestCountry")
        assert len(planes) == 1
        assert planes[0]["callsign"] == "TEST123"
        assert planes[0]["icao24"] == "abc123"


def test_opensky_get_aeroplanes_empty(opensky_api: OpenSkyAPI) -> None:
    """Пустой список состояний должен возвращать пустой список."""
    mock_data: Dict[str, Any] = {"states": []}

    with patch.object(opensky_api, "_make_request", return_value=mock_data):
        planes = opensky_api.get_aeroplanes()
        assert planes == []


def test_opensky_http_error_returns_empty(opensky_api: OpenSkyAPI) -> None:
    """Ошибка HTTP (возвращает None из _make_request) должна обрабатываться как пустой список."""
    with patch.object(opensky_api, "_make_request", return_value=None):
        planes = opensky_api.get_aeroplanes()
        assert planes == []


def test_nominatim_get_coordinates_parse_error(nominatim_api: NominatimAPI) -> None:
    """Строки 44-45: Ошибка парсинга координат (невалидные строки) возвращает None."""
    mock_data: List[Dict[str, Any]] = [{"lat": "invalid", "lon": "invalid"}]
    with patch.object(nominatim_api, "_make_request", return_value=mock_data):
        coords = nominatim_api.get_coordinates("Russia")
        assert coords is None


def test_nominatim_get_bounding_box_parse_error(nominatim_api: NominatimAPI) -> None:
    """Строки 57-59: Ошибка парсинга bbox (невалидные строки) возвращает None."""
    mock_data: List[Dict[str, Any]] = [{"boundingbox": ["a", "b", "c", "d"]}]
    with patch.object(nominatim_api, "_make_request", return_value=mock_data):
        bbox = nominatim_api.get_bounding_box("Russia")
        assert bbox is None


def test_nominatim_get_aeroplanes_returns_empty(nominatim_api: NominatimAPI) -> None:
    """Строка 63: NominatimAPI.get_aeroplanes всегда возвращает пустой список."""
    assert nominatim_api.get_aeroplanes() == []


def test_opensky_get_aeroplanes_with_bbox(opensky_api: OpenSkyAPI) -> None:
    """
    Строки 60-64: Проверяет формирование параметров запроса при передаче bbox.
    """
    mock_data: Dict[str, Any] = {"states": []}
    with patch.object(opensky_api, "_make_request", return_value=mock_data) as mock_request:
        opensky_api.get_aeroplanes(bbox=(40.0, 50.0, 10.0, 20.0))
        mock_request.assert_called_once_with(
            "states/all", params={"lamin": 40.0, "lamax": 50.0, "lomin": 10.0, "lomax": 20.0}
        )
