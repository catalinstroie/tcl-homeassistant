"""API client for interacting with TCL Home servers."""
import asyncio
import base64
import hashlib
import json
import logging
import os
import time
import datetime
import jwt # PyJWT

import aiohttp
from requests_aws4auth import AWS4Auth # This is synchronous, will need to adapt or find async alternative for AWS signing if used directly in async methods.
                                     # For now, the control_device part might need careful handling or a synchronous executor.
                                     # However, the original script uses requests.post with auth=AWS4Auth. aiohttp might need manual header construction.

from .const import (
    ACCOUNT_LOGIN_URL,
    APP_ID,
    AWS_COGNITO_URL,
    AWS_IOT_ENDPOINT,
    AWS_IOT_REGION,
    CLIENT_ID,
    CONTENT_TYPE,
    GET_THINGS_URL,
    HARDCODED_IDENTITY_ID,
    REFRESH_TOKENS_URL,
    TH_APPBUILD,
    TH_PLATFORM,
    TH_VERSION,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)

class TclApiError(Exception):
    """Generic TCL API error."""

class TclApiAuthError(TclApiError):
    """TCL API authentication error."""

def calculate_md5_hash_bytes(input_string):
    """Calculates MD5 hash for a string."""
    md5_hash = hashlib.md5()
    md5_hash.update(input_string.encode("utf-8"))
    return md5_hash.hexdigest()

