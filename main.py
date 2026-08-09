"""
Точка входа в приложение.

Оркестрирует процесс:
1. Создание таблиц в PostgreSQL.
2. Заполнение таблицы стран через Nominatim.
3. Заполнение таблицы самолётов через OpenSky.
4. Автоматическое обновление данных каждый час.
"""

import sys
import time
from datetime import datetime
from typing import Dict, List

import schedule

from src.api.nominatim import NominatimAPI
from src.api.opensky import OpenSkyAPI
from src.database.creator import create_tables
from src.database.manager import DBManager
from src.database.populator import populate_airplanes, populate_countries
from src.utils.logger import setup_logging

MONITORED_COUNTRIES: List[str] = [
    # Северная и Южная Америка
    "United States",
    "Brazil",
    "Mexico",
    # Европа
    "Germany",
    "France",
    "United Kingdom",
    "Finland",
    # Азия
    "Japan",
    "China",
    "India",
    "Pakistan",
    "South Korea",
    "Kazakhstan",
    "United Arab Emirates",
    # Океания
    "Australia",
    # Африка
    "Egypt",
    # Евразия (с обработкой 180-го меридиана)
    "Russia",
]


def refresh_data() -> None:
    """
    Обновляет данные в базе данных.
    Вызывается планировщиком каждый час.

    Процесс обновления:
    1. Обновляет координаты стран (upsert)
    2. Загружает свежие данные о самолетах (delete + insert)
    3. Выводит статистику обновления
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "=" * 70)
    print(" НАЧИНАЕМ ОБНОВЛЕНИЕ ДАННЫХ: " + current_time)
    print("=" * 70)

    try:
        nominatim = NominatimAPI()
        opensky = OpenSkyAPI()
        manager = DBManager()

        # Шаг 1: Обновляем страны (upsert - обновление существующих + вставка новых)
        print(" Обновляем данные о " + str(len(MONITORED_COUNTRIES)) + " странах...")
        countries_data: Dict[str, Dict] = populate_countries(nominatim, MONITORED_COUNTRIES)

        # Шаг 2: Обновляем самолеты (delete + insert - полная перезапись)
        print("✈ Загружаем свежие данные о самолетах...")
        total_added = populate_airplanes(opensky, countries_data, MONITORED_COUNTRIES)

        # Шаг 3: Выводим статистику
        countries_count = manager.get_countries_and_aeroplanes_count()
        avg_speed = manager.get_avg_speed()
        higher_speed_planes = manager.get_aeroplanes_with_higher_speed()

        print("\n  ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("    Стран в БД: " + str(len(countries_count)))
        print("    Самолетов загружено: " + str(total_added))
        print("    Средняя скорость: " + f"{avg_speed:.2f}" + " м/с")
        print("    Самолетов выше средней: " + str(len(higher_speed_planes)))

    except Exception as e:
        print("\n ОШИБКА ПРИ ОБНОВЛЕНИИ ДАННЫХ: " + str(e))
        print("   Следующая попытка будет через 1 час.")

    print("=" * 70 + "\n")


def run_initial_setup() -> None:
    """
    Выполняет первоначальную настройку и первый запуск обновления.

    Процесс:
    1. Настраивает логирование в файл
    2. Выводит информацию о системе
    3. Создает таблицы в БД
    4. Выполняет первое обновление данных
    """
    setup_logging()

    print("\n" + "=" * 70)
    print(" СИСТЕМА МОНИТОРИНГА ВОЗДУШНОГО ПРОСТРАНСТВА")
    print("=" * 70)
    print(" Время запуска: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(" Отслеживается стран: " + str(len(MONITORED_COUNTRIES)))
    print(" Интервал обновления: 1 час")
    print(" Логи сохраняются в: logs/app.log")
    print("=" * 70)

    # Создаем таблицы в БД
    create_tables()

    # Первый запуск обновления данных
    refresh_data()


def run_scheduler() -> None:
    """
    Запускает планировщик для автоматического обновления каждый час.

    Планировщик проверяет задачи каждую минуту и запускает обновление
    данных ровно через 1 час после предыдущего запуска.
    """
    # Планируем задачу на каждый час
    schedule.every(1).hours.do(refresh_data)

    print(" Планировщик запущен. Следующее обновление через 1 час.")
    print(" Нажмите Ctrl+C для остановки.\n")

    # Бесконечный цикл для проверки задач
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Проверяем задачи каждую минуту
    except KeyboardInterrupt:
        print("\n\n Планировщик остановлен пользователем.")


def run() -> int:
    """
    Главная функция приложения.

    Запускает полный сценарий работы:
    1. Первоначальная настройка и первый запуск
    2. Запуск планировщика для автоматического обновления

    :return: код выхода (0 - успех, 1 - ошибка)
    """
    try:
        # Первоначальная настройка и первый запуск
        run_initial_setup()

        # Запуск планировщика
        run_scheduler()

        return 0
    except Exception as e:
        print("\n КРИТИЧЕСКАЯ ОШИБКА: " + str(e))
        return 1


if __name__ == "__main__":
    sys.exit(run())
