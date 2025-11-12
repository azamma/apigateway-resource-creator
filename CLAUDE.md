# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

**Project**: AWS API Gateway Creator - Automated endpoint creation for AWS API Gateway with VPC Link, Cognito auth, and multi-method support.

**Language**: Python 3.7+

**Key Commands**:
```bash
# Run the main endpoint creator tool
python3 apiGatewayCreator.py

# Verify AWS CLI is configured
aws sts get-caller-identity
```

**Main Components**:
- `apiGatewayCreator.py` (1685 lines) - Endpoint creation orchestration
- `common/` - Shared utilities (constants, exceptions, logging, models)
- `gateway_creator/` - Configuration and AWS management
- `config/` - INI configuration files (method, auth, CORS, response templates)

## Development

### Prerequisites
- Python 3.7+ installed
- AWS CLI v2 configured with valid credentials
- IAM permissions for API Gateway and Cognito operations

### Running the Application
```bash
# Main endpoint creator tool (interactive)
python3 apiGatewayCreator.py

# Verify AWS configuration
aws sts get-caller-identity
```

### Code Organization

**Total lines of code**: ~3,200 lines across 10 Python files

**Package structure**:
- `common/constants.py` (221 lines) - Configuration constants, enums, messages
- `common/exceptions.py` (117 lines) - Custom exception hierarchy
- `common/logging_config.py` (265 lines) - Logging system with ANSI colors
- `common/models.py` (219 lines) - Dataclasses for type safety
- `gateway_creator/config_manager.py` (252 lines) - INI config and profile management
- `gateway_creator/aws_manager.py` (205 lines) - AWS CLI interface
- `gateway_creator/ui_components.py` (139 lines) - UI helpers and formatting

### Key Development Patterns

**Logging**: All modules use centralized logger from `common.logging_config`
```python
from common import get_logger
logger = get_logger(__name__)
logger.success("Operation completed")
logger.dump_error(exception, {"context": "details"})  # Creates error_dump_*.log
```

**Error Handling**: Use custom exceptions from `common.exceptions` for specific error types
```python
from common import ResourceNotFoundException, ConfigurationException
# Catch specific exceptions for targeted handling
```

**Configuration**: Load from INI files via `ConfigManager` in `gateway_creator/config_manager.py`
- INI files in `config/` directory for method, auth, CORS, response templates
- User profiles saved in `profiles/` directory (not in git)
- Error logs in `reports/` directory (not in git)

**AWS Operations**: All AWS calls use subprocess to invoke AWS CLI v2
- No external AWS SDK dependencies (uses built-in subprocess)
- Commands executed directly: `aws apigateway`, `aws cognito-idp`, etc.
- Environment variables for AWS_REGION, AWS_PROFILE, credentials

### Adding Features

**New Authorization Type**:
1. Add section to `config/auth_headers.ini`
2. Update `AuthType` enum in `common/constants.py`
3. Update `select_auth_type()` menu in `apiGatewayCreator.py`

**New Configuration Profile**:
- Manually create `profiles/<name>.ini` with PROFILE section
- Or use interactive save after creating first endpoint

**New Validation Check**:
- Add method to profile validation in `gateway_creator/config_manager.py`
- Follow existing pattern in `validate_profile()` method

## Project Overview

**API Gateway Creator** is a Python-based automation tool for AWS API Gateway endpoint creation. It provides:

- **Automated HTTP Method Creation** - Multi-method endpoints with intelligent configuration
- **VPC Link Integration** - Seamless microservice backend connectivity
- **Cognito Authentication** - Built-in support for Admin/Customer authorization
- **Configuration Profiles** - Save and reuse configurations across deployments
- **Multi-Endpoint Support** - Create multiple endpoints in a single session

**Language**: Python 3.7+
**Architecture**: Modular with separate packages for configuration, gateway management, and UI
**AWS Services**: API Gateway, Cognito, VPC Links

## Architecture

### Design Patterns

**Two-Path Architecture**:
The tool distinguishes between two paths:

