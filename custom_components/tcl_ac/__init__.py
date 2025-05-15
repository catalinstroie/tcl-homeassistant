"""The TCL Home Assistant Integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import DOMAIN, CONF_DEVICES, PLATFORMS, LOGGER_NAME
from .api import TclApi, TclAuthenticationError, TclApiError

_LOGGER = logging.getLogger(LOGGER_NAME)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TCL integration from a config entry."""
    _LOGGER.info(
        "Setting up TCL integration for entry ID %s (Title: %s)",
        entry.entry_id,
        entry.title,
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(entry.entry_id, {})

    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    # Selected devices are also in entry.data[CONF_DEVICES]

    session = async_get_clientsession(hass)
    api_client = TclApi(session, email, password)

    try:
        _LOGGER.debug("Attempting to authenticate API client for entry %s", entry.entry_id)
        auth_success = await api_client.authenticate()
        if not auth_success:
            # This path might not be hit if authenticate() raises an exception on failure
            _LOGGER.error("Authentication failed for %s. API client did not authenticate.", entry.title)
            raise ConfigEntryAuthFailed("Authentication failed with TCL API.")
        _LOGGER.info("API client authenticated successfully for %s.", entry.title)

    except TclAuthenticationError as err:
        _LOGGER.error("Authentication error setting up TCL integration for %s: %s", entry.title, err)
        raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
    except TclApiError as err:
        _LOGGER.error("API error setting up TCL integration for %s: %s", entry.title, err)
        # This error suggests a temporary issue with the API or network
        raise ConfigEntryNotReady(f"API communication error: {err}") from err
    except Exception as err: # pylint: disable=broad-except
        _LOGGER.exception("Unexpected error setting up TCL integration for %s: %s", entry.title, err)
        raise ConfigEntryNotReady(f"Unexpected error: {err}") from err


    # Store the API client in hass.data for platforms to use
    hass.data[DOMAIN][entry.entry_id]["api_client"] = api_client
    _LOGGER.debug("API client stored in hass.data for entry %s", entry.entry_id)

    # Store the list of selected device IDs for easy access by platforms
    hass.data[DOMAIN][entry.entry_id][CONF_DEVICES] = entry.data.get(CONF_DEVICES, [])
    _LOGGER.debug(
        "Selected devices for entry %s: %s",
        entry.entry_id,
        hass.data[DOMAIN][entry.entry_id][CONF_DEVICES]
    )


    # Forward the setup to the climate platform
    # The climate platform will then look at hass.data[DOMAIN][entry.entry_id]
    # to get the api_client and the list of devices to set up.
    for platform in PLATFORMS:
        _LOGGER.debug("Forwarding setup for platform %s for entry %s", platform, entry.entry_id)
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )
        # For modern HA (2022.11+), you might use:
        # await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        # but doing it individually in a loop is fine and common.

    _LOGGER.info("TCL integration setup complete for entry %s.", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a TCL config entry."""
    _LOGGER.info("Unloading TCL integration for entry ID %s (Title: %s)", entry.entry_id, entry.title)

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        _LOGGER.debug("Successfully unloaded platforms for entry %s.", entry.entry_id)
        # Clean up hass.data
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry.entry_id)
            _LOGGER.debug("Cleaned up hass.data for entry %s.", entry.entry_id)
            if not hass.data[DOMAIN]: # If no more entries for this domain
                hass.data.pop(DOMAIN)
                _LOGGER.debug("Removed domain %s from hass.data as it's empty.", DOMAIN)
        _LOGGER.info("TCL integration unloaded successfully for entry %s.", entry.entry_id)
    else:
        _LOGGER.error("Failed to unload platforms for TCL entry %s.", entry.entry_id)

    return unload_ok

# Optional: If you implement an options flow and want to reload on options change
# async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
#     """Reload TCL config entry."""
#     _LOGGER.info("Reloading TCL integration for entry ID %s", entry.entry_id)
#     await async_unload_entry(hass, entry)
#     await async_setup_entry(hass, entry)
#     _LOGGER.info("TCL integration reloaded for entry ID %s", entry.entry_id)

