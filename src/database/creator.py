"""Модуль создания схемы базы данных PostgreSQL."""

import logging

import psycopg2

from src.database.config import DB_PARAMS

logger = logging.getLogger(__name__)

CREATE_COUNTRIES_TABLE: str = """
CREATE TABLE IF NOT EXISTS countries (
    country_id SERIAL PRIMARY KEY,
    country_name VARCHAR(100) UNIQUE NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    bbox_south FLOAT,
    bbox_north FLOAT,
    bbox_west FLOAT,
    bbox_east FLOAT
);
"""

CREATE_AIRPLANES_TABLE: str = """
CREATE TABLE IF NOT EXISTS airplanes (
    airplane_id SERIAL PRIMARY KEY,
    icao24 VARCHAR(10),
    callsign VARCHAR(20),
    origin_country VARCHAR(100),
    airspace_country_id INT REFERENCES countries(country_id) ON DELETE CASCADE,
    velocity FLOAT,
    altitude FLOAT,
    on_ground BOOLEAN,
    latitude FLOAT,
    longitude FLOAT,
    last_contact BIGINT
);
"""


def create_tables() -> None:
    """Создаёт таблицы countries и airplanes, если они ещё не существуют."""
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_COUNTRIES_TABLE)
                cur.execute(CREATE_AIRPLANES_TABLE)
            conn.commit()
        logger.info("Таблицы БД созданы/проверены.")
    except psycopg2.Error as exc:
        logger.error("Ошибка при создании таблиц: %s", exc)
        raise
