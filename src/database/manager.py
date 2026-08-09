"""Класс DBManager для работы с данными в БД PostgreSQL (аналитические запросы)."""

import logging
from contextlib import closing
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import DictCursor

from src.database.config import DB_PARAMS

logger = logging.getLogger(__name__)


class DBManager:
    """Класс для подключения к БД PostgreSQL и выполнения аналитических запросов."""

    def __init__(self, db_params: Optional[Dict[str, Any]] = None) -> None:
        """Инициализирует менеджер БД с параметрами подключения."""
        self._db_params: Dict[str, Any] = db_params or DB_PARAMS

    def _connect(self) -> psycopg2.extensions.connection:
        """Создаёт новое подключение к БД."""
        return psycopg2.connect(**self._db_params)

    def _fetch_all(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Выполняет запрос и возвращает все строки как список словарей."""
        try:
            with closing(self._connect()) as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute(query, params)
                    return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as exc:
            logger.error("Ошибка выполнения запроса: %s", exc)
            return []

    def _fetch_one(self, query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """Выполняет запрос и возвращает первую строку как словарь либо None."""
        try:
            with closing(self._connect()) as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute(query, params)
                    row = cur.fetchone()
                    return dict(row) if row else None
        except psycopg2.Error as exc:
            logger.error("Ошибка выполнения запроса: %s", exc)
            return None

    def get_countries_and_aeroplanes_count(self) -> List[Dict[str, Any]]:
        """Получает список всех стран и количество самолётов в их воздушных пространствах."""
        query = """
            SELECT c.country_name, COUNT(a.airplane_id) AS aeroplanes_count
            FROM countries c
            LEFT JOIN airplanes a ON c.country_id = a.airspace_country_id
            GROUP BY c.country_id, c.country_name
            ORDER BY aeroplanes_count DESC;
        """
        return self._fetch_all(query)

    def get_all_aeroplanes(self) -> List[Dict[str, Any]]:
        """Получает список всех воздушных судов."""
        query = "SELECT * FROM airplanes;"
        return self._fetch_all(query)

    def get_avg_speed(self) -> float:
        """Получает среднюю скорость по самолётам."""
        query = "SELECT AVG(velocity) AS avg_speed FROM airplanes WHERE velocity IS NOT NULL;"
        row = self._fetch_one(query)
        if row and row.get("avg_speed") is not None:
            return float(row["avg_speed"])
        return 0.0

    def get_aeroplanes_with_higher_speed(self) -> List[Dict[str, Any]]:
        """Получает список всех самолётов, у которых скорость выше средней."""
        query = """
            SELECT * FROM airplanes
            WHERE velocity > (SELECT AVG(velocity) FROM airplanes WHERE velocity IS NOT NULL);
        """
        return self._fetch_all(query)

    def get_aeroplanes_with_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """Получает список всех самолётов, в позывном которых содержатся переданные символы."""
        query = "SELECT * FROM airplanes WHERE callsign ILIKE %s;"
        return self._fetch_all(query, (f"%{keyword}%",))