1. **Backend Path** (FULL_BACKEND_PATH): Complete microservice path sent to backend via integration
   - Example: `/discounts/v2/campaigns/{id}`
   - First segment represents microservice name (used by VPC routing/load balancer)
   - User provides this when asked "Path COMPLETO del backend"

2. **API Gateway Resource Path**: Path created in API Gateway (first segment removed)
   - Example: `/v2/campaigns/{id}`
   - What users see in API Gateway console
   - Automatically stripped from backend path in `create_endpoint_workflow()` line 1538

**Important**: When you enter `/discounts/prueba`:
- API Gateway only creates `/prueba` as a resource
- Does NOT search for or create a `/discounts` resource
- The first segment `/discounts` is only used in the backend integration URI
- The VPC Link resolves the `{stageVariables.urlDiscountsPrivate}` to route to the correct microservice

The transformation happens in `create_endpoint_workflow()` lines 1535-1540.

**Configuration Layers**:
1. **System Config** - INI files in `config/` (read-only defaults)
2. **User Profiles** - Saved configs in `profiles/` for reuse
3. **Interactive Input** - User selections during execution

**Integration Strategy**:
- **VPC Link**: Private network connectivity to microservices
- **Cognito Auth**: ID token validation via authorizers
- **Claim Mapping**: Headers map Cognito claims to backend via stage variables

### Data Flow

```
User Input (CLI)
  ↓
Config Manager (loads INI + profiles)
  ↓
AWS Manager (executes AWS CLI commands)
  ↓
AWS Resources (creates endpoints in real-time)
  ↓
Logging System (ANSI colors + error dumps)
```

**Key Data Models** (in `common/models.py`):
- `APIConfig` - Stores API, stage, auth configuration
- `EndpointConfig` - Path and HTTP methods for endpoint
- `MethodSpec` - HTTP method timeout and integration settings
- `AWSResource` - AWS resource metadata from API responses

### Configuration Priority

When creating endpoints:
1. Load base config from `config/method_configs.ini` (timeout, integration type)
2. Load auth headers from `config/auth_headers.ini` based on auth type
3. Override with user selections (API, methods, backend path)
4. Optionally save as profile in `profiles/` for reuse
5. Execute AWS CLI commands to create resources

## Core Workflows

### Creating Endpoints

The interactive tool guides you through endpoint creation:
```bash
python3 apiGatewayCreator.py
```

**Workflow options**:
1. **Load Profile** - Quick setup using saved configuration
2. **Manual Configuration** - Full interactive setup with all options

**First endpoint process**:
1. Choose configuration source (Profile or Manual)
2. Select API, HTTP methods, authorizer, and Cognito pool
3. Configure endpoint with backend path
4. Option to save configuration as reusable profile
5. Create endpoint in AWS

**Additional endpoints**:
- Reuse configuration from first endpoint or modify as needed
- Continue loop until complete


## Project Structure

```
apigateway-resource-creator/
├── apiGatewayCreator.py           (Main entry point)
├── CLAUDE.md                      (This file)
├── README.md                      (User documentation)
│
├── gateway_creator/               (Creator package)
│   ├── __init__.py
│   ├── config_manager.py          - INI config loading
│   ├── aws_manager.py             - AWS CLI interface
│   └── ui_components.py           - UI/menu components
│
├── common/                        (Shared utilities)
│   ├── __init__.py
│   ├── constants.py               - Constants & enums
│   ├── exceptions.py              - Custom exceptions
│   ├── logging_config.py          - Logging system
│   └── models.py                  - Data models
│
├── config/                        (Configuration files)
│   ├── method_configs.ini         - HTTP method defaults
│   ├── auth_headers.ini           - Authorization headers
│   ├── cors_headers.ini           - CORS configuration
│   └── response_templates.ini     - Response templates
│
├── profiles/                      (User's saved configurations)
│   └── *.ini
│
└── reports/                       (Error logs)
    └── error_dump_<timestamp>.log
```

## Core Packages

### Common Package (`common/`)

**Purpose**: Shared utilities, constants, and data models

#### `constants.py` (221 lines)

