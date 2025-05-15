"""Constants for the TCL Home Assistant integration."""

DOMAIN = "tcl_homeassistant"

# Configuration constants
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_DEVICES = "devices" # Used to store selected device IDs

# API Endpoints and constants from the script
# It's good practice to have these, but they might be better suited inside an api.py
# For now, including some key ones here for reference or direct use if api.py is simple.
CLIENT_ID = "54148614"
ACCOUNT_LOGIN_URL = "https://pa.account.tcl.com/account/login?clientId={}"
USER_AGENT = "Android" # Or consider a more specific one for the integration
CONTENT_TYPE = "application/json; charset=UTF-8"
GET_THINGS_URL = "https://prod-eu.aws.tcljd.com/v3/user/get_things"
REFRESH_TOKENS_URL = "https://prod-eu.aws.tcljd.com/v3/auth/refresh_tokens"
APP_ID = "wx6e1af3fa84fbe523"
AWS_COGNITO_URL = "https://cognito-identity.eu-central-1.amazonaws.com/"
AWS_IOT_REGION = "eu-central-1" # From script
AWS_IOT_ENDPOINT = "a2qjkbbsk6qn2u-ats.iot.eu-central-1.amazonaws.com" # From script
HARDCODED_IDENTITY_ID = "eu-central-1:61e8f839-2d72-c035-a2bf-7ef50a856ddd" # From script
IDENTITY_POOL_ID = "eu-central-1:83840aed-13f2-4c1d-8eaf-9df7f2daaee3" # From script

# Platforms
PLATFORMS = ["climate"]

# Logging
INTEGRATION_VERSION = "0.1.0" # Align with manifest.json
LOGGER_NAME = "tcl_homeassistant"

# Default values
DEFAULT_TH_PLATFORM = "android"
DEFAULT_TH_VERSION = "4.8.1" # From script, consider if this needs updates
DEFAULT_TH_APPBUILD = "830" # From script