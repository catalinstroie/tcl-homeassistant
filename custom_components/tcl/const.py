"""Constants for TCL IoT integration."""

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
DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 30

# Services
SERVICE_POWER_OFF = "power_off"
