"""API for TCL IoT devices."""

import logging
import hashlib
from typing import Any
import requests

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
        self._password = hashlib.md5(password.encode()).hexdigest()
        self._session = requests.Session()
        self._access_token = None
        self._refresh_token = None
        self._aws_credentials = None

    def authenticate(self) -> bool:
        """Authenticate with TCL cloud."""
        try:
            headers = {
                "th_platform": "android",
                "th_version": "4.8.1",
                "th_appbulid": "830",
                "user-agent": "Android",
                "content-type": "application/json; charset=UTF-8"
            }
            
            # First authentication step
            response = self._session.post(
                "https://pa.account.tcl.com/account/login?clientId=54148614",
                headers=headers,
                json={
                    "equipment": 2,
                    "password": self._password,
                    "osType": 1,
                    "username": self._username,
                    "clientVersion": "4.8.1",
                    "osVersion": "6.0",
                    "deviceModel": "Android",
                    "captchaRule": 2,
                    "channel": "app"
                }
            )
            response.raise_for_status()
            auth_data = response.json()
            
            # Second step - refresh tokens
            refresh_response = self._session.post(
                "https://prod-eu.aws.tcljd.com/v3/auth/refresh_tokens",
                headers={
                    "user-agent": "Android",
                    "content-type": "application/json; charset=UTF-8"
                },
                json={
                    "userId": auth_data["user"]["username"],
                    "ssoToken": auth_data["token"],
                    "appId": "wx6e1af3fa84fbe523"
                }
            )
            refresh_response.raise_for_status()
            
            refresh_data = refresh_response.json()
            _LOGGER.debug("Full refresh response: %s", refresh_data)
            
            self._access_token = refresh_data["data"]["saasToken"]
            
            # Check for AWS credentials in response
            if "awsCredentials" in refresh_data["data"]:
                self._aws_credentials = refresh_data["data"]["awsCredentials"]
                _LOGGER.debug("Received AWS credentials: %s", {
                    "accessKeyId": self._aws_credentials["accessKeyId"][:4] + "...",
                    "expiration": self._aws_credentials["expiration"]
                })
            else:
                _LOGGER.warning("No AWS credentials found in refresh response")
            
            return True
            
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Authentication failed: %s", err)
            raise APIAuthError from err

    def get_devices(self) -> list[dict[str, Any]]:
        """Get list of registered devices."""
        if not self._access_token:
            self.authenticate()

        try:
            if not self._aws_credentials:
                _LOGGER.error("AWS credentials not available - cannot authenticate with AWS API")
                raise APIConnectionError("Missing AWS credentials")

            from requests_aws4auth import AWS4Auth
            import datetime

            # Prepare AWS SigV4 authentication
            aws_auth = AWS4Auth(
                self._aws_credentials["accessKeyId"],
                self._aws_credentials["secretAccessKey"],
                'eu-central-1',
                'execute-api',
                session_token=self._aws_credentials["sessionToken"]
            )

            # Prepare standard headers
            headers = {
                "platform": "android",
                "appversion": "5.4.1",
                "thomeversion": "4.8.1",
                "accesstoken": self._access_token,
                "countrycode": "RO",
                "accept-language": "en",
                "user-agent": "Android",
                "content-type": "application/json; charset=UTF-8"
            }

            _LOGGER.debug("Making AWS authenticated request to devices endpoint")
            response = self._session.get(
                "https://prod-eu.aws.tcljd.com/v3/user/get_things",
                auth=aws_auth,
                headers=headers
            )
            try:
                response.raise_for_status()
                _LOGGER.debug("Successful response:\nHeaders: %s\nBody: %s",
                    response.headers,
                    response.text
                )
                return response.json().get("data", [])
            except requests.exceptions.HTTPError as err:
                _LOGGER.error("Request failed with status %s\nResponse headers: %s\nResponse body: %s",
                    err.response.status_code,
                    err.response.headers,
                    err.response.text
                )
                raise
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Failed to get devices: %s", err)
            raise APIConnectionError from err

    def control_device(self, device_id: str, command: dict) -> bool:
        """Send control command to device."""
        if not self._access_token:
            self.authenticate()

        try:
            response = self._session.post(
                f"https://a2qjkbbsk6qn2u-ats.iot.eu-central-1.amazonaws.com/topics/%24aws/things/{device_id}/shadow/update?qos=0",
                headers={
                    "Content-Type": "application/x-amz-json-1.0",
                    "X-Amz-Security-Token": self._aws_credentials["SessionToken"]
                },
                json={
                    "state": {
                        "desired": command
                    }
                }
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Failed to control device: %s", err)
            raise APIConnectionError from err
