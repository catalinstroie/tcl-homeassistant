# Product Context

## Why This Project Exists
Many TCL air conditioner owners want to control their devices through Home Assistant, but there is no official or community-supported HACS integration for TCL's cloud platform. The only available method is via TCL's mobile app or unofficial scripts, which are not user-friendly or easily integrated into smart home automations.

## Problems Solved
- Eliminates the need for manual or app-based control of TCL AC units.
- Provides a native Home Assistant experience for TCL device owners.
- Simplifies the authentication and device selection process to just email and password.
- Enables automation and remote control of TCL AC units through Home Assistant.
- Offers detailed logging for troubleshooting and development, addressing the lack of transparency in the official app.

## How It Should Work
- The user installs the integration via HACS.
- On first setup, the integration prompts for email and password.
- The integration authenticates with TCL servers and fetches the list of available AC units.
- The user selects which units to import.
- Each selected unit appears as a climate entity in Home Assistant.
- The user can turn AC units on or off from the Home Assistant UI or via automations.
- All API interactions and integration actions are logged for transparency and debugging.

## User Experience Goals
- Simple, guided setup with minimal required input.
- Reliable device discovery and control.
- Clear feedback and error reporting.
- Extensive logging to assist with troubleshooting and future development.
- Seamless integration with Home Assistant's climate platform and automations.
