from unittest.mock import MagicMock

from src.database.manager import DBManager


def test_get_countries_and_aeroplanes_count(mock_db_manager: DBManager, mock_db_connection: MagicMock) -> None:
    """Проверяет получение статистики по странам и количеству самолётов."""
    mock_db_connection.fetchall.return_value = [
        {"country_name": "Russia", "aeroplanes_count": 100},
        {"country_name": "USA", "aeroplanes_count": 500},
    ]

    result = mock_db_manager.get_countries_and_aeroplanes_count()
    assert len(result) == 2
    assert result[0]["country_name"] == "Russia"
    assert result[1]["aeroplanes_count"] == 500


def test_get_avg_speed(mock_db_manager: DBManager, mock_db_connection: MagicMock) -> None:
    """Проверяет расчет средней скорости."""
    mock_db_connection.fetchone.return_value = {"avg_speed": 250.5}

    avg_speed = mock_db_manager.get_avg_speed()
    assert avg_speed == 250.5


def test_get_avg_speed_none(mock_db_manager: DBManager, mock_db_connection: MagicMock) -> None:
    """Если средняя скорость None, должен возвращаться 0.0."""
    mock_db_connection.fetchone.return_value = {"avg_speed": None}

    avg_speed = mock_db_manager.get_avg_speed()
    assert avg_speed == 0.0


def test_get_avg_speed_no_rows(mock_db_manager: DBManager, mock_db_connection: MagicMock) -> None:
    """Если в БД нет записей, fetchone возвращает None."""
    mock_db_connection.fetchone.return_value = None

    avg_speed = mock_db_manager.get_avg_speed()
    assert avg_speed == 0.0


def test_get_aeroplanes_with_keyword(mock_db_manager: DBManager, mock_db_connection: MagicMock) -> None:
    """Проверяет поиск самолётов по ключевому слову в позывном."""
    mock_db_connection.fetchall.return_value = [{"callsign": "TEST123", "velocity": 200.0}]

    result = mock_db_manager.get_aeroplanes_with_keyword("TEST")
    assert len(result) == 1
    assert result[0]["callsign"] == "TEST123"


import psycopg2


def test_fetch_all_db_error(mock_db_manager: DBManager, mock_db_connection: MagicMock) -> None:
    """Строки 33-35: Ошибка БД в _fetch_all должна возвращать пустой список."""
    mock_db_connection.execute.side_effect = psycopg2.Error("DB down")
    result = mock_db_manager.get_countries_and_aeroplanes_count()
    assert result == []


def test_fetch_one_db_error(mock_db_manager: DBManager, mock_db_connection: MagicMock) -> None:
    """Строки 45-47: Ошибка БД в _fetch_one должна возвращать None (и 0.0 в get_avg_speed)."""
    mock_db_connection.execute.side_effect = psycopg2.Error("DB down")
    result = mock_db_manager.get_avg_speed()
    assert result == 0.0


def test_get_all_aeroplanes(mock_db_manager: DBManager, mock_db_connection: MagicMock) -> None:
    """Строки 62-63: Проверяет получение всех самолетов."""
    mock_db_connection.fetchall.return_value = [{"icao24": "abc"}]
    result = mock_db_manager.get_all_aeroplanes()
    assert len(result) == 1


def test_get_aeroplanes_with_higher_speed(mock_db_manager: DBManager, mock_db_connection: MagicMock) -> None:
    """Строки 75-79: Проверяет получение самолетов со скоростью выше средней."""
    mock_db_connection.fetchall.return_value = [{"icao24": "fast"}]
    result = mock_db_manager.get_aeroplanes_with_higher_speed()
    assert len(result) == 1
