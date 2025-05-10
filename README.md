# TCL IoT Home Assistant Integration

Control your TCL IoT devices through Home Assistant.

![Integration Screenshot](https://github.com/catalinstroie/tcl-homeassistant/raw/main/images/screenshot.png)

## Features
- Control TCL AC units and other IoT devices
- Power on/off functionality
- Cloud-based integration

## Installation

### Method 1: Manual Installation
1. Copy the `custom_components/tcl` directory to your Home Assistant `config/custom_components` directory
2. Restart Home Assistant
3. Add integration via Configuration -> Integrations

### Method 2: GitHub Installation
Add to your `configuration.yaml`:
```yaml
custom_components:
  tcl:
    source: https://github.com/catalinstroie/tcl-homeassistant
```
Then restart Home Assistant.

## Configuration
1. Go to Configuration -> Integrations
2. Click "+ Add Integration"
3. Search for "TCL IoT"
4. Enter your TCL account credentials

## Support
For issues or feature requests, please [open an issue](https://github.com/catalinstroie/tcl-homeassistant/issues)

## License
MIT
