"""Модуль форматированного вывода результатов запросов в консоль."""

from typing import Any, Dict, List


def print_countries_count(rows: List[Dict[str, Any]]) -> None:
    """Выводит список стран и количество самолётов в их воздушном пространстве."""
    print("\n" + "=" * 70)
    print("СТРАНЫ И КОЛИЧЕСТВО САМОЛЁТОВ В ИХ ВОЗДУШНОМ ПРОСТРАНСТВЕ")
    print("=" * 70)
    if not rows:
        print("Нет данных.")
        return
    print(f"{'Страна':<25} | {'Самолётов':>10}")
    print("-" * 70)
    for row in rows:
        print(f"{row['country_name']:<25} | {row['aeroplanes_count']:>10}")
    print("=" * 70)


def print_aeroplanes(rows: List[Dict[str, Any]], title: str = "Воздушные суда") -> None:
    """Выводит список воздушных судов в форматированном виде."""
    print("\n" + "=" * 100)
    print(title.upper())
    print("=" * 100)
    if not rows:
        print("Нет данных для отображения.")
        return

    header = (
        f"{'№':<4} | {'Позывной':<10} | {'ICAO24':<8} | {'Страна':<20} | "
        f"{'Скорость':>10} | {'Высота':>10} | {'Статус':<10}"
    )
    print(header)
    print("-" * 100)

    for idx, plane in enumerate(rows, start=1):
        velocity = f"{plane['velocity']:.2f}" if plane["velocity"] is not None else "N/A"
        altitude = f"{plane['altitude']:.2f}" if plane["altitude"] is not None else "N/A"
        status = "На земле" if plane["on_ground"] else "В воздухе"
        print(
            f"{idx:<4} | {plane['callsign']:<10} | {plane['icao24']:<8} | "
            f"{plane['origin_country']:<20} | {velocity:>10} | {altitude:>10} | {status:<10}"
        )

    print("-" * 100)
    print(f"Всего записей: {len(rows)}")
    print("=" * 100)


def print_avg_speed(avg_speed: float) -> None:
    """Выводит среднюю скорость воздушных судов."""
    print("\n" + "=" * 70)
    print("СРЕДНЯЯ СКОРОСТЬ ПО САМОЛЁТАМ")
    print("=" * 70)
    print(f"Средняя скорость: {avg_speed:.2f} м/с")
    print("=" * 70)
