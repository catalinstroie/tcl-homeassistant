"""API for TCL IoT devices."""

import logging
from typing import Any

import requests
from requests_aws4auth import AWS4Auth

_LOGGER = logging.getLogger(__name__)

class APIAuthError(Exception):
    """Authentication error."""

class APIConnectionError(Exception):
    """Connection error."""

class TCLAPI:
    """Class to interface with TCL IoT API."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize API client."""
        self._username = username
        self._password = password
        self._session = requests.Session()
        self._auth_token = None

    def authenticate(self) -> bool:
        """Authenticate with TCL cloud."""
        try:
            response = self._session.post(
                "https://api.tcl.com/auth/login",
                json={"username": self._username, "password": self._password}
            )
            response.raise_for_status()
            self._auth_token = response.json().get("token")
            return True
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Authentication failed: %s", err)
            raise APIAuthError from err

    def get_devices(self) -> list[dict[str, Any]]:
        """Get list of registered devices."""
        if not self._auth_token:
            self.authenticate()

        try:
            response = self._session.get(
                "https://api.tcl.com/api/devices",
                headers={"Authorization": f"Bearer {self._auth_token}"}
            )
            response.raise_for_status()
            return response.json().get("devices", [])
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Failed to get devices: %s", err)
            raise APIConnectionError from err

    def control_device(self, device_id: str, command: str) -> bool:
        """Send control command to device."""
        if not self._auth_token:
            self.authenticate()

        try:
            response = self._session.post(
                f"https://api.tcl.com/api/control/{device_id}",
                json={"command": command},
                headers={"Authorization": f"Bearer {self._auth_token}"}
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Failed to control device: %s", err)
            raise APIConnectionError from err