AWS configuration constants:
- `CONFIG_TIMEOUT_MS = 29000` - Integration timeout
- `CONFIG_PASSTHROUGH_BEHAVIOR = "WHEN_NO_MATCH"` - Body handling
- `CONFIG_INTEGRATION_TYPE = "HTTP_PROXY"` - Integration mode
- `CONFIG_CONNECTION_TYPE = "VPC_LINK"` - Connection type

Enums:
- `AuthType`: COGNITO_ADMIN, COGNITO_CUSTOMER, NO_AUTH
- File path constants for config directories

#### `exceptions.py` (117 lines)

Custom exception hierarchy:
```
APIGatewayException (base)
├── AWSException - AWS CLI failures
├── ConfigurationException - Config errors
├── ProfileException - Profile load/save
├── ValidationException - Validation failures
├── ResourceNotFoundException - Missing resources
├── UserCancelledException - User cancellation
├── MethodCreationException - Method creation failure
└── IntegrationException - Integration setup failure
```

**Usage**: Catch specific exceptions for targeted error handling and user feedback

#### `logging_config.py` (265 lines)

Centralized logging with ANSI colors:

```python
from common.logging_config import get_logger

logger = get_logger(__name__)
logger.info("Message")
logger.success("Success message")
logger.warning("Warning")
logger.error("Error message")
logger.dump_error(exception, context_dict)  # Creates error dump file
```

Features:
- Colored output for different log levels
- `dump_error()` saves timestamped error dumps with full traceback
- Singleton pattern - one logger instance per module

#### `models.py` (219 lines)

Dataclasses for type-safe configuration:

```python
@dataclass
class APIConfig:
    api_id: str
    stage_variable: str
    authorizer_id: str
    cognito_pool: str
    backend_host: str
    auth_type: AuthType
    cors_type: str

@dataclass
class EndpointConfig:
    full_backend_path: str
    methods: List[str]
    profile_name: Optional[str]

@dataclass
class MethodSpec:
    http_method: str
    timeout_ms: int
    integration_type: str
    passthrough_behavior: str
```

### Gateway Creator Package (`gateway_creator/`)

**Purpose**: API Gateway resource creation and configuration

#### `config_manager.py` (252 lines)

**ConfigManager class:**
- Loads INI files from `config/` directory
- Methods:
  - `get_method_config(method)` → MethodSpec
  - `get_auth_headers(auth_type)` → dict
  - `get_cors_headers(cors_type)` → dict
  - `get_response_templates()` → dict

**ProfileConfigManager class:**
- `load_profile(profile_name)` → dict
- `save_profile(profile_name, config)` → bool
- `validate_profile(profile_name)` → ValidationResult
- `list_profiles()` → List[str]

Profile validation checks:
- API still exists in AWS
- Stage variable exists
- Authorizer still exists
- Cognito pool still exists

#### `aws_manager.py` (205 lines)

AWS CLI interface (implementation in `apiGatewayCreator.py`, marked for refactoring):

Methods for:
- Listing REST APIs
- Creating resources and methods
- Configuring integrations
- Attaching authorizers
- Setting up VPC Links

**Note**: Most AWS operations use subprocess calls to AWS CLI directly

#### `ui_components.py` (139 lines)

UI helper functions:
- `print_menu_header(title)` - Menu styling
- `print_menu_option(number, option)` - Option formatting
- `print_summary_item(label, value)` - Configuration display
- `print_box_message(message, style)` - Box formatting
- `clear_screen()` - Terminal clear

## Configuration Architecture

### Path Architecture

The tool uses **two distinct paths**:

1. **Backend Path (FULL_BACKEND_PATH)**: Complete microservice path
   - Example: `/discounts/v2/campaigns/{id}`
   - First segment represents microservice name (handled by VPC routing)

2. **API Gateway Resource Path**: Derived by stripping first segment
   - Example: `/v2/campaigns/{id}`
   - Created in API Gateway

**Implemented in**: `create_endpoint_workflow()` - apiGatewayCreator.py (line 848)

### Configuration Sources

Two configuration modes in `select_configuration_source()`:

