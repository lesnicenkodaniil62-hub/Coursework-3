"""Модуль заполнения базы данных данными из внешних API (ETL)."""

import logging
from typing import Any, Dict, List

import psycopg2

from src.api.nominatim import NominatimAPI
from src.api.opensky import OpenSkyAPI
from src.database.config import DB_PARAMS
from src.models.aeroplane import Aeroplane

logger = logging.getLogger(__name__)


def populate_countries(api: NominatimAPI, countries: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Заполняет таблицу countries и возвращает данные о странах.

    :param api: клиент Nominatim
    :param countries: список названий стран
    :return: словарь {country_name: {"id": country_id, "bbox": bbox}}
    """
    countries_data: Dict[str, Dict[str, Any]] = {}
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                for country in countries:
                    logger.info(f"Геокодирование страны: {country}...")
                    coords = api.get_coordinates(country)
                    bbox = api.get_bounding_box(country)

                    lat, lon = coords if coords else (None, None)
                    south, north, west, east = bbox if bbox else (None, None, None, None)

                    cur.execute(
                        """
                        INSERT INTO countries
                            (country_name, latitude, longitude, bbox_south, bbox_north, bbox_west, bbox_east)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (country_name) DO UPDATE SET
                            latitude = EXCLUDED.latitude,
                            longitude = EXCLUDED.longitude,
                            bbox_south = EXCLUDED.bbox_south,
                            bbox_north = EXCLUDED.bbox_north,
                            bbox_west = EXCLUDED.bbox_west,
                            bbox_east = EXCLUDED.bbox_east
                        RETURNING country_id;
                        """,
                        (country, lat, lon, south, north, west, east),
                    )
                    country_id = cur.fetchone()[0]
                    countries_data[country] = {"id": country_id, "bbox": bbox}
            conn.commit()
        logger.info(f"Заполнено стран: {len(countries_data)}")
    except psycopg2.Error as exc:
        logger.error(f"Ошибка при заполнении таблицы countries: {exc}")
        raise
    return countries_data


def populate_airplanes(
    opensky_api: OpenSkyAPI,
    countries_data: Dict[str, Dict[str, Any]],
    target_countries: List[str],
) -> int:
    """
    Заполняет таблицу airplanes самолётами в воздушном пространстве выбранных стран.

    :param opensky_api: клиент OpenSky
    :param countries_data: данные о странах из populate_countries
    :param target_countries: страны, для которых загружаем самолёты
    :return: количество добавленных записей
    """
    total_added: int = 0
    insert_sql: str = """
        INSERT INTO airplanes
            (icao24, callsign, origin_country, airspace_country_id,
             velocity, altitude, on_ground, latitude, longitude, last_contact)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM airplanes;")

                for country in target_countries:
                    if country not in countries_data:
                        logger.warning(f"Страна {country} отсутствует в countries_data")
                        continue

                    country_id = countries_data[country]["id"]
                    bbox = countries_data[country]["bbox"]

                    if not bbox:
                        logger.warning(f"Нет bounding box для {country}, пропускаем")
                        continue

                    south, north, west, east = bbox

                    # Обработка 180-го меридиана (Россия, США и др.)
                    if west > east:
                        logger.warning(
                            f"Bbox для {country} пересекает 180-й меридиан. " f"Используем фильтр по названию страны."
                        )
                        states = opensky_api.get_aeroplanes(country=country)
                    else:
                        states = opensky_api.get_aeroplanes(bbox=bbox)

                    country_added = 0
                    for state in states:
                        plane = Aeroplane.from_api_state(state)
                        if plane is None:
                            continue
                        cur.execute(insert_sql, plane.to_db_tuple(country_id))
                        total_added += 1
                        country_added += 1

                    logger.info(f"Для {country} загружено самолетов: {country_added}")

            conn.commit()
        logger.info(f"ИТОГО добавлено самолётов в БД: {total_added}")
    except psycopg2.Error as exc:
        logger.error(f"Ошибка при заполнении таблицы airplanes: {exc}")
        raise
    return total_added
