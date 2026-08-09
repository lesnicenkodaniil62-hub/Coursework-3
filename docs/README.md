# **Анализ воздушного пространства** — Документация

## Описание

«Анализ воздушного пространства» — система мониторинга и анализа данных о воздушных судах в реальном времени. Проект интегрируется с API **OpenSky Network** (телеметрия самолётов) и **Nominatim / OpenStreetMap** (геокодирование стран), сохраняет данные в **PostgreSQL** и выполняет аналитические запросы.

Приложение работает автономно: автоматически обновляет данные каждый час, валидирует входящую информацию и логирует все действия в файл.

### Архитектура
src/
├── api/ # API-клиенты (Nominatim, OpenSky)
├── database/ # Работа с PostgreSQL (схема, ETL, запросы)
├── models/ # Модели данных с валидацией
└── utils/ # Логирование и форматированный вывод
tests/ # Полное тестовое покрытие (pytest)
main.py # Точка входа и планировщик

Проект построен по принципам **SOLID**: абстрактные классы определяют контракты, миксины отвечают за HTTP-запросы, а модели обеспечивают валидацию данных.

---

## Нововведения и функции

### Для пользователей

| Функция | Описание |
|---------|----------|
| **Автоматическое обновление** | Данные о самолётах обновляются каждый час без участия пользователя |
| **Мониторинг 18 стран** | США, Бразилия, Мексика, Германия, Франция, Великобритания, Финляндия, Япония, Китай, Индия, Пакистан, Южная Корея, Казахстан, ОАЭ, Австралия, Египет, Россия |
| **Расширенная аналитика** | Количество самолётов по странам, средняя скорость, поиск по позывному, список «быстрых» самолётов |
| **Форматированный вывод** | Таблицы стран, детальные списки самолётов со статусом (в воздухе / на земле) |
| **Защита от некорректных данных** | Автокоррекция отрицательных скоростей/высот, сброс невалидных координат |

### Технические

| Компонент | Реализация |
|-----------|------------|
| **API-клиенты** | Абстрактный `BaseAPI` + миксин `RequestMixin` (принцип SRP) |
| **Обработка 180-го меридиана** | Для России и США используется фильтр по стране, а не по bounding box |
| **Строгая типизация** | Полные type hints, проверка через `mypy` |
| **Upsert в БД** | Страны обновляются через `ON CONFLICT DO UPDATE`, самолёты перезаписываются каждый час |
| **Логирование** | Только в файл `logs/app.log` (консоль не засоряется) |

Дальнейшие функции будут описаны в последующих обновлениях.

---

## Подробное описание функций проекта

### Модуль API (`src/api/`)

**`BaseAPI`** — абстрактный базовый класс, определяющий контракт для всех API-клиентов. Объявляет три метода без реализации: получение координат страны, получение bounding box и получение списка самолётов.

**`RequestMixin`** — миксин, отвечающий исключительно за HTTP-запросы. Управляет сессией `requests`, обрабатывает таймауты, HTTP-ошибки и ошибки парсинга JSON.

**`NominatimAPI`** — клиент OpenStreetMap для геокодирования стран. Соблюдает политику использования Nominatim (задержка 1.1 сек между запросами, кастомный User-Agent).

**`OpenSkyAPI`** — клиент OpenSky Network для получения данных о самолётах в реальном времени. Поддерживает фильтрацию по стране и по bounding box, парсит сырой ответ (список списков) в структурированные словари.

### Модуль базы данных (`src/database/`)

**`creator`** — создаёт таблицы `countries` и `airplanes` с корректными типами данных и внешними ключами.

**`manager` (класс `DBManager`)** — выполняет аналитические запросы: статистика по странам, средняя скорость, поиск по ключевому слову в позывном, выборка самолётов со скоростью выше средней.

**`populator`** — ETL-процесс:
- `populate_countries()` — геокодирует страны через Nominatim и делает upsert в БД
- `populate_airplanes()` — загружает самолёты через OpenSky с учётом 180-го меридиана