#### Profile Mode
- Load saved `.ini` files from `profiles/` directory
- Validates all resources still exist before use
- Reuses HTTP methods across multiple endpoints
- Fast configuration for repeated deployments

**Validation checks:**
- API exists (`validate_resource_exists()`)
- Stage variable exists
- Authorizer exists
- Cognito Pool exists

#### Manual Mode
- Interactive selection via `get_interactive_config()` (line 479)
- Groups APIs by base name using `select_api_grouped()` (line 143)
- Excludes PROD environment by default (unless explicitly selected)
- Selects Stage and stage variables for VPC Link
- Chooses Authorizer and User Pool
- Configures authorization type
- Option to save as profile for reuse

### Configuration Files

Located in `config/` directory:

#### `method_configs.ini`

HTTP method defaults (all methods use same config):
```ini
[DEFAULT]
timeout_millis = 29000
passthrough_behavior = WHEN_NO_MATCH
connection_type = VPC_LINK
integration_type = HTTP_PROXY
response_status_code = 200
```

#### `auth_headers.ini`

Integration request headers by authorization type:

```ini
[COGNITO_ADMIN]
Claim-Email = context.authorizer.claims.email
Claim-User-Id = context.authorizer.claims.custom:admin_id
CognitoPool = 'admin'
KNOWN-TOKEN-KEY = stageVariables.knownTokenKey
X-Amzn-Request-Id = context.requestId

[COGNITO_CUSTOMER]
Claim-Email = context.authorizer.claims.email
Claim-User-Id = context.authorizer.claims.custom:customer_id
CognitoPool = 'customer'
KNOWN-TOKEN-KEY = stageVariables.knownTokenKey
X-Amzn-Request-Id = context.requestId

[NO_AUTH]
KNOWN-TOKEN-KEY = stageVariables.knownTokenKey
X-Amzn-Request-Id = context.requestId
```

**Context variables:**
- `context.authorizer.claims.*` - Cognito claims
- `stageVariables.*` - Stage variables (VPC Link ID, backend host, etc.)
- `context.requestId` - AWS request ID

#### `cors_headers.ini`

CORS configuration for OPTIONS method:
```ini
[DEFAULT]
Access-Control-Allow-Headers = 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token,X-Api-Version'
Access-Control-Allow-Methods = 'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT'
Access-Control-Allow-Origin = '*'
```

#### `response_templates.ini`

Response mapping templates (application/json, text/html, etc.)

### Profile Format

Profiles saved in `profiles/<name>.ini`:

```ini
[PROFILE]
api_id = rest-api-xxxxxxxx
connection_variable = vpcLinkId
authorizer_id = authorizer-xxxxxxxx
cognito_pool = my-user-pool-name
backend_host = https://${stageVariables.urlBackendPrivate}
auth_type = COGNITO_ADMIN
cors_type = DEFAULT
```

**Important**:
- `connection_variable` is the **stage variable name** containing the VPC Link ID (e.g., "vpcLinkId"), NOT the actual VPC Link ID
- `backend_host` can reference different stage variables for flexibility across environments
- Example: `https://${stageVariables.urlDiscountsPrivate}` uses URL from stage variables

## Authorization Types

Three authorization types configured in `auth_headers.ini`:

### COGNITO_ADMIN
- Claims include `custom:admin_id`
- For administrative/privileged endpoints
- Headers automatically include admin-specific claims
- **When to use**: Admin dashboard, management APIs, staff-only endpoints

### COGNITO_CUSTOMER
- Claims include `custom:customer_id`
- For customer-facing endpoints
- Headers automatically include customer-specific claims
- **When to use**: Customer portal, user-accessible APIs, commerce endpoints

### NO_AUTH
- Minimal headers (KNOWN-TOKEN-KEY, X-Amzn-Request-Id only)
- For public APIs or legacy integrations
- **When to use**: Public endpoints, health checks, webhooks (if no auth needed)

**Headers are automatically mapped** in `create_http_method()` (line 698) as integration request headers.

## Resource Creation Logic

### `ensure_resources_exist()` (line 653)

