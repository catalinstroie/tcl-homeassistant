"""Local API for TCL AC control."""
import asyncio
import logging
from typing import Optional

import aiohttp
from aiohttp.client_exceptions import ClientError

from .const import (
    CONTROL_ENDPOINT,
    DEFAULT_PORT,
    DEFAULT_POLL_INTERVAL,
    LOGGER_NAME,
    STATUS_ENDPOINT,
    SUPPORTED_MODES,
    SUPPORTED_FAN_SPEEDS,
)

_LOGGER = logging.getLogger(LOGGER_NAME)


class TclApiError(Exception):
    """Exception to indicate a general API error."""


class TclApi:
    """Class to manage local TCL AC communication."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int = DEFAULT_PORT,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ):
        """Initialize the API."""
        self._session = session
        self._host = host
        self._port = port
        self._poll_interval = poll_interval
        self._base_url = f"http://{host}:{port}"

    async def _request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        """Make an async HTTP request to the local AC unit."""
        url = f"{self._base_url}{endpoint}"
        _LOGGER.debug("Request to %s: %s", url, data)

        try:
            async with self._session.request(
                method,
                url,
                json=data,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                response.raise_for_status()
                return await response.json()

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout connecting to %s", url)
            raise TclApiError(f"Timeout connecting to AC unit at {url}")

        except ClientError as err:
            _LOGGER.error("Error communicating with AC unit: %s", err)
            raise TclApiError(f"Error communicating with AC unit: {err}")

        except Exception as err:
            _LOGGER.error("Unexpected error: %s", err)
            raise TclApiError(f"Unexpected error: {err}")

    async def get_status(self) -> dict:
        """Get current status of the AC unit."""
        return await self._request("GET", STATUS_ENDPOINT)

    async def set_power(self, power: bool) -> bool:
        """Turn AC unit on/off."""
        result = await self._request(
            "POST",
            CONTROL_ENDPOINT,
            {"power": "on" if power else "off"},
        )
        return result.get("success", False)

    async def set_mode(self, mode: str) -> bool:
        """Set AC operation mode."""
        if mode not in SUPPORTED_MODES:
            raise TclApiError(f"Unsupported mode: {mode}")

        result = await self._request(
            "POST",
            CONTROL_ENDPOINT,
            {"mode": mode},
        )
        return result.get("success", False)

    async def set_temperature(self, temperature: float) -> bool:
        """Set target temperature."""
        result = await self._request(
            "POST",
            CONTROL_ENDPOINT,
            {"temperature": temperature},
        )
        return result.get("success", False)

    async def set_fan_speed(self, fan_speed: str) -> bool:
        """Set fan speed."""
        if fan_speed not in SUPPORTED_FAN_SPEEDS:
            raise TclApiError(f"Unsupported fan speed: {fan_speed}")

        result = await self._request(
            "POST",
            CONTROL_ENDPOINT,
            {"fan_speed": fan_speed},
        )
        return result.get("success", False)

    async def update(self) -> dict:
        """Get full status update."""
        return await self.get_status()
