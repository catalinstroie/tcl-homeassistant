"""Config flow for TCL Home Assistant integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from .const import DOMAIN, CONF_DEVICES, LOGGER_NAME
from .api import TclApi, TclAuthenticationError, TclApiError

_LOGGER = logging.getLogger(LOGGER_NAME)


class TclConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TCL integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize the config flow."""
        self._config_data: Dict[str, Any] = {}
        self._api_client: Optional[TclApi] = None
        self._available_devices: Dict[str, str] = {} # Store as {device_id: nickName}

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            # Ensure unique ID is set based on email first to check existing entries
            # The actual unique_id will be updated if authentication is successful and username_id is available
            await self.async_set_unique_id(email.lower()) # Use lowercase email as a preliminary unique_id
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            self._api_client = TclApi(session, email, password)

            try:
                _LOGGER.info("Attempting to authenticate with TCL API for %s", email)
                auth_success = await self._api_client.authenticate()
                if auth_success:
                    _LOGGER.info("Authentication successful for %s", email)
                    # Update unique_id to the more stable username_id from API if available
                    if self._api_client._username_id:
                        await self.async_set_unique_id(self._api_client._username_id, raise_on_progress=False)
                        self._abort_if_unique_id_configured(updates={CONF_EMAIL: email}) # Pass updates if any
                    
                    self._config_data = user_input.copy() # Store email and password

                    # Fetch devices
                    _LOGGER.info("Fetching devices for %s", email)
                    devices_data = await self._api_client.get_devices()
                    if devices_data:
                        self._available_devices = {
                            device["deviceId"]: device.get("nickName", f"Unnamed Device ({device['deviceId'][-4:]})")
                            for device in devices_data
                        }
                        if not self._available_devices:
                            _LOGGER.warning("No devices found for account %s after successful auth.", email)
                            errors["base"] = "no_devices_found" # Or proceed to create entry with no devices
                            # If proceeding, skip device selection or handle empty selection
                        else:
                            _LOGGER.info("Found %s devices, proceeding to selection step.", len(self._available_devices))
                            return await self.async_step_select_devices()
                    else:
                        _LOGGER.warning("Failed to fetch devices for %s, but authentication was successful.", email)
                        errors["base"] = "no_devices_found" # Treat as no devices
                        # Optionally, allow creating an entry even if no devices are found initially
                        # For now, let's show an error and halt.
                else:
                    # This case should ideally be caught by TclAuthenticationError
                    _LOGGER.warning("Authentication failed for %s with no specific exception.", email)
                    errors["base"] = "invalid_auth"

            except TclAuthenticationError as e:
                _LOGGER.warning("Authentication failed for %s: %s", email, e)
                errors["base"] = "invalid_auth"
            except TclApiError as e:
                _LOGGER.error("API error during authentication/device fetch for %s: %s", email, e)
                errors["base"] = "cannot_connect"
            except Exception as e:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception for %s: %s", email, e)
                errors["base"] = "unknown"
        
        # Prepare data schema for the user form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_select_devices(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle the device selection step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            selected_device_ids = user_input.get(CONF_DEVICES, [])
            if not selected_device_ids:
                _LOGGER.warning("User selected no devices.")
                # Depending on desired behavior, either show an error or allow an entry with no devices.
                # For now, let's assume at least one device should be selected if available.
                # If _available_devices is not empty, and selected_device_ids is, it's a choice.
                # If _available_devices is empty, this step shouldn't ideally be reached or handled differently.
            
            self._config_data[CONF_DEVICES] = selected_device_ids
            
            _LOGGER.info(
                "Creating config entry for %s with %s selected devices.",
                self._config_data[CONF_EMAIL],
                len(selected_device_ids)
            )
            return self.async_create_entry(
                title=self._config_data[CONF_EMAIL], data=self._config_data
            )

        if not self._available_devices:
            _LOGGER.info("No devices available to select, creating entry without devices.")
            # This path might be taken if get_devices returned empty or failed but we decided to proceed
            self._config_data[CONF_DEVICES] = []
            return self.async_create_entry(
                title=self._config_data[CONF_EMAIL], data=self._config_data
            )

        # Prepare data schema for device selection
        # Options for multi-select should be { "value": "label" }
        device_options = {
            dev_id: name for dev_id, name in self._available_devices.items()
        }
        
        data_schema = vol.Schema(
            {
                vol.Optional(CONF_DEVICES, default=[]): cv.multi_select(device_options)
            }
        )

        return self.async_show_form(
            step_id="select_devices",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "num_devices": str(len(self._available_devices))
            },
        )

    # If you want to support re-authentication (e.g., if password changes)
    # async def async_step_reauth(self, user_input: Optional[Dict[str, Any]] = None):
    #     """Handle re-authentication."""
    #     # Similar logic to async_step_user but for an existing entry
    #     # You'd typically get the existing entry's email
    #     # self.context['email'] or self.hass.config_entries.async_get_entry(self.context['entry_id']).data[CONF_EMAIL]
    #     pass

    # If you want to support options flow (e.g., to change selected devices later)
    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry: config_entries.ConfigEntry):
    #     """Get the options flow for this handler."""
    #     return TclOptionsFlowHandler(config_entry)


