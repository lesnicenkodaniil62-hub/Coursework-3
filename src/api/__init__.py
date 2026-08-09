"""Пакет для работы с внешними API (Nominatim, OpenSky)."""

from src.api.base import BaseAPI
from src.api.nominatim import NominatimAPI
from src.api.opensky import OpenSkyAPI

__all__ = ["BaseAPI", "NominatimAPI", "OpenSkyAPI"]
