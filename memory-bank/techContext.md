# TCL AC Integration - Technical Context

## Core Technologies
- Python 3.9+
- Home Assistant Core
- aiohttp for async HTTP requests
- AWS4Auth for AWS request signing
- PyJWT for token validation

## Dependencies
- requests
- requests_aws4auth
- pyjwt
- aiohttp

## API Endpoints
- TCL Account Login: `https://pa.account.tcl.com`
- TCL Device API: `https://prod-eu.aws.tcljd.com`
- AWS Cognito: `https://cognito-identity.eu-central-1.amazonaws.com`
- AWS IoT: `a2qjkbbsk6qn2u-ats.iot.eu-central-1.amazonaws.com`

## Development Setup
1. Clone repository into Home Assistant custom_components
2. Install dependencies via pip
3. Configure through Home Assistant UI

## Testing Approach
- Manual testing with real TCL AC units
- Mock API responses for unit tests (future)
- Integration tests with Home Assistant (future)
