"""Constants for TCL IoT integration."""
from datetime import timedelta

DOMAIN = "tcl"

# Configuration
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# API Configuration
API_BASE_URL = "https://api.tcl.com"
AUTH_ENDPOINT = "/auth/login"
DEVICES_ENDPOINT = "/api/devices"
CONTROL_ENDPOINT = "/api/control"

# Defaults
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)
MIN_SCAN_INTERVAL = timedelta(seconds=30)

# Services
SERVICE_POWER_OFF = "power_off"
