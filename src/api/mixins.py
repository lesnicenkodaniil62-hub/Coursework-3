"""
Миксины для переиспользования функциональности.

Реализация HTTP-запросов вынесена сюда, чтобы абстрактный класс BaseAPI
содержал только объявления методов (требование ТЗ + принцип SRP).
"""

import logging
from typing import Any, Dict, List, Optional, Union, cast

import requests

logger = logging.getLogger(__name__)


class RequestMixin:
    """Миксин, отвечающий исключительно за выполнение HTTP-запросов."""

    def __init__(self, base_url: str, timeout: int = 10, user_agent: str = "AeroplanesApp/1.0") -> None:
        """Инициализирует HTTP-сессию с заданным User-Agent."""
        self.base_url: str = base_url.rstrip("/")
        self.timeout: int = timeout
        self.user_agent: str = user_agent
        self.session: requests.Session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
    ) -> Optional[Union[Dict[str, Any], List[Any]]]:
        """
        Выполняет HTTP-запрос и возвращает распарсенный JSON либо None при ошибке.

        :param endpoint: конечная точка API
        :param params: параметры запроса
        :param method: HTTP-метод (GET, POST и т.д.)
        :return: словарь или список из JSON-ответа, либо None при ошибке
        """
        url: str = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response: requests.Response = self.session.request(
                method=method, url=url, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            # Используем cast для явного указания типа возвращаемого значения
            return cast(Optional[Union[Dict[str, Any], List[Any]]], response.json())
        except requests.exceptions.Timeout:
            logger.error("Таймаут запроса к %s", url)
        except requests.exceptions.HTTPError as exc:
            logger.error("HTTP-ошибка при запросе к %s: %s", url, exc)
        except requests.exceptions.RequestException as exc:
            logger.error("Ошибка запроса к %s: %s", url, exc)
        except ValueError as exc:
            logger.error("Ошибка парсинга JSON от %s: %s", url, exc)
        return None
