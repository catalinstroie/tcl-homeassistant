"""Data update coordinator for TCL IoT integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.tcl.api import TCLAPI
from custom_components.tcl.const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

class TCLCoordinator(DataUpdateCoordinator):
    """Class to manage fetching TCL device data."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="TCL Devices",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.api = TCLAPI(
            config_entry.data["username"],
            config_entry.data["password"]
        )
        self.devices: list[dict[str, Any]] = []

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch data from TCL API."""
        try:
            self.devices = await self.hass.async_add_executor_job(
                self.api.get_devices
            )
            return self.devices
        except Exception as err:
            _LOGGER.error("Error updating TCL devices: %s", err)
            raise
