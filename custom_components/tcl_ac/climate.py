"""Climate platform for TCL AC integration."""
import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVACMode,
    SUPPORT_TARGET_TEMPERATURE, # Will not be used initially
    SUPPORT_FAN_MODE, # Will not be used initially
    HVACAction
)
from homeassistant.const import TEMP_CELSIUS, ATTR_TEMPERATURE
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity # May use later if we add a coordinator

from .const import DOMAIN
from .api import TclApi, TclApiError

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = 0 # Initially, only on/off, so no specific support flags beyond basic ClimateEntity

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the TCL AC climate entities."""
    api = hass.data[DOMAIN][config_entry.entry_id]
    
    try:
        _LOGGER.info("Fetching devices for climate entity setup")
        devices_data = await api.async_get_devices()
    except TclApiError as err:
        _LOGGER.error(f"Error fetching devices for TCL AC: {err}")
        # We might not want to raise ConfigEntryNotReady here if auth was successful
        # but device fetching failed. Or, handle it in __init__ more gracefully.
        return

    entities = []
    if devices_data:
        for device_info in devices_data:
            # Assuming device_info has keys like 'deviceId', 'nickName', 'deviceType'
            # We should filter for AC units if deviceType is available and known
            # For now, let's assume all devices returned are ACs that can be controlled.
            device_id = device_info.get("deviceId")
            nick_name = device_info.get("nickName", f"TCL AC {device_id}")
            if device_id:
                _LOGGER.info(f"Found device: {nick_name} ({device_id})")
                entities.append(TclClimateEntity(api, device_info))
            else:
                _LOGGER.warning(f"Device found with no deviceId: {device_info}")
    else:
        _LOGGER.warning("No devices found for TCL AC integration.")

    async_add_entities(entities, update_before_add=True) # update_before_add calls async_update first

class TclClimateEntity(ClimateEntity):
    """Representation of a TCL AC unit."""

    def __init__(self, api: TclApi, device_info: dict):
        """Initialize the TCL AC climate entity."""
        self._api = api
        self._device_info = device_info
        self._device_id = device_info["deviceId"]
        self._name = device_info.get("nickName", f"TCL AC {self._device_id}")
        self._unique_id = f"tcl_ac_{self._device_id}"
        
        # Initial state - assuming off. Will be updated by async_update.
        self._hvac_mode = HVACMode.OFF
        self._hvac_action = HVACAction.OFF
        self._is_on = False # Internal state for power
        self._current_temperature = None # If available from API
        self._target_temperature = None # If available/controllable

        _LOGGER.debug(f"Initializing TclClimateEntity: {self._name} ({self._device_id})")

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._name,
            "manufacturer": "TCL",
            "model": self._device_info.get("deviceType", "AC Unit"), # Use deviceType if available
            # "sw_version": self._device_info.get("firmwareVersion"), # If available
        }

    @property
    def supported_features(self):
        """Return the list of supported features."""
        # For now, only on/off. No specific flags needed beyond base ClimateEntity.
        # If we add temperature, fan, etc., we add SUPPORT_TARGET_TEMPERATURE, SUPPORT_FAN_MODE.
        return SUPPORT_FLAGS 

    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS # Assuming Celsius, adjust if API provides this or it's configurable

    @property
    def hvac_mode(self):
        """Return current hvac operation state."""
        return self._hvac_mode

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes."""
        # For now, only ON (as COOL) and OFF
        return [HVACMode.OFF, HVACMode.COOL] # Using COOL to represent ON state for an AC

    @property
    def hvac_action(self):
        """Return the current running hvac operation if supported."""
        # This would ideally reflect if it's actually cooling, idle, etc.
        # For a simple on/off, if it's ON and mode is COOL, action is COOLING.
        # If OFF, action is OFF.
        if self._hvac_mode == HVACMode.COOL:
            return HVACAction.COOLING
        return HVACAction.OFF

    # @property
    # def current_temperature(self):
    #     """Return the current temperature."""
    #     return self._current_temperature # To be implemented if API provides it

    # @property
    # def target_temperature(self):
    #     """Return the temperature we are trying to reach."""
    #     return self._target_temperature # To be implemented if API provides it

    async def async_turn_on(self):
        """Turn the climate entity on."""
        _LOGGER.info(f"Turning ON device: {self.name}")
        try:
            # The original script uses {"powerSwitch": 0} for OFF.
            # Assuming {"powerSwitch": 1} is for ON.
            # This needs to be verified with the actual device behavior or API docs.
            await self._api.async_control_device(self._device_id, {"powerSwitch": 1})
            self._is_on = True
            self._hvac_mode = HVACMode.COOL # Represent ON state as COOL for an AC
            self._hvac_action = HVACAction.COOLING
            self.async_write_ha_state()
        except TclApiError as err:
            _LOGGER.error(f"Error turning on {self.name}: {err}")

    async def async_turn_off(self):
        """Turn the climate entity off."""
        _LOGGER.info(f"Turning OFF device: {self.name}")
        try:
            await self._api.async_control_device(self._device_id, {"powerSwitch": 0})
            self._is_on = False
            self._hvac_mode = HVACMode.OFF
            self._hvac_action = HVACAction.OFF
            self.async_write_ha_state()
        except TclApiError as err:
            _LOGGER.error(f"Error turning off {self.name}: {err}")

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        _LOGGER.debug(f"Setting HVAC mode to: {hvac_mode} for {self.name}")
        if hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
        elif hvac_mode == HVACMode.COOL: # Or any other "ON" state
            await self.async_turn_on()
        else:
            _LOGGER.warning(f"Unsupported HVAC mode: {hvac_mode} for {self.name}")
            return
        self.async_write_ha_state()

    # async def async_set_temperature(self, **kwargs):
    #     """Set new target temperature."""
    #     temperature = kwargs.get(ATTR_TEMPERATURE)
    #     if temperature is None:
    #         return
    #     # Call API to set temperature, then update self._target_temperature
    #     _LOGGER.info(f"Setting temperature to {temperature} for {self.name}")
    #     # await self._api.async_control_device(self._device_id, {"targetTemperature": temperature, "powerSwitch": 1})
    #     self.async_write_ha_state()

    async def async_update(self):
        """Update the state of the entity.
        
        This method is called by Home Assistant to refresh the state.
        It should fetch the latest state from the device/API.
        For now, the provided script doesn't have a dedicated status polling endpoint for individual devices after listing.
        The `get_things` endpoint lists devices with some state, but it's not clear if it's real-time enough for updates.
        If the API doesn't provide a good way to get current power state, we might have to rely on assumed state after commands.
        However, a proper climate entity should ideally poll for current state.
        Let's assume for now that `get_devices` (get_things) can be used, but it might be heavy.
        A more targeted device status API would be better.
        
        For this first iteration, we will assume the state based on the last command.
        A more robust solution would involve fetching the actual state.
        The `powerSwitch` property in the device list from `get_things` might indicate current state.
        Example from original script: `devices['data'][0]['properties']['powerSwitch']` (0 or 1)
        We need to see if this is reliable and how often `get_devices` should be called.
        """
        _LOGGER.debug(f"Updating state for {self.name}")
        # This is a placeholder. A real update would fetch state from the API.
        # For example, if the API provides a status:
        # try:
        #     device_status = await self._api.async_get_device_status(self._device_id)
        #     if device_status.get("powerSwitch") == 1:
        #         self._is_on = True
        #         self._hvac_mode = HVACMode.COOL
        #         self._hvac_action = HVACAction.COOLING
        #     else:
        #         self._is_on = False
        #         self._hvac_mode = HVACMode.OFF
        #         self._hvac_action = HVACAction.OFF
        #     # Update other properties like current_temperature if available
        #     # self._current_temperature = device_status.get("currentTemperature")
        # except TclApiError as err:
        #     _LOGGER.error(f"Error updating state for {self.name}: {err}")
        #     # Handle unavailability or errors appropriately
        #     pass # Keep previous state or mark as unavailable

        # For now, since we don't have a dedicated status poll in the initial script beyond device listing,
        # the state is primarily managed by the command methods (turn_on, turn_off).
        # `update_before_add=True` in async_setup_entry will call this once.
        # We can try to parse the initial state from the device_info passed during init if it contains powerSwitch.
        if self._device_info and "properties" in self._device_info and "powerSwitch" in self._device_info["properties"]:
            power_state = self._device_info["properties"]["powerSwitch"]
            _LOGGER.debug(f"Initial powerSwitch state from device_info for {self.name}: {power_state}")
            if power_state == 1:
                self._is_on = True
                self._hvac_mode = HVACMode.COOL
                self._hvac_action = HVACAction.COOLING
            else:
                self._is_on = False
                self._hvac_mode = HVACMode.OFF
                self._hvac_action = HVACAction.OFF
        else:
            _LOGGER.warning(f"No initial powerSwitch state found in device_info for {self.name}, assuming OFF.")
            self._is_on = False
            self._hvac_mode = HVACMode.OFF
            self._hvac_action = HVACAction.OFF

