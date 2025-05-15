# System Patterns

## Architecture Overview
- The integration is structured as a Home Assistant custom component, installable via HACS.
- It uses a configuration flow (config_flow.py) to guide the user through authentication and device selection.
- The integration communicates with TCL's cloud APIs for authentication, device discovery, and control.
- Each selected AC unit is represented as a Home Assistant climate entity.
- All API interactions and integration actions are logged using Home Assistant's logging facilities.

## Key Technical Decisions
- Authentication is performed using only email and password, following the official TCL API flow.
- Device discovery and control use the same endpoints and payloads as the reference script.
- The integration is designed to be stateless where possible, storing only necessary tokens and device info.
- Extensive logging is implemented at every step for development and debugging.

## Design Patterns
- **Config Flow Pattern:** Uses Home Assistant's config flow to prompt for credentials and device selection.
- **Entity Pattern:** Each AC unit is a subclass of Home Assistant's ClimateEntity, encapsulating state and control logic.
- **API Client Pattern:** A dedicated client module handles all communication with TCL's cloud APIs, abstracting authentication, device listing, and control.
- **Logging Pattern:** All requests, responses, and errors are logged at DEBUG level for maximum transparency.

## Component Relationships
- **Config Flow** interacts with the user and stores configuration.
- **API Client** handles all TCL server communication.
- **Climate Entities** represent and control individual AC units.
- **Logger** records all actions and API traffic for troubleshooting.

## Critical Implementation Paths
- User authentication and token management.
- Device discovery and mapping to Home Assistant entities.
- Command dispatch (on/off) to TCL cloud and state synchronization.
- Error handling and user feedback during setup and operation.