class TclApi:
    """TCL API Client."""

    def __init__(self, email, password, loop, session: aiohttp.ClientSession = None):
        """Initialize the API client."""
        self._email = email
        self._password_hash = hashlib.md5(password.encode()).hexdigest()
        self._loop = loop
        self._session = session if session else aiohttp.ClientSession()
        self._sso_token = None
        self._saas_token = None
        self._cognito_token = None
        self._aws_credentials = None
        self._country_abbr = None
        self._user_id = None # This is the email/username

    async def _request(self, method, url, headers=None, data=None, auth=None, is_json=True):
        """Make an asynchronous HTTP request with logging."""
        _LOGGER.debug(
            f"Request: {method} {url}\nHeaders: {json.dumps(headers, indent=2)}\nBody: {json.dumps(data, indent=2) if data else '{}'}"
        )
        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                json=data if is_json and data else None,
                data=data if not is_json and data else None,
                auth=auth # aiohttp uses aiohttp.BasicAuth or custom auth helpers
            ) as response:
                response_text = await response.text()
                _LOGGER.debug(
                    f"Response: {response.status}\nHeaders: {json.dumps(dict(response.headers), indent=2)}\nBody: {response_text[:1000]}"
                )
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                try:
                    return await response.json()
                except aiohttp.ContentTypeError: # Handle non-JSON responses if necessary
                    _LOGGER.debug("Response was not JSON, returning raw text.")
                    return response_text
        except aiohttp.ClientResponseError as err:
            _LOGGER.error(f"API request failed [{err.status}]: {err.message} for {url}")
            if err.status == 401 or err.status == 403:
                raise TclApiAuthError(f"Authentication failed: {err.message}") from err
            raise TclApiError(f"API request error: {err.message}") from err
        except aiohttp.ClientError as err:
            _LOGGER.error(f"API request failed: {err} for {url}")
            raise TclApiError(f"API request error: {err}") from err
        except asyncio.TimeoutError as err:
            _LOGGER.error(f"API request timed out: {err} for {url}")
            raise TclApiError(f"API request timeout: {err}") from err

    async def async_do_account_auth(self):
        """Authenticate with TCL account servers."""
        url = ACCOUNT_LOGIN_URL.format(CLIENT_ID)
        headers = {
            "th_platform": TH_PLATFORM,
            "th_version": TH_VERSION,
            "th_appbulid": TH_APPBUILD, # Note: original script has 'th_appbulid', might be a typo for 'th_appbuild'
            "user-agent": USER_AGENT,
            "content-type": CONTENT_TYPE,
        }
        payload = {
            "equipment": 2,
            "password": self._password_hash,
            "osType": 1,
            "username": self._email,
            "clientVersion": "4.8.1", # Should this be TH_VERSION?
            "osVersion": "6.0",
            "deviceModel": "Android SDK built for x86", # Consider making this configurable or more generic
            "captchaRule": 2,
            "channel": "app",
        }
        _LOGGER.info(f"Attempting account authentication for {self._email}")
        response_data = await self._request("POST", url, headers=headers, data=payload)

        if not response_data or response_data.get("errorcode") != "0":
            error_msg = response_data.get("msg", "Unknown authentication error")
            _LOGGER.error(f"Account authentication failed: {error_msg}")
            raise TclApiAuthError(f"Account authentication failed: {error_msg}")

        self._sso_token = response_data.get("token")
        self._country_abbr = response_data.get("user", {}).get("countryAbbr")
        self._user_id = response_data.get("user", {}).get("username") # This should be the email

        if not all([self._sso_token, self._country_abbr, self._user_id]):
            _LOGGER.error("Authentication response missing critical data.")
            raise TclApiAuthError("Authentication response incomplete.")
        
        _LOGGER.info(f"Successfully authenticated {self._email}, obtained SSO token.")
        # After initial auth, refresh tokens to get saas and cognito tokens
        await self.async_refresh_tokens()
        return True

    async def async_refresh_tokens(self):
        """Refresh SSO token to get SaaS and Cognito tokens."""
        if not self._sso_token or not self._user_id:
            _LOGGER.error("Cannot refresh tokens without SSO token and user ID.")
            raise TclApiAuthError("SSO token or User ID not available for token refresh.")

        headers = {
            "user-agent": USER_AGENT,
            "content-type": CONTENT_TYPE,
            "accept-encoding": "gzip, deflate, br",
        }
        payload = {
            "userId": self._user_id,
            "ssoToken": self._sso_token,
            "appId": APP_ID,
        }
        _LOGGER.info(f"Refreshing tokens for {self._user_id}")
        response_data = await self._request("POST", REFRESH_TOKENS_URL, headers=headers, data=payload)

        if not response_data or response_data.get("errorcode") != "0":
            error_msg = response_data.get("msg", "Unknown token refresh error")
            _LOGGER.error(f"Token refresh failed: {error_msg}")
            raise TclApiAuthError(f"Token refresh failed: {error_msg}")

        data_payload = response_data.get("data", {})
        self._cognito_token = data_payload.get("cognitoToken")
        self._saas_token = data_payload.get("saasToken")

        if not self._cognito_token or not self._saas_token:
            _LOGGER.error("Token refresh response missing cognito or saas token.")
            raise TclApiAuthError("Token refresh response incomplete.")

        # Validate Cognito token expiry (optional but good practice)
        try:
            decoded_cognito = jwt.decode(self._cognito_token, options={"verify_signature": False})
            expiry_time = datetime.datetime.fromtimestamp(decoded_cognito["exp"], tz=datetime.timezone.utc)
            if datetime.datetime.now(tz=datetime.timezone.utc) > expiry_time:
                _LOGGER.error("Cognito token obtained from refresh is already expired.")
                raise TclApiAuthError("Refreshed Cognito token is expired.")
        except jwt.ExpiredSignatureError:
            _LOGGER.error("Cognito token is expired (caught by PyJWT).")
            raise TclApiAuthError("Refreshed Cognito token is expired.")
        except jwt.InvalidTokenError as e:
            _LOGGER.error(f"Invalid Cognito token: {e}")
            raise TclApiAuthError(f"Invalid Cognito token: {e}")

        _LOGGER.info("Successfully refreshed tokens, obtained Cognito and SaaS tokens.")
        # After refreshing tokens, get AWS credentials
        await self.async_get_aws_credentials()
        return True

    async def async_get_aws_credentials(self):
        """Get AWS credentials using Cognito token."""
        if not self._cognito_token:
            _LOGGER.error("Cannot get AWS credentials without Cognito token.")
            raise TclApiAuthError("Cognito token not available for AWS credential retrieval.")

        headers = {
            "X-Amz-Target": "AWSCognitoIdentityService.GetCredentialsForIdentity",
            "Content-Type": "application/x-amz-json-1.1",
            "User-Agent": "aws-sdk-iOS/2.26.2 iOS/18.4.1 en_RO", # Consider if this needs to be dynamic
            "X-Amz-Date": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
            "Accept-Language": "en-GB,en;q=0.9",
        }
        payload = {
            "IdentityId": HARDCODED_IDENTITY_ID, # This is hardcoded in the original script
            "Logins": {
                "cognito-identity.amazonaws.com": self._cognito_token
            }
        }
        _LOGGER.info("Fetching AWS credentials.")
        response_data = await self._request("POST", AWS_COGNITO_URL, headers=headers, data=payload)

        # AWS Cognito API might not have 'errorcode' field like TCL's own APIs.
        # It usually returns HTTP status codes for errors.
        # The _request method already handles HTTP errors.
        # We need to check the structure of a successful response.
        if not response_data or "Credentials" not in response_data:
            _LOGGER.error(f"Failed to get AWS credentials. Response: {response_data}")
            raise TclApiError("Failed to retrieve AWS credentials.")

        self._aws_credentials = response_data["Credentials"]
        if not all (k in self._aws_credentials for k in ["AccessKeyId", "SecretKey", "SessionToken"]):
            _LOGGER.error(f"AWS credentials response missing critical keys: {self._aws_credentials}")
            raise TclApiError("Incomplete AWS credentials received.")

        _LOGGER.info("Successfully obtained AWS credentials.")
        return self._aws_credentials

    async def async_get_devices(self):
        """Get list of devices (Things)."""
        if not self._saas_token or not self._country_abbr:
            _LOGGER.error("SaaS token or country code not available for fetching devices.")
            # Attempt to re-authenticate if tokens are missing
            _LOGGER.info("Attempting re-authentication to fetch devices.")
            await self.async_do_account_auth()
            if not self._saas_token or not self._country_abbr:
                 raise TclApiAuthError("SaaS token or country code still not available after re-auth.")

        timestamp = str(int(time.time() * 1000))
        nonce = os.urandom(16).hex()
        # The signature is MD5(timestamp + nonce + saas_token)
        sign_str = timestamp + nonce + self._saas_token
        sign = calculate_md5_hash_bytes(sign_str)

        headers = {
            "platform": TH_PLATFORM,
            "appversion": "5.4.1", # This was different in original script's get_devices vs auth
            "thomeversion": TH_VERSION,
            "accesstoken": self._saas_token,
            "countrycode": self._country_abbr,
            "accept-language": "en", # Consider making this configurable
            "timestamp": timestamp,
            "nonce": nonce,
            "sign": sign,
            "user-agent": USER_AGENT,
            "content-type": CONTENT_TYPE,
            "accept-encoding": "gzip, deflate, br",
        }
        _LOGGER.info("Fetching devices.")
        response_data = await self._request("POST", GET_THINGS_URL, headers=headers, data={}) # Empty JSON body for POST

        if not response_data or response_data.get("errorcode") != "0":
            error_msg = response_data.get("msg", "Unknown error fetching devices")
            _LOGGER.error(f"Failed to get devices: {error_msg}")
            raise TclApiError(f"Failed to get devices: {error_msg}")

        devices = response_data.get("data", [])
        _LOGGER.info(f"Successfully fetched {len(devices)} devices.")
        return devices

    async def async_control_device(self, device_id, command):
        """Control a device via AWS IoT."""
        if not self._aws_credentials:
            _LOGGER.error("AWS credentials not available for device control.")
            # Attempt to re-authenticate if AWS creds are missing
            _LOGGER.info("Attempting re-authentication to control device.")
            await self.async_do_account_auth()
            if not self._aws_credentials:
                raise TclApiAuthError("AWS credentials still not available after re-auth.")

        url = f"https://{AWS_IOT_ENDPOINT}/topics/%24aws/things/{device_id}/shadow/update?qos=0"
        
        # AWS4Auth is synchronous. For aiohttp, we need to manually create the signature
        # or run the signing part in an executor. This is complex.
        # A simpler, though less ideal, approach for now might be to use `requests` in an executor for this specific call.
        # Or, find an async AWS signing library compatible with aiohttp.
        # For now, let's try to construct headers manually, but this is non-trivial for AWS SigV4.
        # The `requests_aws4auth` library does a lot under the hood.

        # Placeholder for actual AWS SigV4 signing with aiohttp
        # This part will require significant work to implement AWS SigV4 signing asynchronously
        # or use a thread pool executor for the synchronous `requests` call.
        # For a first pass, we might have to accept a blocking call here if an async alternative isn't readily available.

        # Let's try to use requests with AWS4Auth in a thread pool executor
        # This is a common pattern when mixing async with blocking libraries.
        
        payload = {
            "state": {"desired": command},
            "clientToken": f"mobile_{int(time.time() * 1000)}"
        }

        # Synchronous part to be run in executor
        def _blocking_control_request():
            sync_session = __import__("requests").Session()
            auth = AWS4Auth(
                self._aws_credentials["AccessKeyId"],
                self._aws_credentials["SecretKey"],
                AWS_IOT_REGION,
                'iotdata',
                session_token=self._aws_credentials["SessionToken"]
            )
            headers = {
                # Content-Type is set by requests based on json=payload
                # X-Amz-Security-Token is added by AWS4Auth if session_token is provided
                # X-Amz-Date is added by AWS4Auth
                "User-Agent": "aws-sdk-iOS/2.26.2 iOS/18.4.1 en_RO", # From original script
            }
            _LOGGER.debug(
                f"SYNC Request (via executor): POST {url}\nHeaders: {json.dumps(headers, indent=2)} (Note: Auth headers added by AWS4Auth)\nBody: {json.dumps(payload, indent=2)}"
            )
            response = sync_session.post(url, headers=headers, json=payload, auth=auth)
            _LOGGER.debug(
                f"SYNC Response (via executor): {response.status_code}\nHeaders: {json.dumps(dict(response.headers), indent=2)}\nBody: {response.text[:1000]}"
            )
            response.raise_for_status()
            return response.json()

        try:
            _LOGGER.info(f"Sending command to device {device_id}: {command}")
            response_data = await self._loop.run_in_executor(None, _blocking_control_request)
            _LOGGER.info(f"Device control command successful for {device_id}.")
            return response_data
        except __import__("requests").exceptions.HTTPError as err:
            _LOGGER.error(f"Device control failed [{err.response.status_code}]: {err.response.text}")
            if err.response.status_code == 401 or err.response.status_code == 403:
                raise TclApiAuthError(f"Device control auth failed: {err.response.text}") from err
            raise TclApiError(f"Device control API error: {err.response.text}") from err
        except Exception as err:
            _LOGGER.error(f"Device control failed: {err}")
            raise TclApiError(f"Device control error: {err}") from err

    async def close_session(self):
        """Close the aiohttp session if it was created by this instance."""
        # Only close if we created it, otherwise let the caller manage it.
        # This logic needs to be refined based on how session is passed.
        # For now, assume if self._session exists, we can close it.
        if self._session and not self._session.closed:
            await self._session.close()
            _LOGGER.debug("TCL API session closed.")