Resource creation workflow:

1. **Parse path** into segments using `parse_uri_path()` (line 610)
2. **Validate each segment** exists using `find_resource_by_path()` (line 631)
3. **Confirm creation** with user for new resources
4. **Create resources** recursively (parent → child)
5. **Auto-create OPTIONS** for CORS preflight (line 682)

**Handles:**
- Parameterized segments: `{id}`, `{customerId}`
- Nested paths: `/v2/campaigns/{id}/analytics`
- User cancellation: Returns None if user declines

**Returns**: Root resource ID or None if cancelled

### `create_http_method()` (line 698)

Complete method creation with authorization and integration:

**Parameters:**
- api_id, resource_id, method (GET, POST, etc.)
- authorizer_id, cognito_pool
- auth_type (COGNITO_ADMIN, COGNITO_CUSTOMER, NO_AUTH)
- backend_host, stage_variable (for VPC Link)

**Process:**
1. Get auth headers from config (based on auth_type)
2. Create authorization in API Gateway
3. Set up integration (VPC Link endpoint)
4. Configure integration request headers
5. Set response mapping
6. Create method response

**AWS CLI commands used:**
- `aws apigateway put-method` - Create method with authorization
- `aws apigateway put-integration` - Set integration to VPC Link
- `aws apigateway put-integration-request-parameters` - Map headers
- `aws apigateway put-method-response` - Define response models

## Multi-Endpoint Creation

### Main Loop (line 938)

Allows creating multiple endpoints without restarting:

**First endpoint:**
- Full configuration flow (methods, paths, auth)
- Creates resources and methods
- Option to save configuration as profile after success

**Subsequent endpoints:**
- Default: reuse methods from previous endpoint
- Option: change methods or auth type per endpoint
- Continue until user exits

**Loop control:**
```python
while True:
    # Create endpoint
    # Ask: "Create another endpoint? (y/n)"
    if response.lower() != 'y':
        break
```

## Error Handling

### `log_error()` Function (line 18)

Centralized error handling with timestamped dumps:

```python
try:
    # operation
except Exception as e:
    logger.dump_error(e, {"context": "operation", "api_id": api_id})
    # File created: reports/error_dump_20251028_153045.log
```

**Error files:**
- Location: `reports/` directory
- Format: `error_dump_YYYYMMDD_HHMMSS.log`
- Contains: Full traceback + context + relevant data

### Exception Hierarchy

Catch specific exceptions for targeted handling:

```python
try:
    # operation
except ResourceNotFoundException:
    # Handle missing resource
except ValidationException:
    # Handle validation error
except AWSException:
    # Handle AWS CLI failure
except APIGatewayException:
    # Catch any gateway error
```

## AWS Interactions

All AWS operations use **subprocess calls to AWS CLI** v2:

```bash
aws apigateway list-rest-apis
aws apigateway get-resources --rest-api-id <id>
aws apigateway get-method --rest-api-id <id> --resource-id <id> --http-method GET
aws apigateway put-method --rest-api-id <id> --resource-id <id> --http-method POST \
  --type AWS_IAM --authorization-type AWS_IAM --authorizer-id <id>
aws apigateway put-integration --rest-api-id <id> --resource-id <id> --http-method GET \
  --type HTTP_PROXY --integration-http-method GET \
  --uri https://${stageVariables.backend}
aws cognito-idp list-user-pools --max-results 50
```

**Requires:**
- AWS CLI v2 installed and configured
- AWS credentials configured (via ~/.aws/credentials or environment)
- Appropriate IAM permissions for API Gateway and Cognito

### AWS Permissions Required

```
apigateway:ListRestApis
apigateway:GetRestApis
apigateway:GetResources
apigateway:GetResource
apigateway:GetMethod
apigateway:GetAuthorizer
apigateway:CreateResource
apigateway:PutMethod
apigateway:PutIntegration
apigateway:PutMethodResponse
apigateway:PutIntegrationResponse
apigateway:PutIntegrationRequestParameters
apigateway:GetMethodResponse
cognito-idp:ListUserPools
cognito-idp:DescribeUserPool
```

