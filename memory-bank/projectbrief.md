# Project Brief

## Project Name
TCL Home Assistant HACS Integration

## Objective
Develop a Home Assistant HACS integration that allows users to control TCL air conditioners via the TCL cloud platform.

## Core Requirements
- Ask the user for their email and password to authenticate with TCL servers.
- Authenticate using the official TCL API endpoints.
- List all available TCL air conditioner devices associated with the user account.
- Allow the user to select which AC units to import into Home Assistant.
- Create Home Assistant climate entities for each imported AC unit.
- Allow users to turn AC units on or off from Home Assistant.
- Log all API requests, responses, and integration actions extensively for development and debugging.

## Constraints
- Only email and password are required from the user for authentication.
- The integration must be installable via HACS.
- The code should be structured for maintainability and extensibility.
- Logging should be as verbose as possible during development.

## Deliverables
- A fully functional HACS integration package.
- Documentation for installation and configuration.
- A release pushed to the GitHub repository: https://github.com/catalinstroie/tcl-homeassistant

## Source Materials
- Reference Python script for TCL API interaction.
- Sample log file demonstrating authentication, device listing, and control.
