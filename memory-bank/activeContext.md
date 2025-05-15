# TCL AC Integration - Active Context

## Current Focus
- Maintaining stable basic functionality (on/off control)
- Preparing for next feature additions (temperature control)

## Recent Changes
- Implemented proper error handling in API client
- Added device state tracking
- Improved authentication flow reliability

## Next Steps
1. Implement temperature control functionality
2. Add fan speed control options
3. Improve state polling mechanism
4. Add more detailed error reporting

## Key Decisions
- Using AWS4Auth for AWS request signing
- Representing ON state as HVACMode.COOL
- Using email as unique_id for config entries

## Important Patterns
- All API calls go through centralized request method
- Separate error classes for different error types
- Extensive logging for debugging