## Key Functions Reference

### apiGatewayCreator.py

**Configuration & Selection:**
- `select_api_grouped()` (143) - Groups APIs, filters PROD
- `select_http_methods()` (190) - Multi-select interface (comma-separated)
- `select_auth_type()` (211) - Authorization type menu
- `list_configuration_profiles()` (238) - Lists profiles from `profiles/`
- `select_configuration_source()` (354) - Profile vs Manual choice

**Profile Management:**
- `save_configuration_profile()` (249) - Saves to `profiles/<name>.ini`
- `load_configuration_profile()` (285) - Loads profile
- `validate_configuration_profile()` (321) - Verifies resources exist

**Interactive Configuration:**
- `get_endpoint_and_methods()` (456) - Prompts for endpoint config
- `get_interactive_config()` (479) - Full manual configuration flow

**Resource Management:**
- `parse_uri_path()` (610) - Parses paths into segments
- `find_resource_by_path()` (631) - Searches for existing resource
- `create_resource()` (643) - Creates single resource
- `ensure_resources_exist()` (653) - Creates full path hierarchy

**Method Creation:**
- `extract_path_parameters()` (691) - Extracts `{param}` placeholders
- `create_http_method()` (698) - Complete method creation with auth
- `create_options_method()` (794) - CORS preflight setup
- `verify_methods_integration()` (833) - Validates method integrations

**Orchestration:**
- `create_endpoint_workflow()` (848) - Orchestrates full endpoint creation
- `main()` (911) - Main entry with loop

## Development Guidelines

### Adding New Authorization Types

1. **Add to `auth_headers.ini`:**
   ```ini
   [NEW_AUTH_TYPE]
   Header-Name = context.value
   Other-Header = stageVariables.var
   ```

2. **Update `AuthType` enum** in `common/constants.py`

3. **Update `select_auth_type()`** menu in apiGatewayCreator.py

4. **Test**: Create endpoint with new auth type, verify headers in AWS console

### Adding New Configuration Profiles

Profiles are automatically saved after first successful endpoint creation. To manually create:

1. **Create file**: `profiles/my-config.ini`
2. **Add content**:
   ```ini
   [PROFILE]
   api_id = rest-api-xxxxxxxx
   connection_variable = vpcLinkId
   authorizer_id = authorizer-xxxxxxxx
   cognito_pool = my-pool
   backend_host = https://${stageVariables.backend}
   auth_type = COGNITO_ADMIN
   cors_type = DEFAULT
   ```

3. **Use**: Select "Load configuration profile" and choose your profile

### Adding Error Handling

Use custom exceptions from `common/exceptions.py`:

```python
from common.exceptions import ConfigurationException, AWSException
from common.logging_config import get_logger

logger = get_logger(__name__)

try:
    # operation
except Exception as e:
    logger.error(f"Operation failed: {str(e)}")
    logger.dump_error(e, {"context": "operation", "api_id": api_id})
    raise ConfigurationException(f"Failed to configure: {str(e)}") from e
```

### Testing Endpoints

After creating an endpoint:

1. **Verify in AWS Console:**
   - Navigate to API Gateway → REST API → Resources
   - Check resource path created correctly
   - Verify method shows authorizer

2. **Test authorization:**
   ```bash
   # Get Cognito token
   TOKEN=$(aws cognito-idp initiate-auth \
     --auth-flow USER_PASSWORD_AUTH \
     --client-id <client-id> \
     --auth-parameters USERNAME=user PASSWORD=pass \
     --user-pool-id <pool-id> | jq -r .AuthenticationResult.IdToken)

   # Call endpoint
   curl -H "Authorization: Bearer $TOKEN" https://<api-id>.execute-api.<region>.amazonaws.com/<stage>/endpoint
   ```

3. **Check integration:**
   - Verify backend receives request with correct headers
   - Check headers include authentication claims

### Debugging Issues

**Enable verbose output:**
```python
# In common/logging_config.py
logger.set_level("DEBUG")
```

