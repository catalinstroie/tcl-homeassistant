"""Constants for the TCL Home Assistant integration."""

DOMAIN = "tcl_ac"

# Configuration constants
CONF_HOST = "host"
CONF_PORT = "port"
CONF_DEVICE_ID = "device_id"
CONF_POLL_INTERVAL = "poll_interval"

# Default values
DEFAULT_PORT = 5000
DEFAULT_POLL_INTERVAL = 30  # seconds

# Local API endpoints
CONTROL_ENDPOINT = "/api/control"
STATUS_ENDPOINT = "/api/status"

# Platforms
PLATFORMS = ["climate"]

# Logging
INTEGRATION_VERSION = "0.1.0"  # Align with manifest.json
LOGGER_NAME = "tcl_ac"

# Device capabilities
SUPPORTED_MODES = ["cool", "heat", "fan", "dry", "auto"]
SUPPORTED_FAN_SPEEDS = ["low", "medium", "high", "auto"]
MIN_TEMP = 16  # Celsius
MAX_TEMP = 30  # Celsius
