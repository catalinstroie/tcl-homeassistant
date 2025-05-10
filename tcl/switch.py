"""Switch platform for TCL IoT devices."""

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from tcl.const import DOMAIN
from tcl.coordinator import TCLCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TCL switches from config entry."""
    coordinator: TCLCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    switches = [
        TCLSwitch(coordinator, device["id"], device["name"])
        for device in coordinator.devices
        if device.get("type") == "AC"  # Only create switches for AC devices
    ]
    
    async_add_entities(switches)

class TCLSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a TCL device switch."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator: TCLCoordinator, device_id: str, name: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_name = name
        self._attr_unique_id = f"tcl_{device_id}"

    @property
    def is_on(self) -> bool | None:
        """Return true if device is on."""
        device = next(
            (d for d in self.coordinator.devices if d["id"] == self._device_id),
            None
        )
        return device.get("power_state") == "on" if device else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        await self.hass.async_add_executor_job(
            self.coordinator.api.control_device,
            self._device_id,
            "power_on"
        )
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        await self.hass.async_add_executor_job(
            self.coordinator.api.control_device,
            self._device_id,
            "power_off"
        )
        await self.coordinator.async_refresh()