**Check error dumps:**
```bash
ls reports/error_dump_*.log
cat reports/error_dump_<timestamp>.log
```

**Verify AWS resources:**
```bash
# List APIs
aws apigateway get-rest-apis

# Get API resources
aws apigateway get-resources --rest-api-id <id>

# Check method
aws apigateway get-method --rest-api-id <id> --resource-id <id> --http-method GET

# Check integration
aws apigateway get-integration --rest-api-id <id> --resource-id <id> --http-method GET
```

## Important Files

### Configuration Files (read-only in git)
- `config/method_configs.ini` - HTTP method defaults (timeout: 29s, passthrough: WHEN_NO_MATCH)
- `config/auth_headers.ini` - Authorization headers for COGNITO_ADMIN, COGNITO_CUSTOMER, NO_AUTH
- `config/cors_headers.ini` - CORS preflight headers for OPTIONS methods
- `config/response_templates.ini` - Response mapping templates
- `config/whitelist.json` - Security check whitelist (endpoints to exclude from analysis)

### Generated Directories (not in git)
- `profiles/` - User-saved endpoint configurations (*.ini files)
- `reports/` - Error logs with format `error_dump_YYYYMMDD_HHMMSS.log` containing full tracebacks

### Entry Points
- `apiGatewayCreator.py` - Main endpoint creation tool (1685 lines)
- Future security checker scripts may reference `config/whitelist.json`

## Common Workflows

### Create Single Endpoint

```bash
python3 apiGatewayCreator.py
# Select: Manual configuration
# Select: API, Methods (e.g., 1,2 for GET,POST)
# Select: Authorizer and Cognito Pool
# Select: Stage and Stage Variables
# Select: Auth Type (COGNITO_ADMIN, COGNITO_CUSTOMER, NO_AUTH)
# Enter: Full backend path (e.g., /discounts/v2/campaigns/{id})
# Choose: Save profile? (y/n)
```

### Create Multiple Endpoints with Profile

```bash
python3 apiGatewayCreator.py
# Select: Load configuration profile
# Select: Existing profile
# Enter: Full backend path (endpoint 1)
# Choose: Create another endpoint? (y)
# Enter: Full backend path (endpoint 2)
# Repeat until done
```

### Validate Saved Profile

Profiles are automatically validated before use. To manually validate:

1. Load profile in creator tool
2. Tool checks all resources exist
3. If any missing, option to configure manually

## Performance Notes

**Creator Tool:**
- Profile loading: < 1 second
- Manual configuration: 10-30 seconds (depends on API count)
- Endpoint creation: 5-15 seconds per endpoint

**Optimization tips:**
- Use profiles for repeated deployments
- Run during off-peak hours to avoid API rate limits

## Dependencies

**Built-in modules only:**
- `subprocess` - AWS CLI execution
- `json` - JSON parsing
- `configparser` - INI file parsing
- `concurrent.futures.ThreadPoolExecutor` - Parallel processing
- `pathlib.Path` - File system operations
- `dataclasses` - Type-safe data models
- `datetime`, `enum`, `typing`, `re`, `os`, `sys`

**No external packages required** - uses AWS CLI for all AWS interactions

## Environment Variables

**AWS Configuration:**
```bash
export AWS_REGION=us-east-1
export AWS_PROFILE=my-profile
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
```

**Application Configuration (optional):**
```bash
export APIGATEWAY_LOG_LEVEL=INFO
export APIGATEWAY_PROFILE_DIR=./profiles
export APIGATEWAY_CONFIG_DIR=./config
```

## File Exclusions (.gitignore)

```
profiles/*.ini              # Contain sensitive API IDs
error_dump_*.log           # Error logs with sensitive info
reports/                   # Generated reports
__pycache__/              # Python cache
*.py[cod]                 # Compiled Python
*.egg-info/               # Package metadata
.vscode/, .idea/          # IDE files
venv/, env/, ENV/         # Virtual environments
.env, .env.local          # Credential files
*.bak, *.tmp              # Temporary files
```

## Recent Architecture Improvements

