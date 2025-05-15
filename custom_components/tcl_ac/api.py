"""API for TCL Cloud."""
import asyncio
import hashlib
import json
import logging
import os
import time
import datetime

import aiohttp
from requests_aws4auth import AWS4Auth # Still used for signing, requests.post will be replaced
import jwt # For decoding JWT

from .const import (
    ACCOUNT_LOGIN_URL,
    APP_ID,
    AWS_COGNITO_URL,
    AWS_IOT_ENDPOINT,
    AWS_IOT_REGION,
    CLIENT_ID,
    CONTENT_TYPE,
    DEFAULT_TH_APPBUILD,
    DEFAULT_TH_PLATFORM,
    DEFAULT_TH_VERSION,
    GET_THINGS_URL,
    HARDCODED_IDENTITY_ID,
    REFRESH_TOKENS_URL,
    USER_AGENT,
    LOGGER_NAME,
)

_LOGGER = logging.getLogger(LOGGER_NAME)


class TclAuthenticationError(Exception):
    """Exception to indicate an authentication error."""

class TclApiError(Exception):
    """Exception to indicate a general API error."""


class TclApi:
    """Class to manage the TCL API calls."""

    def __init__(self, session: aiohttp.ClientSession, email: str, password: str):
        """Initialize the API."""
        self._session = session
        self._email = email
        self._password_hash = hashlib.md5(password.encode()).hexdigest()
        self._sso_token = None
        self._saas_token = None
        self._cognito_token = None
        self._cognito_id = None
        self._aws_access_key_id = None
        self._aws_secret_key = None
        self._aws_session_token = None
        self._country_abbr = None
        self._username_id = None # This is the numeric username like "208679190"

    def _calculate_md5_hash_bytes(self, input_string: str) -> str:
        """Calculate MD5 hash."""
        md5_hash = hashlib.md5()
        md5_hash.update(input_string.encode('utf-8'))
        return md5_hash.hexdigest()

    async def _request(self, method: str, url: str, headers: dict, data: dict = None, auth=None, is_json=True):
        """Make an asynchronous HTTP request."""
        _LOGGER.debug("Request URL: %s", url)
        _LOGGER.debug("Request Headers: %s", headers)
        _LOGGER.debug("Request Data: %s", data)

        try:
            if method.upper() == "POST":
                if is_json:
                    async with self._session.post(url, headers=headers, json=data, auth=auth) as response:
                        _LOGGER.debug("Response Status: %s", response.status)
                        _LOGGER.debug("Response Headers: %s", response.headers)
                        if response.status >= 400:
                            text_content = await response.text()
                            _LOGGER.error("API Error %s: %s", response.status, text_content)
                            response.raise_for_status() # Will raise ClientResponseError
                        try:
                            resp_json = await response.json()
                            _LOGGER.debug("Response JSON: %s", json.dumps(resp_json, indent=2))
                            return resp_json
                        except aiohttp.ContentTypeError:
                            text_content = await response.text()
                            _LOGGER.debug("Response Text (not JSON): %s", text_content[:500])
                            return text_content # Or handle as error if JSON was expected
                else: # For x-www-form-urlencoded or other non-json posts if needed
                    async with self._session.post(url, headers=headers, data=data, auth=auth) as response:
                        _LOGGER.debug("Response Status: %s", response.status)
                        _LOGGER.debug("Response Headers: %s", response.headers)
                        if response.status >= 400:
                            text_content = await response.text()
                            _LOGGER.error("API Error %s: %s", response.status, text_content)
                            response.raise_for_status()
                        # Similar JSON/text handling as above
                        try:
                            resp_json = await response.json()
                            _LOGGER.debug("Response JSON: %s", json.dumps(resp_json, indent=2))
                            return resp_json
                        except aiohttp.ContentTypeError:
                            text_content = await response.text()
                            _LOGGER.debug("Response Text (not JSON): %s", text_content[:500])
                            return text_content
            elif method.upper() == "GET":
                async with self._session.get(url, headers=headers, auth=auth) as response:
                    _LOGGER.debug("Response Status: %s", response.status)
                    _LOGGER.debug("Response Headers: %s", response.headers)
                    if response.status >= 400:
                        text_content = await response.text()
                        _LOGGER.error("API Error %s: %s", response.status, text_content)
                        response.raise_for_status()
                    try:
                        resp_json = await response.json()
                        _LOGGER.debug("Response JSON: %s", json.dumps(resp_json, indent=2))
                        return resp_json
                    except aiohttp.ContentTypeError:
                        text_content = await response.text()
                        _LOGGER.debug("Response Text (not JSON): %s", text_content[:500])
                        return text_content
            else:
                _LOGGER.error("Unsupported HTTP method: %s", method)
                raise TclApiError(f"Unsupported HTTP method: {method}")

        except aiohttp.ClientError as e:
            _LOGGER.error("Network or HTTP error during API request to %s: %s", url, e)
            raise TclApiError(f"Request to {url} failed: {e}") from e
        except json.JSONDecodeError as e:
            _LOGGER.error("Failed to decode JSON response from %s: %s", url, e)
            raise TclApiError(f"Invalid JSON response from {url}: {e}") from e


    async def authenticate(self) -> bool:
        """Authenticate with TCL servers and fetch initial tokens."""
        _LOGGER.info("Attempting authentication for user: %s", self._email)
        if not await self._do_account_auth():
            return False
        if not await self._refresh_tokens():
            return False
        if not await self._get_aws_credentials():
            return False
        _LOGGER.info("Authentication successful.")
        return True

    async def _do_account_auth(self) -> bool:
        """Perform initial account login."""
        url = ACCOUNT_LOGIN_URL.format(CLIENT_ID)
        headers = {
            "th_platform": DEFAULT_TH_PLATFORM,
            "th_version": DEFAULT_TH_VERSION,
            "th_appbulid": DEFAULT_TH_APPBUILD, # Note: Typo in original script 'th_appbulid' vs 'th_appbuild'
            "user-agent": USER_AGENT,
            "content-type": CONTENT_TYPE,
        }
        data = {
            "equipment": 2,
            "password": self._password_hash,
            "osType": 1,
            "username": self._email, # Uses email for this initial login
            "clientVersion": DEFAULT_TH_VERSION, # "4.8.1"
            "osVersion": "6.0", # Example, may not be critical
            "deviceModel": "HomeAssistantIntegration", # "AndroidAndroid SDK built for x86"
            "captchaRule": 2,
            "channel": "app",
        }
        try:
            response = await self._request("POST", url, headers, data)
            if response and response.get("status") == 1 and "token" in response:
                self._sso_token = response["token"]
                self._country_abbr = response.get("user", {}).get("countryAbbr")
                self._username_id = response.get("user", {}).get("username") # This is the numeric ID
                _LOGGER.info("Account auth successful. SSO Token obtained. Username ID: %s", self._username_id)
                return True
            _LOGGER.error("Account auth failed. Response: %s", response)
            raise TclAuthenticationError(f"Account authentication failed: {response.get('msg', 'Unknown error')}")
        except TclApiError as e:
            _LOGGER.error("API error during account auth: %s", e)
            raise TclAuthenticationError(f"API error during account auth: {e}") from e

    async def _refresh_tokens(self) -> bool:
        """Refresh SaaS and Cognito tokens."""
        if not self._sso_token or not self._username_id:
            _LOGGER.error("Cannot refresh tokens without SSO token and Username ID.")
            return False

        headers = {
            "user-agent": USER_AGENT,
            "content-type": CONTENT_TYPE,
            "accept-encoding": "gzip, deflate, br", # aiohttp handles this automatically
        }
        data = {
            "userId": self._username_id, # Use the numeric username ID
            "ssoToken": self._sso_token,
            "appId": APP_ID,
        }
        try:
            response = await self._request("POST", REFRESH_TOKENS_URL, headers, data)
            if response and response.get("code") == 0 and "data" in response:
                token_data = response["data"]
                self._saas_token = token_data.get("saasToken")
                self._cognito_token = token_data.get("cognitoToken")
                self._cognito_id = token_data.get("cognitoId") # This might be the same as HARDCODED_IDENTITY_ID

                if not self._saas_token or not self._cognito_token:
                    _LOGGER.error("Failed to retrieve SaaS or Cognito token from refresh response.")
                    raise TclAuthenticationError("Missing SaaS or Cognito token in refresh response.")

                # Validate Cognito token expiry (optional but good practice)
                try:
                    decoded_cognito = jwt.decode(self._cognito_token, options={"verify_signature": False})
                    expiry_time = datetime.datetime.fromtimestamp(decoded_cognito["exp"], tz=datetime.timezone.utc)
                    if datetime.datetime.now(tz=datetime.timezone.utc) > expiry_time:
                        _LOGGER.error("Cognito token obtained is already expired.")
                        raise TclAuthenticationError("Fetched Cognito token is expired.")
                except jwt.PyJWTError as e:
                    _LOGGER.warning("Could not decode Cognito token to check expiry: %s", e)


                _LOGGER.info("Tokens refreshed successfully. SaaS and Cognito tokens obtained.")
                return True
            _LOGGER.error("Token refresh failed. Response: %s", response)
            raise TclAuthenticationError(f"Token refresh failed: {response.get('message', 'Unknown error')}")
        except TclApiError as e:
            _LOGGER.error("API error during token refresh: %s", e)
            raise TclAuthenticationError(f"API error during token refresh: {e}") from e

    async def _get_aws_credentials(self) -> bool:
        """Get AWS temporary credentials using Cognito token."""
        if not self._cognito_token:
            _LOGGER.error("Cannot get AWS credentials without Cognito token.")
            return False

        # The HARDCODED_IDENTITY_ID seems to be crucial.
        # The cognitoId from refresh_tokens might be the same or related.
        # Using the one from the script for now.
        identity_id_to_use = HARDCODED_IDENTITY_ID
        _LOGGER.debug("Using IdentityId for AWS Credentials: %s", identity_id_to_use)

        headers = {
            "X-Amz-Target": "AWSCognitoIdentityService.GetCredentialsForIdentity",
            "Content-Type": "application/x-amz-json-1.1",
            "User-Agent": "aws-sdk-ios/2.35.0 iOS/17.4.1 en_US",
            "X-Amz-Date": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
            "Accept-Language": "en-GB,en;q=0.9",
            "Accept": "application/json",
            "Host": "cognito-identity.eu-central-1.amazonaws.com"
        }
        data = {
            "IdentityId": identity_id_to_use,
            "Logins": {
                "cognito-identity.amazonaws.com": self._cognito_token
            },
            "IdentityPoolId": "eu-central-1:83840aed-13f2-4c1d-8eaf-9df7f2daaee3"
        }
        # Ensure data is properly JSON encoded with correct formatting
        data = json.dumps(data, separators=(',', ':'))  # Compact JSON without spaces
        _LOGGER.debug("AWS Cognito request data: %s", data)
        try:
            response = await self._request("POST", AWS_COGNITO_URL, headers, data, is_json=False)
            
            # Handle case where response comes as string that needs JSON parsing
            if isinstance(response, str):
                try:
                    response = json.loads(response)
                except json.JSONDecodeError as e:
                    _LOGGER.error("Failed to parse AWS response as JSON: %s", e)
                    raise TclAuthenticationError("Failed to parse AWS response") from e

            if not isinstance(response, dict):
                _LOGGER.error("Unexpected response type from AWS Cognito: %s. Full response: %s", 
                             type(response), str(response)[:500])
                raise TclAuthenticationError("AWS credentials response is not in expected format")

            response_data = response
            
            if "Credentials" in response_data:
                creds = response_data["Credentials"]
                self._aws_access_key_id = creds.get("AccessKeyId")
                self._aws_secret_key = creds.get("SecretKey")
                self._aws_session_token = creds.get("SessionToken")

                if not all([self._aws_access_key_id, self._aws_secret_key, self._aws_session_token]):
                    _LOGGER.error("Incomplete AWS credentials received: %s", creds)
                    raise TclAuthenticationError("Incomplete AWS credentials")

                _LOGGER.info("AWS credentials obtained successfully")
                return True
            
            # Handle AWS error responses
            if "__type" in response:
                error_type = response["__type"]
                error_message = response.get("message", "No error message provided")
                _LOGGER.error("AWS Cognito error: %s - %s", error_type, error_message)
                raise TclAuthenticationError(f"AWS Cognito error: {error_type} - {error_message}")
            
            _LOGGER.error("Unexpected AWS response format: %s", response)
            raise TclAuthenticationError("Unexpected AWS response format")
            
        except TclApiError as e:
            _LOGGER.error("API error during AWS credential retrieval: %s", e)
            raise TclAuthenticationError(f"API error during AWS credential retrieval: {e}") from e
        except Exception as e:
            _LOGGER.error("Unexpected error getting AWS credentials: %s", e)
            raise TclAuthenticationError(f"Unexpected error: {e}") from e

    async def get_devices(self) -> list | None:
        """Fetch list of devices."""
        if not self._saas_token or not self._country_abbr:
            _LOGGER.error("Cannot get devices without SaaS token or country code.")
            return None

        timestamp = str(int(time.time() * 1000))
        nonce = os.urandom(16).hex()
        # Ensure self._saas_token is not None before using it in sign calculation
        sign = self._calculate_md5_hash_bytes(timestamp + nonce + self._saas_token)

        headers = {
            "platform": DEFAULT_TH_PLATFORM,
            "appversion": "5.4.1", # From script log
            "thomeversion": DEFAULT_TH_VERSION,
            "accesstoken": self._saas_token,
            "countrycode": self._country_abbr,
            "accept-language": "en",
            "timestamp": timestamp,
            "nonce": nonce,
            "sign": sign,
            "user-agent": USER_AGENT,
            "content-type": CONTENT_TYPE,
        }
        try:
            response = await self._request("POST", GET_THINGS_URL, headers, {})
            if response and response.get("code") == 0 and "data" in response:
                _LOGGER.info("Successfully fetched %s devices.", len(response["data"]))
                return response["data"]
            _LOGGER.error("Failed to get devices. Response: %s", response)
            raise TclApiError(f"Failed to get devices: {response.get('message', 'Unknown error')}")
        except TclApiError as e:
            _LOGGER.error("API error while fetching devices: %s", e)
            raise # Re-raise to be caught by config_flow

    async def control_device(self, device_id: str, command: dict) -> dict | None:
        """Send a control command to a device."""
        if not all([self._aws_access_key_id, self._aws_secret_key, self._aws_session_token]):
            _LOGGER.error("AWS credentials not available for device control.")
            raise TclApiError("AWS credentials not available for device control.")

        url = f"https://{AWS_IOT_ENDPOINT}/topics/%24aws/things/{device_id}/shadow/update?qos=0"
        
        # AWS4Auth needs a synchronous requests.Request object to sign,
        # but we are using aiohttp for the actual request.
        # We can prepare a dummy request for signing purposes.
        # This is a bit of a workaround as requests_aws4auth is synchronous.
        # A fully async AWS SigV4 library would be ideal.
        
        # Create the body first
        payload = {
            "state": {"desired": command},
            "clientToken": f"homeassistant_{int(time.time() * 1000)}"
        }
        payload_bytes = json.dumps(payload).encode('utf-8')

        # Headers for the actual aiohttp request
        # The AWS4Auth object will add the 'Authorization' and 'X-Amz-Date' (if not present),
        # and 'X-Amz-Security-Token' headers.
        # We need to ensure Content-Type is set for the signing process if it affects the signature.
        
        # requests_aws4auth modifies the headers dict in place.
        # For aiohttp, we need to pass the auth object directly.
        # The AWS4Auth class itself can be used as an auth object with requests.
        # For aiohttp, we need to manually sign or find an async equivalent.
        # Let's try to use requests_aws4auth to generate the signature and headers,
        # then apply them to an aiohttp request. This is complex.

        # Alternative: Use a synchronous requests.post within an executor if fully async signing is too hard.
        # For now, let's try to adapt.
        # requests_aws4auth is fundamentally synchronous.
        # The simplest way for now is to run the signed request in an executor.
        
        _LOGGER.debug("Device control URL: %s", url)
        _LOGGER.debug("Device control command: %s", command)

        auth = AWS4Auth(
            self._aws_access_key_id,
            self._aws_secret_key,
            AWS_IOT_REGION,
            'iotdata', # Service name for IoT Data Plane
            session_token=self._aws_session_token
        )

        # Headers that AWS4Auth will expect and potentially use for signing
        # The actual 'Authorization' header will be generated by AWS4Auth
        # The 'host' header is also critical for SigV4 and is derived from the URL.
        # 'X-Amz-Date' is also added by AWS4Auth.
        # 'X-Amz-Security-Token' is added if session_token is provided.
        
        # We need to run the synchronous `requests.post` call in a thread pool executor
        # as it's a blocking I/O operation.
        loop = asyncio.get_event_loop()
        try:
            # Prepare headers that AWS4Auth might need for signing,
            # but the auth object itself will add the necessary Authorization header.
            # The `requests` library handles the Host header automatically.
            # For `aiohttp` with manual signing, you'd add it.
            
            # This specific call is blocking, so it needs to be run in an executor
            import requests # Synchronous requests library
            
            # Headers specifically for the requests library call
            # Content-Type is important for the payload.
            req_headers = {
                "Content-Type": "application/json; charset=utf-8", # Ensure this is what the endpoint expects
                # User-Agent can be added if desired
            }

            response = await loop.run_in_executor(
                None,  # Uses the default ThreadPoolExecutor
                requests.post,
                url,
                headers=req_headers, # AWS4Auth will add/modify headers like Authorization, X-Amz-Date, X-Amz-Security-Token
                data=payload_bytes, # Send as bytes
                auth=auth
            )

            _LOGGER.debug("Device control response status: %s", response.status_code)
            _LOGGER.debug("Device control response headers: %s", response.headers)
            
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
            resp_json = response.json()
            _LOGGER.debug("Device control response JSON: %s", json.dumps(resp_json, indent=2))
            return resp_json

        except requests.exceptions.RequestException as e:
            _LOGGER.error("Error controlling device %s: %s", device_id, e)
            # Attempt to get more details from the response if available
            if hasattr(e, 'response') and e.response is not None:
                _LOGGER.error("Error response content: %s", e.response.text)
                raise TclApiError(f"Failed to control device {device_id}: {e.response.status_code} - {e.response.text}") from e
            raise TclApiError(f"Failed to control device {device_id}: {e}") from e
        except json.JSONDecodeError as e:
            _LOGGER.error("Failed to decode JSON response from device control for %s: %s", device_id, e)
            raise TclApiError(f"Invalid JSON response from device control {device_id}: {e}") from e

    # --- Properties to expose tokens if needed by other parts of the integration ---
    @property
    def sso_token(self):
        return self._sso_token

    @property
    def saas_token(self):
        return self._saas_token

    @property
    def cognito_token(self):
        return self._cognito_token
    
    @property
    def aws_credentials(self):
        if self._aws_access_key_id and self._aws_secret_key and self._aws_session_token:
            return {
                "AccessKeyId": self._aws_access_key_id,
                "SecretKey": self._aws_secret_key,
                "SessionToken": self._aws_session_token,
            }
        return None
