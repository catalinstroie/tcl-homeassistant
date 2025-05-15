# Active Context

## Current Work Focus
- Updating Memory Bank documentation to reflect current state.
- Preparing release v1.1.12 of the integration.
- Reviewing all files for consistency and accuracy.

## Recent Changes
- Created and populated all core Memory Bank files:
  - projectbrief.md
  - productContext.md
  - systemPatterns.md
  - techContext.md

## Next Steps
- Scaffold the Home Assistant custom component structure under custom_components/tcl_ac/.
- Implement the config flow to prompt for email, password, and device selection.
- Develop the TCL API client module for authentication, device listing, and control.
- Implement the climate entity for each selected AC unit.
- Integrate extensive logging throughout the codebase.
- Prepare documentation and test the integration in a Home Assistant dev environment.
- Package and release the integration to the GitHub repository.

## Active Decisions and Considerations
- All configuration will be handled via the Home Assistant UI (no YAML).
- Only email and password will be requested from the user.
- Logging will be set to DEBUG level during development.
- Sensitive data (tokens, passwords) will not be logged.
- The integration will be designed for easy extension to support more features in the future.

## Important Patterns and Preferences
- Use Home Assistant's config flow and entity patterns.
- Abstract all TCL API interactions into a dedicated client module.
- Follow Home Assistant's async and logging best practices.

## Learnings and Project Insights
- TCL's API flow requires multiple steps: account authentication, token refresh, AWS credential acquisition, device listing, and device control.
- Device metadata includes nicknames, IDs, and control shortcuts (e.g., powerSwitch).
- The reference script and logs provide a reliable blueprint for API payloads and expected responses.