### Modular Packages (v2.1+)
- **common/** - Centralized utilities, exceptions, logging, and data models
- **gateway_creator/** - Configuration management, AWS CLI interface, and UI components
- Benefits: Code reusability, clean imports, easier testing and maintenance

### Key Features
1. **Multi-method Endpoints** - Create GET, POST, PUT, DELETE, PATCH in one session
2. **Configuration Profiles** - Save and reuse complete endpoint configs
3. **Three Auth Types** - COGNITO_ADMIN, COGNITO_CUSTOMER, NO_AUTH with automatic header mapping
4. **Intelligent Validation** - Profiles validate that saved resources still exist before use
5. **Professional Error Handling** - Custom exceptions with timestamped error dumps in `reports/`
6. **VPC Link Integration** - Private connectivity to microservices with stage variables

## Path Architecture Deep Dive

### Common Questions

**Q: If I enter `/discounts/prueba`, does it search for a `/discounts` resource?**

**A: No.** The tool ONLY creates `/prueba` in API Gateway:
- Input path `/discounts/prueba` is split at line 1538
- First segment (`discounts`) is removed
- Only `/prueba` is created as an API Gateway resource
- The first segment is used only in the backend integration URI

**Q: What happens to the `/discounts` part?**

**A:** It's used in the backend integration:
- Stored in `FULL_BACKEND_PATH = "/discounts/prueba"`
- Used to construct the backend URI: `https://${stageVariables.urlDiscountsPrivate}/discounts/prueba`
- VPC Link sends requests with this full path to the microservice

**Q: Why remove the first segment?**

**A:** AWS API Gateway resources are created relative to the API root, not including the microservice name. The microservice routing is handled by:
1. VPC Link configuration (knows which backend to call)
2. Stage variables (e.g., `urlDiscountsPrivate`)
3. The full backend path in the integration URI

**Example Request Flow:**
```
Client → API Gateway GET /v2/campaigns
           ↓ (creates resource /v2/campaigns only)
        VPC Link resolves ${stageVariables.urlDiscountsPrivate}
           ↓
        Backend GET /discounts/v2/campaigns
```

### Resource Creation Algorithm

When creating an endpoint `/v2/campaigns/{id}`:

1. Parse path → `['v2', 'campaigns', '{id}']`
2. For each segment:
   - Check if `/v2`, `/v2/campaigns`, `/v2/campaigns/{id}` exists
   - If exists: reuse resource ID
   - If not exists: ask user confirmation, create if approved
3. Only these resources are created in AWS API Gateway
4. The backend integration always uses the FULL path provided by user

### Path Parameter Handling

Path parameters are preserved during transformation:
- Input: `/orders/{id}/items/{itemId}`
- Backend: `/orders/{id}/items/{itemId}` (full path preserved)
- API Gateway: `/orders/{id}/items/{itemId}` (because it has 3 segments after removing first)

If only 1 segment with parameters:
- Input: `/{id}` (unusual, only parameter)
- Behavior: No stripping occurs (needs 2+ segments)
- API Gateway: `/{id}`

## Understanding the Codebase

### Entry Points for Development
- **Main workflow**: `apiGatewayCreator.py` - Start here to understand endpoint creation flow
- **Configuration system**: `gateway_creator/config_manager.py` - How INI files and profiles are loaded
- **Error handling**: `common/exceptions.py` - Custom exception types for specific error scenarios
- **Logging**: `common/logging_config.py` - How colored output and error dumps work

### Common Tasks

**Debugging failed endpoint creation**:
1. Check most recent error dump in `reports/` directory
2. Verify AWS CLI credentials with `aws sts get-caller-identity`
3. Review error message in dump file for specific failure reason

**Adding new authorization type**:
1. Add section to `config/auth_headers.ini` with header mappings
2. Add enum value to `AuthType` in `common/constants.py`
3. Add menu option to `select_auth_type()` in `apiGatewayCreator.py`

**Extending configuration**:
- INI files are loaded via `ConfigParser` in `gateway_creator/config_manager.py`
- Add new sections to existing INI files for new defaults
- User profiles in `profiles/` directory override system defaults
