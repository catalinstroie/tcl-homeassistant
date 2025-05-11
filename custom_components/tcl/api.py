"""API for TCL IoT devices."""

import logging
import hashlib
import datetime
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
        _LOGGER.debug("Initialized API client for username: %s", username)
        _LOGGER.debug("Password MD5: %s", self._password)
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
                "content-type": "application/json; charset=UTF-8",
                "accept-encoding": "gzip, deflate, br",
                "connection": "keep-alive"
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
                    "deviceModel": "AndroidAndroid SDK built for x86",
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
                    "content-type": "application/json; charset=UTF-8",
                    "accept-encoding": "gzip, deflate, br"
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
            
            # Get AWS credentials from Cognito
            cognito_response = self._session.post(
                "https://cognito-identity.eu-central-1.amazonaws.com/",
                headers={
                    "X-Amz-Target": "AWSCognitoIdentityService.GetCredentialsForIdentity",
                    "Content-Type": "application/x-amz-json-1.1",
                    "User-Agent": "aws-sdk-iOS/2.26.2 iOS/18.4.1 en_RO",
                    "X-Amz-Date": datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                },
                json={
                    "IdentityId": refresh_data["data"]["cognitoId"],
                    "Logins": {
                        "cognito-identity.amazonaws.com": refresh_data["data"]["cognitoToken"]
                    }
                }
            )
            cognito_response.raise_for_status()
            cognito_data = cognito_response.json()
            
            self._aws_credentials = cognito_data["Credentials"]
            _LOGGER.debug("Received AWS credentials: %s", {
                "accessKeyId": self._aws_credentials["AccessKeyId"][:4] + "...",
                "expiration": self._aws_credentials["Expiration"]
            })
            
            return True
            
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Authentication failed: %s", err)
            raise APIAuthError from err

    def _parse_expiration(self, expiration) -> datetime.datetime:
        """Parse AWS credential expiration timestamp."""
        try:
            if isinstance(expiration, str):
                return datetime.datetime.strptime(expiration, "%Y-%m-%dT%H:%M:%SZ")
            elif isinstance(expiration, (int, float)):
                return datetime.datetime.fromtimestamp(expiration)
            else:
                _LOGGER.warning("Unknown expiration format: %s (type: %s)", 
                               expiration, type(expiration))
                return datetime.datetime.min
        except Exception as err:
            _LOGGER.error("Failed to parse expiration: %s", err)
            return datetime.datetime.min

    def _validate_credentials(self) -> None:
        """Validate and refresh credentials if needed."""
        if not self._access_token:
            self.authenticate()
            return
            
        if self._aws_credentials:
            expiration = self._parse_expiration(self._aws_credentials["Expiration"])
            # Refresh 5 minutes before expiration
            buffer = datetime.timedelta(minutes=5)
            if expiration - buffer < datetime.datetime.utcnow():
                _LOGGER.debug("Refreshing credentials (expires at %s, buffer: %s)...",
                            expiration,
                            buffer)
                try:
                    self.authenticate()
                except Exception as err:
                    _LOGGER.error("Failed to refresh credentials: %s", err)
                    raise

    def get_devices(self) -> list[dict[str, Any]]:
        """Get list of registered devices."""
        try:
            self._validate_credentials()
            
            # Debug log current credentials state
            if self._aws_credentials:
                _LOGGER.debug("Current AWS credentials: %s", {
                    "accessKeyId": self._aws_credentials["AccessKeyId"][:4] + "...",
                    "expiration": self._aws_credentials["Expiration"],
                    "sessionToken": bool(self._aws_credentials["SessionToken"])
                })
            import time
            import random
            import hashlib
            
            timestamp = str(int(time.time() * 1000))
            nonce = hashlib.md5(str(random.random()).encode()).hexdigest()
            sign_str = f"{timestamp}{nonce}{self._access_token}"
            sign = hashlib.md5(sign_str.encode()).hexdigest()
            
            expiration = self._parse_expiration(self._aws_credentials["Expiration"])
            _LOGGER.debug("Current AWS credentials state: %s", {
                "accessKeyId": self._aws_credentials["AccessKeyId"][:4] + "...",
                "expirationRaw": self._aws_credentials["Expiration"],
                "expirationType": type(self._aws_credentials["Expiration"]).__name__,
                "expirationParsed": expiration.isoformat(),
                "valid": expiration > datetime.datetime.utcnow()
            })

            headers = {
                "platform": "android",
                "appversion": "5.4.1",
                "thomeversion": "4.8.1",
                "accesstoken": self._access_token,
                "countrycode": "RO",
                "accept-language": "en",
                "timestamp": timestamp,
                "nonce": nonce,
                "sign": sign,
                "user-agent": "Android",
                "content-type": "application/json; charset=UTF-8",
                "accept-encoding": "gzip, deflate, br",
                "x-amz-security-token": self._aws_credentials["SessionToken"],
                "x-amz-date": datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"),
                "x-amz-content-sha256": hashlib.sha256(b"").hexdigest()
            }

            # Log full request details including masked credentials
            _LOGGER.debug("Full request details:\nURL: %s\nMethod: GET\nHeaders: %s\nAWS Credentials: %s",
                "https://prod-eu.aws.tcljd.com/v3/user/get_things",
                {
                    k: (v[:4] + '...' if 'token' in k.lower() or 'secret' in k.lower() else v)
                    for k, v in headers.items()
                },
                {
                    "AccessKeyId": self._aws_credentials["AccessKeyId"][:4] + "...",
                    "SessionToken": self._aws_credentials["SessionToken"][:4] + "...",
                    "Expiration": self._aws_credentials["Expiration"],
                    "Valid": self._parse_expiration(self._aws_credentials["Expiration"]) > datetime.datetime.utcnow()
                }
            )
            
            try:
                response = self._session.get(
                    "https://prod-eu.aws.tcljd.com/v3/user/get_things",
                    headers=headers
                )
                _LOGGER.debug("Raw response headers: %s", dict(response.headers))
                _LOGGER.debug("Response status: %s, headers: %s",
                    response.status_code,
                    dict(response.headers)
                )
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
                # If 403, try with original headers but different timestamp format
                if err.response.status_code == 403:
                    _LOGGER.debug("Attempting fallback authentication method")
                    headers["timestamp"] = str(int(time.time()))
                    response = self._session.get(
                        "https://prod-eu.aws.tcljd.com/v3/user/get_things",
                        headers=headers
                    )
                    response.raise_for_status()
                    return response.json().get("data", [])
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
                    "X-Amz-Security-Token": self._aws_credentials["SessionToken"],
                    "User-Agent": "aws-sdk-iOS/2.26.2 iOS/18.4.1 en_RO",
                    "X-Amz-Date": datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                },
                json={
                    "state": {
                        "desired": command
                    },
                    "clientToken": f"mobile_{int(time.time() * 1000)}"
                }
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Failed to control device: %s", err)
            raise APIConnectionError from err
