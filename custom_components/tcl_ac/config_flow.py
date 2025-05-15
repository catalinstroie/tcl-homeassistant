"""Config flow for TCL Home Assistant local integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import (
    DOMAIN,
    DEFAULT_PORT,
    LOGGER_NAME,
    CONF_DEVICE_ID,
    CONF_POLL_INTERVAL
)
from .api import TclApi, TclApiError

_LOGGER = logging.getLogger(LOGGER_NAME)


class TclConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for local TCL integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize the config flow."""
        self._config_data: Dict[str, Any] = {}
        self._api_client: Optional[TclApi] = None

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)

            # Use host as unique ID for local setup
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            self._api_client = TclApi(session, host, port)

            try:
                # Test connection by getting status
                status = await self._api_client.get_status()
                if status:
                    self._config_data = user_input.copy()
                    self._config_data[CONF_DEVICE_ID] = status.get("device_id", host)
                    return self.async_create_entry(
                        title=f"TCL AC ({host})",
                        data=self._config_data
                    )
                else:
                    errors["base"] = "cannot_connect"

            except TclApiError as e:
                _LOGGER.error("Connection error to %s:%s: %s", host, port, e)
                errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.exception("Unexpected exception: %s", e)
                errors["base"] = "unknown"

        data_schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Optional(CONF_POLL_INTERVAL, default=30): int,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow."""
        return TclOptionsFlowHandler(config_entry)


class TclOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for TCL."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema({
            vol.Optional(
                CONF_POLL_INTERVAL,
                default=self.config_entry.options.get(CONF_POLL_INTERVAL, 30)
            ): int,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema
        )
