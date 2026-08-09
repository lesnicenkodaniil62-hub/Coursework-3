from unittest.mock import MagicMock, patch

import pytest
import requests

from src.api.mixins import RequestMixin


class TestAPIClient(RequestMixin):
    """Тестовый класс для проверки RequestMixin."""

    def __init__(self) -> None:
        super().__init__(base_url="https://api.test.com")


def test_make_request_success() -> None:
    """Успешный HTTP-запрос возвращает распарсенный JSON."""
    client = TestAPIClient()
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "ok"}
    mock_response.raise_for_status.return_value = None

    with patch.object(client.session, "request", return_value=mock_response) as mock_req:
        result = client._make_request("endpoint")
        assert result == {"status": "ok"}
        mock_req.assert_called_once()


@pytest.mark.parametrize(
    "exception_type",
    [
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
        requests.exceptions.RequestException,
    ],
)
def test_make_request_network_errors(exception_type: type) -> None:
    """Сетевые ошибки (Timeout, HTTPError, RequestException) возвращают None."""
    client = TestAPIClient()
    with patch.object(client.session, "request", side_effect=exception_type):
        result = client._make_request("endpoint")
        assert result is None


def test_make_request_invalid_json() -> None:
    """Ошибка парсинга JSON (ValueError) возвращает None."""
    client = TestAPIClient()
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("No JSON")

    with patch.object(client.session, "request", return_value=mock_response):
        result = client._make_request("endpoint")
        assert result is None
