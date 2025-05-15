# TCL AC Active Context

## Current Focus
- Implementing climate entity integration (climate.py)
- Adding coordinator pattern for status updates
- Testing with real AC unit

## Recent Changes
- Completed local network API implementation
- Updated configuration flow for local setup
- Removed cloud dependencies

## Next Steps
1. Implement climate entity with all features
2. Add coordinator for regular status updates
3. Implement device discovery
4. Add error handling and recovery
5. Write unit tests

## Active Decisions
- Using async/await pattern throughout
- Local network control only (no cloud API)
- Following Home Assistant custom component standards
- Targeting HACS compatibility

## Important Patterns
- API calls will use aiohttp with timeout
- Configuration via config entries
- Options flow for advanced settings