# Example Options Flow (Optional - for changing settings later, e.g., device selection)
# class TclOptionsFlowHandler(config_entries.OptionsFlow):
#     """Handle an options flow for TCL."""

#     def __init__(self, config_entry: config_entries.ConfigEntry):
#         """Initialize options flow."""
#         self.config_entry = config_entry
#         self._available_devices: Dict[str, str] = {} # {device_id: nickName}
#         self._api_client: Optional[TclApi] = None

#     async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None):
#         """Manage the options for the TCL integration."""
#         errors: Dict[str, str] = {}

#         # Need to re-authenticate or use stored tokens to list devices
#         # This is a simplified example; robust token management would be needed if not storing password
#         email = self.config_entry.data[CONF_EMAIL]
#         password = self.config_entry.data[CONF_PASSWORD] # Assuming password is stored

#         session = async_get_clientsession(self.hass)
#         self._api_client = TclApi(session, email, password)

#         try:
#             if not await self._api_client.authenticate(): # Full re-auth to be safe
#                 errors["base"] = "reauth_failure" # Custom error string
#             else:
#                 devices_data = await self._api_client.get_devices()
#                 if devices_data:
#                     self._available_devices = {
#                         device["deviceId"]: device.get("nickName", f"Unnamed Device ({device['deviceId'][-4:]})")
#                         for device in devices_data
#                     }
#                 else:
#                     self._available_devices = {} # No devices found or error

#         except (TclAuthenticationError, TclApiError) as e:
#             _LOGGER.warning("API error during options flow device fetch: %s", e)
#             errors["base"] = "cannot_connect_options" # Custom error string
#             self._available_devices = {} # Clear devices on error


#         if user_input is not None:
#             # Update the config entry's options
#             return self.async_create_entry(title="", data=user_input)

#         # Get current selected devices from config_entry.options or config_entry.data
#         # For simplicity, let's assume CONF_DEVICES is in config_entry.data
#         # If you store it in options, use self.config_entry.options.get(CONF_DEVICES, [])
#         current_selected_devices = self.config_entry.data.get(CONF_DEVICES, [])

#         device_options = {
#             dev_id: name for dev_id, name in self._available_devices.items()
#         }
#         if not self._available_devices and not errors: # If API call was ok but no devices
#             errors["base"] = "no_devices_options"


#         options_schema = vol.Schema(
#             {
#                 vol.Optional(
#                     CONF_DEVICES,
#                     default=current_selected_devices
#                 ): cv.multi_select(device_options),
#             }
#         )

#         return self.async_show_form(
#             step_id="init", data_schema=options_schema, errors=errors
#         )
