"""Config flow for TCL AC integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD
from .api import TclApi, TclApiAuthError, TclApiError

_LOGGER = logging.getLogger(__name__)

class TclAcConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TCL AC."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            # Check if already configured
            await self.async_set_unique_id(email.lower()) # Use email as unique_id
            self._abort_if_unique_id_configured()

            api = TclApi(email, password, self.hass.loop, async_get_clientsession(self.hass))

            try:
                _LOGGER.debug("Attempting to authenticate with TCL API for config flow")
                await api.async_do_account_auth() # This will also refresh tokens and get AWS creds internally
                _LOGGER.info("Successfully authenticated with TCL API")
                return self.async_create_entry(title=email, data=user_input)
            except TclApiAuthError as err:
                _LOGGER.error(f"Authentication failed: {err}")
                errors["base"] = "invalid_auth"
            except TclApiError as err:
                _LOGGER.error(f"API error during authentication: {err}")
                errors["base"] = "cannot_connect" # Generic connection error
            except Exception as err: # pylint: disable=broad-except
                _LOGGER.exception(f"Unexpected error during authentication: {err}")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    # If you want to support options flow, you can add it here
    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):
    #     return TclAcOptionsFlowHandler(config_entry)

# class TclAcOptionsFlowHandler(config_entries.OptionsFlow):
#     def __init__(self, config_entry):
#         self.config_entry = config_entry
# 
#     async def async_step_init(self, user_input=None):
#         # Manage the options for the integration.
#         # For now, we don't have options beyond initial setup.
#         return self.async_show_form(step_id="init")

