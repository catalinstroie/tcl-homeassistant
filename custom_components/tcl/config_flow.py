"""Config flow for TCL IoT integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.tcl.api import TCLAPI, APIAuthError, APIConnectionError
from custom_components.tcl.const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect to TCL cloud."""
    try:
        api = TCLAPI(data[CONF_USERNAME], data[CONF_PASSWORD])
        await hass.async_add_executor_job(api.authenticate)
        return {"title": f"TCL IoT ({data[CONF_USERNAME]})"}
    except APIAuthError as err:
        _LOGGER.error("Authentication failed: %s", err)
        if "404" in str(err):
            raise InvalidEndpoint from err
        raise InvalidAuth from err
    except APIConnectionError as err:
        _LOGGER.error("Connection error: %s", err)
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.error("Unexpected error: %s", err)
        raise CannotConnect from err

class TCLConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TCL IoT integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                await self.async_set_unique_id(info["title"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""

class InvalidEndpoint(HomeAssistantError):
    """Error to indicate the API endpoint is invalid."""
