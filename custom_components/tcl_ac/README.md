# TCL AC Home Assistant Integration

This custom component allows you to control your TCL air conditioning units via Home Assistant. It interacts with the TCL Home cloud services to provide control over your devices.

## Features

*   **Authentication:** Securely connect to your TCL Home account using your email and password.
*   **Device Discovery:** Automatically discovers your TCL AC units.
*   **Climate Entity:** Represents each AC unit as a standard Home Assistant climate entity.
*   **Basic Control (Version 0.1.0):**
    *   Turn AC On
    *   Turn AC Off
*   **Debug Logging:** Comprehensive logging of API requests and responses for troubleshooting (enable DEBUG level logging for the component).

## Prerequisites

*   Home Assistant instance.
*   HACS (Home Assistant Community Store) installed (recommended for easy installation).
*   Your TCL Home account email and password.

## Installation

### Option 1: Installation via HACS (Recommended)

1.  Ensure HACS is installed and configured in your Home Assistant.
2.  Open HACS in Home Assistant.
3.  Go to "Integrations".
4.  Click the three dots in the top right corner and select "Custom repositories".
5.  In the "Repository" field, enter the URL of this GitHub repository (e.g., `https://github.com/your_username/tcl_ac_hass_integration`).
6.  In the "Category" field, select "Integration".
7.  Click "Add".
8.  The "TCL AC Control" integration should now appear in the HACS integrations list. Click "Install".
9.  Follow the HACS prompts to complete the installation.
10. Restart Home Assistant.

### Option 2: Manual Installation

1.  Download the latest release ZIP file from the GitHub repository (or clone the repository).
2.  Extract the `tcl_ac` directory from the `custom_components` folder in the ZIP file.
3.  Copy the extracted `tcl_ac` directory into your Home Assistant configuration directory, under the `custom_components` folder. If `custom_components` doesn't exist, create it.
    *   Path should look like: `<config_directory>/custom_components/tcl_ac`
4.  Restart Home Assistant.

## Configuration

1.  After restarting Home Assistant, go to **Settings > Devices & Services**.
2.  Click the **+ ADD INTEGRATION** button in the bottom right corner.
3.  Search for "TCL AC Control" and select it.
4.  A configuration dialog will appear, prompting you for your TCL Home account **Email** and **Password**.
5.  Enter your credentials and click **Submit**.
6.  The integration will attempt to authenticate and discover your devices.
7.  Once successful, your TCL AC units will be added as climate entities.

## Usage

Once configured, your TCL AC units will appear as climate entities in Home Assistant. You can add them to your Lovelace dashboards to control their power state (On/Off).

For this initial version, only On/Off control is supported. Future versions may include temperature control, mode selection, and fan speed control.

## Debugging

If you encounter issues, you can enable debug logging for this integration:

```yaml
logger:
  default: info
  logs:
    custom_components.tcl_ac: debug
```

Add this to your `configuration.yaml` file, then restart Home Assistant. Check the Home Assistant logs for detailed information about API calls and component behavior.

## Known Limitations (Version 0.1.0)

*   Only supports On/Off control.
*   Device state updates rely on the initial information from device discovery and assumed state after commands. Real-time polling for status updates from the API needs further investigation for a more robust solution.
*   The AWS IoT device control part uses a synchronous `requests` call within a thread pool executor due to the complexity of asynchronous AWS SigV4 signing. This is generally acceptable but not purely asynchronous.

## Contributing

Contributions are welcome! If you have ideas for improvements or bug fixes, please open an issue or submit a pull request on the GitHub repository.

## Disclaimer

This is an unofficial integration and is not affiliated with TCL. Use at your own risk.

