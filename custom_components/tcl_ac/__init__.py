"""The TCL AC integration."""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, PLATFORMS
from .api import TclApi

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TCL AC from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    email = entry.data["email"]
    password = entry.data["password"]

    api = TclApi(email, password, hass.loop)

    try:
        await api.async_do_account_auth()
        # Further setup like fetching devices would go here
        # For now, just store the api instance
    except Exception as err:
        _LOGGER.error(f"Error authenticating with TCL API: {err}")
        raise ConfigEntryNotReady(f"Failed to authenticate with TCL API: {err}") from err

    hass.data[DOMAIN][entry.entry_id] = api

    # Forward the setup to the climate platform.
    # hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    # For now, let's just set up the climate platform directly
    # This will be refined later when PLATFORMS is properly defined
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

