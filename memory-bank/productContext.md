# TCL AC Control - Product Context

## Purpose
Enable Home Assistant users to control their TCL air conditioners through Home Assistant's climate platform.

## User Experience Goals
- Simple setup through Home Assistant's config flow
- Reliable on/off control of AC units
- Clear status feedback in Home Assistant UI
- Minimal configuration required (just email/password)

## Key Features
- Cloud-based control of TCL AC units
- Automatic device discovery
- Basic climate entity implementation
- Error handling for common issues

## Integration Points
- Home Assistant climate platform
- TCL cloud API (EU region)
- AWS IoT for device control
- AWS Cognito for authentication

## Limitations
- Currently only supports on/off control
- No temperature or fan speed control yet
- Cloud-dependent (no local control)
