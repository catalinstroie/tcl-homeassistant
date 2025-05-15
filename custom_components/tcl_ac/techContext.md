# TCL AC Technical Context

## Core Technologies
- Python 3.9+
- Home Assistant Core (2023.5+)
- AsyncIO for network operations
- aiohttp for HTTP requests
- Home Assistant's DataUpdateCoordinator pattern

## Architecture
- API layer (api.py) handles direct communication with AC units
- Config flow (config_flow.py) manages user setup
- Climate entity (climate.py) provides HA integration
- Constants (const.py) centralize configuration
- Manifest (manifest.json) defines package metadata

## Development Setup
1. Python virtual environment
2. Home Assistant development environment
3. HACS for testing installation
4. pytest for unit tests
5. Local TCL AC unit for testing

## Dependencies
- aiohttp
- async_timeout
- Home Assistant core dependencies

## Key Implementation Patterns
- Async/await for all I/O operations
- Configuration via config entries
- Entity platform integration
- Options flow for settings
- Coordinator pattern for data updates