### Модуль моделей (`src/models/`)

**`Aeroplane`** — dataclass, представляющий воздушное судно. Автоматически валидирует данные при создании:
- Пустой `callsign` → исключение `ValueError`
- Отрицательные `velocity` и `altitude` → коррекция до `0.0`
- Координаты вне допустимых диапазонов → сброс в `None`

Метод `from_api_state()` преобразует ответ OpenSky в объект модели, `to_db_tuple()` — кортеж для SQL-вставки.

### Модуль утилит (`src/utils/`)

**`logger`** — настраивает логирование в файл с отключением вывода сторонних библиотек.

**`display`** — форматированный вывод результатов в консоль: таблицы стран, детальные списки самолётов, статистика скоростей.

### Точка входа (`main.py`)

- **`refresh_data()`** — обновление данных (upsert стран + полная перезапись самолётов)
- **`run_initial_setup()`** — первоначальная настройка (логирование, создание таблиц, первый запуск)
- **`run_scheduler()`** — планировщик на `schedule`, обновляет данные каждый час
- **`run()`** — главный сценарий: настройка → первый запуск → планировщик

---

## Инструкция по настройке базы данных

Для работы приложения требуется **PostgreSQL**.

### 1. Установка PostgreSQL

Скачайте с [официального сайта](https://www.postgresql.org/download/) и установите.

### 2. Создание базы данных

Если таблицы не создаались автоматически при запуске, создайте БД вручную:

1. Запустите **SQL Shell (psql)**
2. Введите пароль суперпользователя
3. Выполните:
```sql
CREATE DATABASE planesdb;
```
## 3. Настройка подключения
Откройте файл src/database/config.py и замените пароль на свой:
```
DB_PARAMS = {
    "dbname": "planesdb",
    "user": "postgres",
    "password": "ВАШ_ПАРОЛЬ",  # ← Обязательно замените "QbiX39"
    "host": "localhost",
}
После этого запустите приложение — таблицы создадутся автоматически.

```

Инструкция по настройке линтеров
Файл .flake8 в корне проекта

```

[flake8]
max-line-length = 119
ignore = E402, E251, E203
exclude = .git, .venv, __pycache__, venv

```
Файл pyproject.toml
Если разделы не прописаны, добавьте:

```

[tool.black]
# Максимальная длина строки
line-length = 119
# Файлы, которые не нужно форматировать
exclude = '''
(
  /(
      \.eggs         # Исключить несколько общих каталогов
    | \.git          # в корне проекта
    | \.hg
    | \.mypy_cache
    | \.tox
    | \.venv
    | dist
  )/
  | foo.py           # Также отдельно исключить файл с именем foo.py
                     # в корне проекта
)

'''


[tool.isort]
# максимальная длина строки
line_length = 119


[tool.mypy]
disallow_untyped_defs = true
warn_return_any = true
ignore_missing_imports = true
exclude = "venv"

```

Все зависимости устанавливаются автоматически через Poetry.

И все зависимости что есть на данный момент будут прописаны.

## **Тестирование кодов**

Общие фикстуры (tests/conftest.py)
Фикстуры используются всеми тестами для единообразия данных и мокирования внешних зависимостей:
* sample_api_state — валидный словарь с данными самолёта от OpenSky API
* sample_aeroplane — готовый объект Aeroplane на основе sample_api_state
* nominatim_api — экземпляр NominatimAPI
* opensky_api — экземпляр OpenSkyAPI
* mock_db_manager — DBManager с тестовыми параметрами подключения
* mock_db_connection — мок подключения к БД (патчит DBManager._connect)
1. test_api.py — Тесты API-клиентов (10 тестов)
* test_nominatim_get_coordinates_success — успешное получение координат от Nominatim → (lat, lon)
* test_nominatim_get_coordinates_empty_response — пустой ответ от API возвращает None
* test_nominatim_get_bounding_box_success — успешное получение bounding box страны
* test_opensky_get_aeroplanes_success — успешное получение списка самолётов от OpenSky
* test_opensky_get_aeroplanes_empty — пустой список состояний → возвращает []
* test_opensky_http_error_returns_empty — HTTP-ошибка (_make_request вернул None) → пустой список
* test_nominatim_get_coordinates_parse_error — ошибка парсинга координат (невалидные строки) → None
* test_nominatim_get_bounding_box_parse_error — ошибка парсинга bbox (невалидные строки) → None
* test_nominatim_get_aeroplanes_returns_empty — NominatimAPI.get_aeroplanes() всегда возвращает []
* test_opensky_get_aeroplanes_with_bbox — проверка формирования параметров запроса при передаче bbox
2. test_database.py — Тесты работы с БД (9 тестов)
* test_get_countries_and_aeroplanes_count — проверка получения статистики по странам и количеству самолётов
* test_get_avg_speed — проверка расчёта средней скорости
* test_get_avg_speed_none — средняя скорость None → возвращает 0.0
* test_get_avg_speed_no_rows — нет записей в БД → возвращает 0.0
* test_get_aeroplanes_with_keyword — проверка поиска самолётов по ключевому слову в позывном
* test_fetch_all_db_error — ошибка БД в _fetch_all → возвращает пустой список []
* test_fetch_one_db_error — ошибка БД в _fetch_one → возвращает None (и 0.0 в get_avg_speed)
* test_get_all_aeroplanes — проверка получения списка всех самолётов
* test_get_aeroplanes_with_higher_speed — проверка получения самолётов со скоростью выше средней
3. test_mixins.py — Тесты миксина RequestMixin (4 теста)
* test_make_request_success — успешный HTTP-запрос возвращает распарсенный JSON
* test_make_request_network_errors — сетевые ошибки возвращают None (параметризованный тест: Timeout, HTTPError, RequestException)
* test_make_request_invalid_json — ошибка парсинга JSON (ValueError) → возвращает None
4. test_models.py — Тесты модели Aeroplane (9 тестов)
* test_from_api_state_valid — корректное создание объекта из валидного словаря (проверяет strip() для callsign)
* test_velocity_correction — коррекция отрицательной скорости (параметризованный тест: 100.0, -50.0 → 0.0, None)
* test_altitude_correction — коррекция высоты с учётом приоритета baro_altitude / geo_altitude (параметризованный тест, 4 случая)
* test_latitude_correction — сброс некорректной широты (параметризованный тест: 45.0, -100.0 → None, None)
* test_longitude_correction — сброс некорректной долготы (параметризованный тест: 45.0, 200.0 → None, None)
* test_empty_callsign_returns_none — самолёт с пустым позывным → from_api_state возвращает None
* test_to_db_tuple — проверка формирования кортежа для вставки в БД (10 элементов)
* test_empty_callsign_raises_value_error — прямой вызов конструктора с пустым callsign → ValueError
* test_from_api_state_invalid_data_returns_none — невалидные данные (строка вместо int) → возвращает None
5. test_populator.py — Тесты ETL-процесса (8 тестов)
* test_populate_countries_success — успешное заполнение таблицы countries (проверка upsert и возвращаемых данных)
* test_populate_airplanes_success — успешное заполнение таблицы airplanes (1 DELETE + N INSERT)
* test_populate_countries_db_error — ошибка БД при заполнении стран → пробрасывает psycopg2.Error
* test_populate_airplanes_country_not_in_data — если страны нет в countries_data → она пропускается
* test_populate_airplanes_no_bbox — если у страны нет bbox → она пропускается
* test_populate_airplanes_180_meridian — обработка 180-го меридиана (west > east) → используется фильтр по country, а не по bbox
* test_populate_airplanes_invalid_plane_skipped — невалидные самолёты (None из from_api_state) пропускаются
* test_populate_airplanes_db_error — ошибка БД при заполнении самолётов → пробрасывает psycopg2.Error2.Error
