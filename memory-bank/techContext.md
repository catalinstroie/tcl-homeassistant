# Tech Context

## Technologies Used
- **Home Assistant**: Open-source home automation platform.
- **HACS (Home Assistant Community Store)**: For custom integration distribution and installation.
- **Python 3.10+**: Required for Home Assistant custom components.
- **requests**: For HTTP API communication with TCL servers.
- **requests_aws4auth**: For AWS IoT authenticated requests.
- **PyJWT**: For decoding JWT tokens from TCL API.
- **Home Assistant Core APIs**: For config flow, entity, and logging integration.

## Development Setup
- The integration is developed as a Python package under the custom_components/ directory.
- Follows Home Assistant's custom component structure: __init__.py, manifest.json, config_flow.py, climate.py, api.py, const.py, etc.
- Uses Home Assistant's logging facilities (`logging.getLogger(__name__)`).
- All configuration is handled via the UI (config flow), not YAML.
- Development and testing are performed in a Home Assistant dev environment with HACS installed.

## Technical Constraints
- Only email and password are collected from the user.
- All API endpoints and payloads must match the official TCL app/script.
- Tokens and sensitive data must be handled securely and not logged.
- The integration must be compatible with Home Assistant's async architecture where possible.
- Must support multiple AC units per account.

## Dependencies
- Home Assistant Core (2023.0+ recommended)
- HACS (latest)
- requests
- requests_aws4auth
- PyJWT

## Tool Usage Patterns
- Use requests for all HTTP API calls.
- Use requests_aws4auth for AWS IoT device control.
- Use Home Assistant's config flow for setup and device selection.
- Use Home Assistant's ClimateEntity for representing AC units.
- Use Home Assistant's logger for all debug and info output.
