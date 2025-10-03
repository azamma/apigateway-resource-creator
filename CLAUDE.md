# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python-based AWS API Gateway resource creation tool for automating HTTP method setup (GET, POST, PUT, DELETE, PATCH) with VPC Link integration and Cognito authentication. The tool supports configuration profiles for reusability and creates methods with proper authorization headers, CORS handling, and backend integration.

## Running the Tool

```bash
python3 apiGatewayCreator.py
```

The script is interactive - no command-line arguments needed. It will guide you through configuration. Requires AWS CLI configured with appropriate credentials and region.

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

Two configuration modes (handled in `select_configuration_source()`, lines 354-378):

**Profile Mode**: Load saved `.ini` files from `profiles/` directory
- Validates resources still exist before use (`validate_configuration_profile()`, lines 321-352)
- Checks API, Stage Variable (VPC Link), Authorizer, and Cognito Pool validity
- Reuses HTTP methods across multiple endpoints
- Allows user to retry with manual configuration if validation fails

**Manual Mode**: Interactive selection via `get_interactive_config()` (lines 479-555)
- Groups APIs by base name using `select_api_grouped()` (line 143)
- Excludes PROD environment by default unless explicitly selected
- Selects Stage and stage variables for VPC Link and backend host
- Selects Authorizer, User Pool
- Configures authorization type (ADMIN/CUSTOMER/NO_AUTH)
- Option to save as profile for reuse after first successful endpoint creation

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

`ensure_resources_exist()` (lines 653-689):
- Parses nested paths into segments using `parse_uri_path()` (line 610)
- Checks each segment exists before creating using `find_resource_by_path()` (line 631)
- Prompts for user confirmation before creating new resources
- Automatically creates OPTIONS method for new resources (line 682-683)
- Handles parameterized segments (e.g., `{id}`, `{customerId}`)
- Returns None if user cancels creation

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

Main loop (lines 938-977) allows creating multiple endpoints without restarting:
- First endpoint: configure methods + path (or load from profile/manual config)
- Subsequent endpoints: reuse methods by default, option to change per endpoint
- Option to save profile after first successful creation (lines 968-972)
- User can exit loop by answering 'n' to continue prompt

## AWS CLI Usage

All AWS interactions use subprocess calls to AWS CLI:
- `aws apigateway` - API Gateway resources
- `aws cognito-idp` - User pool listings

Requires AWS CLI configured with appropriate credentials and region.

## Key Functions Reference

- `log_error()` (line 18): Saves detailed error dumps with timestamp to `error_dump_*.log` files
- `select_api_grouped()` (line 143): Groups APIs by name, filters PROD environment by default
- `select_http_methods()` (line 190): Multi-select interface for HTTP methods (comma-separated)
- `select_auth_type()` (line 211): Interactive menu for authorization type selection
- `list_configuration_profiles()` (line 238): Lists available `.ini` profiles from `profiles/` directory
- `save_configuration_profile()` (line 249): Saves current config to `profiles/<name>.ini`
- `load_configuration_profile()` (line 285): Loads profile from file
- `validate_configuration_profile()` (line 321): Validates all resources in loaded profile still exist
- `select_configuration_source()` (line 354): Main entry point for profile vs manual selection
- `get_endpoint_and_methods()` (line 456): Prompts for endpoint config, optionally reuses methods
- `get_interactive_config()` (line 479): Full manual configuration flow
- `parse_uri_path()` (line 610): Parses paths into segments, identifies parameters
- `find_resource_by_path()` (line 631): Searches for existing resource by path
- `create_resource()` (line 643): Creates single API Gateway resource
- `ensure_resources_exist()` (line 653): Creates full path hierarchy with user confirmation
- `extract_path_parameters()` (line 691): Extracts `{param}` placeholders from paths
- `create_http_method()` (line 698): Complete method creation with auth + integration
- `create_options_method()` (line 794): CORS preflight configuration
- `verify_methods_integration()` (line 833): Verifies all method integrations were created
- `create_endpoint_workflow()` (line 848): Orchestrates full endpoint creation
- `main()` (line 911): Main entry point with loop for multiple endpoint creation
