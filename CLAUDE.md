# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python-based AWS API Gateway resource creation tool for automating HTTP method setup (GET, POST, PUT, DELETE, PATCH) with VPC Link integration and Cognito authentication. The tool supports configuration profiles for reusability and creates methods with proper authorization headers, CORS handling, and backend integration.

## Running the Tool

```bash
python3 apiGatewayCreator.py
```

The script is interactive - no command-line arguments needed. It will guide you through configuration.

## Architecture

### Core Components

**`ConfigManager` (lines 45-85)**: Loads and manages INI configuration files from `config/` directory:
- `method_configs.ini` - HTTP method defaults (timeout, passthrough, integration type)
- `auth_headers.ini` - Authorization headers by type (COGNITO_ADMIN, COGNITO_CUSTOMER, NO_AUTH)
- `cors_headers.ini` - CORS configuration
- `response_templates.ini` - Response template mappings

**`APIGatewayManager` (lines 554-836)**: Main AWS API Gateway interaction layer:
- Resource creation and path parsing (handles parameterized paths like `/users/{id}`)
- HTTP method creation with integration setup
- Path vs Backend path separation (see Path Architecture below)
- VPC Link integration configuration
- Cognito authorizer attachment

### Path Architecture

The tool uses **two distinct paths**:

1. **Backend Path (FULL_BACKEND_PATH)**: Complete microservice path (e.g., `/discounts/v2/campaigns/{id}`)
2. **API Gateway Resource Path**: Derived by stripping first segment (e.g., `/v2/campaigns/{id}`)

This separation is implemented in `create_endpoint_workflow()` (lines 838-899). The first path segment typically represents the microservice name and is handled by VPC routing.

### Configuration Flow

Two configuration modes (handled in `select_configuration_source()`, lines 350-374):

**Profile Mode**: Load saved `.ini` files from `profiles/` directory
- Validates resources still exist before use (`validate_configuration_profile()`, lines 321-348)
- Checks API, VPC Link, Authorizer, and Cognito Pool validity
- Reuses HTTP methods across multiple endpoints

**Manual Mode**: Interactive selection via `get_interactive_config()` (lines 475-548)
- Groups APIs by base name, excluding PROD by default
- Selects VPC Link, Authorizer, User Pool, Stage
- Configures authorization type (ADMIN/CUSTOMER/NO_AUTH)
- Option to save as profile for reuse

### Authorization Types

Three auth types configured via `auth_headers.ini`:

- **COGNITO_ADMIN**: Claims include `custom:admin_id` - for admin endpoints
- **COGNITO_CUSTOMER**: Claims include `custom:customer_id` - for customer endpoints
- **NO_AUTH**: Minimal headers (KNOWN-TOKEN-KEY, X-Amzn-Request-Id only)

Headers are automatically mapped as integration request headers when creating methods (see `create_http_method()`, lines 691-782).

### Profile System

Profiles stored as INI files in `profiles/` directory containing:
- API ID
- Stage variable name for VPC Link (referenced as `${stageVariables.<connection_variable>}`)
- Authorizer ID and Cognito Pool name
- Backend host with stage variables (e.g., `https://${stageVariables.urlDiscountsPrivate}`)
- Auth type and CORS type

The VPC Link uses a stage variable reference instead of a hardcoded VPC Link ID, allowing environment-specific configuration. The backend host also uses stage variables for flexibility across environments.

Example profile structure: `profiles/dev-customer-get.ini`

### Resource Creation Logic

`ensure_resources_exist()` (lines 646-682):
- Parses nested paths into segments
- Checks each segment exists before creating
- Prompts for confirmation before creating new resources
- Automatically creates OPTIONS method for new resources
- Handles parameterized segments (e.g., `{id}`, `{customerId}`)

### Error Handling

`log_error()` function (lines 18-43) creates timestamped error dump files with full tracebacks. Error files: `error_dump_YYYYMMDD_HHMMSS.log`

## Configuration Files

### auth_headers.ini Format

Headers use AWS API Gateway context variable syntax:
```ini
[COGNITO_ADMIN]
Claim-User-Id = context.authorizer.claims.custom:admin_id
CognitoPool = 'admin'
```

Values are passed directly to AWS CLI commands as integration request parameters.

### method_configs.ini Defaults

All HTTP methods use same config:
- 29000ms timeout
- HTTP_PROXY integration type via VPC_LINK
- WHEN_NO_MATCH passthrough behavior

### Profile INI Structure

```ini
[PROFILE]
api_id = <rest-api-id>
connection_variable = <stage-variable-name-for-vpc-link>
authorizer_id = <cognito-authorizer-id>
cognito_pool = <pool-name>
backend_host = https://${stageVariables.variableName}
auth_type = COGNITO_ADMIN|COGNITO_CUSTOMER|NO_AUTH
cors_type = DEFAULT
```

Note: `connection_variable` should be the name of the stage variable containing the VPC Link ID (e.g., "vpcLinkId"), not the actual VPC Link ID. The tool will use `${stageVariables.<connection_variable>}` in the integration. The `backend_host` can reference a different stage variable for the backend URL.

## Multi-Endpoint Creation

Main loop (lines 927-967) allows creating multiple endpoints without restarting:
- First endpoint: configure methods + path
- Subsequent endpoints: reuse methods, only specify new path
- Option to save profile after first successful creation

## AWS CLI Usage

All AWS interactions use subprocess calls to AWS CLI:
- `aws apigateway` - API Gateway resources
- `aws cognito-idp` - User pool listings

Requires AWS CLI configured with appropriate credentials and region.

## Key Functions Reference

- `select_api_grouped()` (line 143): Groups APIs by name, filters environments
- `select_http_methods()` (line 190): Multi-select interface for HTTP methods
- `parse_uri_path()` (line 603): Parses paths into segments, identifies parameters
- `create_http_method()` (line 691): Complete method creation with auth + integration
- `create_options_method()` (line 784): CORS preflight configuration
- `create_endpoint_workflow()` (line 838): Orchestrates full endpoint creation
