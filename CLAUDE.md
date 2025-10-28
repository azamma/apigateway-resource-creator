# CLAUDE.md - API Gateway Resource Creator

Comprehensive development guidance for working with the AWS API Gateway Resource Creator project.

## Project Overview

**API Gateway Resource Creator & Security Auditor** is a Python-based automation suite for AWS API Gateway management. It provides two main tools:

1. **Creator Tool** (`apiGatewayCreator.py`) - Interactive HTTP method creation with VPC Link and Cognito integration
2. **Security Auditor** (`apiGatewaySecurityCheck.py`) - Concurrent security analysis and compliance reporting

**Language**: Python 3.7+
**Architecture**: Modular with separate packages for configuration, gateway management, and security analysis
**AWS Services**: API Gateway, Cognito, VPC Links

## Running the Tools

### Primary Tool: API Gateway Creator

```bash
python3 apiGatewayCreator.py
```

**Interactive workflow:**
1. Choose configuration source (Profile or Manual)
2. Select API, HTTP methods, authorizer, and Cognito pool
3. Configure endpoint with backend path
4. Optionally save configuration as reusable profile
5. Create additional endpoints or exit

### Secondary Tool: Security Auditor

```bash
python3 apiGatewaySecurityCheck.py
```

**Functionality:**
- Scans all API Gateway resources for authorization
- Generates CSV reports with security analysis
- Parallel processing for performance (configurable 1-10 workers)
- Filters out development APIs (-DEV, -CI suffixes)

## Project Structure

```
apigateway-resource-creator/
├── apiGatewayCreator.py           (1,619 lines) - Main creator tool
├── apiGatewaySecurityCheck.py     (1,364 lines) - Security audit tool
├── CLAUDE.md                       (this file)
├── README.md                       (user documentation)
│
├── common/                         (Shared utilities - 909 lines)
│   ├── __init__.py                (87 lines)
│   ├── constants.py               (221 lines) - Constants & enums
│   ├── exceptions.py              (117 lines) - Custom exceptions
│   ├── logging_config.py          (265 lines) - Logging system
│   └── models.py                  (219 lines) - Data models (dataclasses)
│
├── gateway_creator/               (Creator package - 635 lines)
│   ├── __init__.py                (39 lines)
│   ├── config_manager.py          (252 lines) - INI config loading
│   ├── aws_manager.py             (205 lines) - AWS CLI interface
│   └── ui_components.py           (139 lines) - UI/menu components
│
├── security_check/                (Security package - 629 lines)
│   ├── __init__.py                (19 lines)
│   ├── api_filter.py              (122 lines) - API filtering
│   ├── concurrent_analyzer.py     (256 lines) - Parallel analysis
│   └── metadata_collector.py      (251 lines) - Metadata collection
│
├── config/                        (Configuration files)
│   ├── method_configs.ini         - HTTP method defaults
│   ├── auth_headers.ini           - Authorization headers by type
│   ├── cors_headers.ini           - CORS configuration
│   └── response_templates.ini     - Response templates
│
├── profiles/                      (Generated - user's saved configs)
│   └── *.ini                      (Profile INI files)
│
└── reports/                       (Generated - audit results)
    ├── <api-name>_report_<timestamp>.csv
    ├── security_audit_report_<timestamp>.csv
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

### Security Check Package (`security_check/`)

**Purpose**: Security audit and compliance analysis

#### `api_filter.py` (122 lines)

APIFilter class with static methods:
- `filter_apis(apis, exclude_patterns)` - Remove APIs by suffix pattern
- `filter_methods(methods)` - Exclude methods like OPTIONS
- Configurable exclusion patterns (-DEV, -CI by default)

#### `concurrent_analyzer.py` (256 lines)

**AnalysisResult dataclass:**
```python
@dataclass
class AnalysisResult:
    api_id: str
    api_name: str
    methods_analyzed: int
    methods_protected: int
    methods_unprotected: int
    authorization_details: List[dict]
```

**ConcurrentAnalyzer class:**
- ThreadPoolExecutor-based parallel analysis
- Configurable pool size (1-10 workers)
- Methods:
  - `analyze_apis(apis, max_workers=5)` → List[AnalysisResult]
  - `analyze_single_api(api)` → AnalysisResult
  - Timeout handling per analysis

Performance: 4x faster than sequential analysis (116 resources analyzed in 60-75 seconds)

#### `metadata_collector.py` (251 lines)

**ResourceMetadata dataclass:**
```python
@dataclass
class ResourceMetadata:
    api_id: str
    resource_path: str
    http_method: str
    is_authorized: bool
    authorization_type: str
    specific_auth_type: str  # COGNITO_ADMIN, COGNITO_CUSTOMER, NO_AUTH
    authorizer_name: str
    created_date: Optional[str]
    last_modified: Optional[str]
```

**MetadataCollector class:**
- Collects authorization metadata from resources
- Caches authorizer information
- Methods:
  - `collect_resource_metadata(api, resource)` → ResourceMetadata
  - `get_authorizer_info(authorizer_id)` → dict
  - `to_dict()`, `from_dict()` - Serialization

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

### Endpoint Whitelist

Located in `config/whitelist.json`:

**Purpose**: Exclude endpoints that have authentication in the microservice backend (not in API Gateway)

**Format**:
```json
{
  "whitelist": {
    "MS-Auth-Server-Public-PROD": [
      "/oauth/token",
      "/oauth/validate",
      "/auth/login"
    ],
    "MS-Customer-Public-PROD": [
      "/customer/register",
      "/customer/*/profile"
    ]
  }
}
```

**Features**:
- **Exact match**: `/oauth/token` matches exactly that path
- **Wildcard patterns**: `/customer/*/profile` matches `/customer/123/profile`, `/customer/456/profile`, etc.
- **Auto-loading**: Whitelist is automatically loaded at the start of analysis
- **CSV filtering**: Whitelisted endpoints are NOT included in the CSV report

**Adding endpoints**:
1. Find the API name from the security check menu
2. Add the endpoint path to the whitelist under that API name
3. Run the security check again - whitelisted endpoints will be excluded

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

## Security Auditor Architecture

### Execution Model: Sequential APIs with Parallel Resources

The security auditor implements a hybrid parallelization strategy:

**API-Level Execution** (Sequential):
- APIs are analyzed **one at a time** in sequence
- This ensures clean, organized output
- Each API completes fully before the next begins
- Prevents output interleaving from concurrent API analysis

**Resource-Level Execution** (Parallel):
- Within each API, resources are analyzed in **parallel**
- Uses `ThreadPoolExecutor` with configurable pool size (1-10 workers)
- Multiple resources from the same API analyzed simultaneously
- Results processed as they complete via `as_completed()`

**Benefits:**
- ✓ Clean, readable output per API
- ✓ Fast analysis (resources parallelized)
- ✓ No output confusion from concurrent APIs
- ✓ Configurable performance tuning
- ✓ Single authorizer cache per API prevents race conditions

### Data Flow

```
┌─────────────────────────────────────────────┐
│ User selects API or scans ALL               │
└─────────┬───────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│ analyze_apis_sequentially()                 │
│ (SEQUENTIAL loop through APIs)              │
└─────────┬───────────────────────────────────┘
          │
          ├──────► API 1: check_api_security()
          │        ├─ build_authorizer_cache()
          │        └─ Resources (PARALLEL pool):
          │           ├─ Resource 1
          │           ├─ Resource 2  (concurrent)
          │           └─ Resource 3
          │
          ├──────► API 2: check_api_security()
          │        (same pattern)
          │
          └──────► API N: check_api_security()
                   (same pattern)
```

### Optimized Cache Building

The authorizer cache building process is highly optimized with configurable parallelization:

**Phase 1: Parallel Resource Scanning**
- Scans all resources in parallel
- Identifies which authorizers are used
- Collects authorizer IDs from resource methods
- Pool size = configured resource pool size (default: 5)
- ~70% faster than sequential scanning

**Phase 2: Parallel Authorizer Caching**
- Caches authorizer details in parallel
- Each authorizer fetched independently
- Results combined into single cache dictionary
- Pool size = resource pool size / 2 (auto-scaled, default: 2-3)
- ~80% faster than sequential caching

**Total Performance:**
- 116 resources, 4 authorizers: ~10-15 seconds (was 30-35 seconds)
- 60-70% faster cache building overall
- **Automatically scales** based on your resource pool configuration

**How It Works:**
- If you set resource pool = 8, cache uses: phase 1 (8 workers), phase 2 (4 workers)
- If you set resource pool = 2, cache uses: phase 1 (2 workers), phase 2 (1 worker)
- Lower values = lighter system load but slower cache building
- Higher values = faster cache building but higher resource usage

### Configuration

**Pool Size** (Resource Parallelization):
- Default: 5 workers
- Range: 1-10 workers
- Controls how many resources analyzed simultaneously within each API
- Higher = faster but more resource usage
- Lower = slower but lighter system load

**Example Usage:**
```
# Scan all APIs with 8 parallel resource workers
python3 apiGatewaySecurityCheck.py
# Select: 2 (Scan all APIs)
# Enter: 8 (pool size)
```

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

### apiGatewaySecurityCheck.py

**API Management:**
- `get_rest_apis()` - Lists all REST APIs
- `filter_apis_by_suffix()` - Applies exclusion filters

**Analysis:**
- `build_authorizer_cache()` - Caches authorizer metadata (prevents race conditions)
- `check_api_security()` - Analyzes single API with parallel resource processing
- `analyze_resource_methods()` - Analyzes resource methods
- `analyze_apis_sequentially()` - Sequential API analysis with parallel resource pools

**Reporting:**
- `create_consolidated_report_file()` - Creates CSV report with columns: api, method, path, is_authorized, authorization_type, specific_auth_type, authorizer_name, api_key
- `update_report_file()` - Real-time report updates with smart authorization detection
- `save_security_report()` - Saves JSON report
- `main()` - Main entry point

**Important Architecture Notes:**
- **APIs are analyzed SEQUENTIALLY** (one after another) to prevent output confusion
- **Resources within each API are parallelized** using configurable pool size
- This ensures clean, readable output while maintaining performance benefits

**CSV Report Details:**
- **is_authorized**: YES only for robust authorization (Cognito, Lambda, AWS IAM) - NOT API Key
- **api_key**: Separate column (YES/NO) to track API Key requirement independently
- **whitelisted**: YES for endpoints in config/whitelist.json (excluded from review as they have backend auth)
- This distinction allows granular security analysis - you can identify endpoints relying only on API Keys or those with backend authentication

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

### Run Security Audit

```bash
python3 apiGatewaySecurityCheck.py
# Automatically analyzes all APIs (except -DEV, -CI)
# Generates: reports/security_audit_report_<timestamp>.csv
# Optional: Adjust thread pool size for performance
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

**Security Auditor:**
- 116 resources, 4 authorizers:
  - Authorizer cache build: ~30-35 seconds
  - Concurrent analysis (5 workers): ~25-40 seconds
  - **Total: ~60-75 seconds** (4x faster than sequential)

**Optimization tips:**
- Use profiles for repeated deployments
- Increase worker pool size (up to 10) for security audits
- Run security audits off-peak to avoid API rate limits

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

## Summary

This comprehensive system provides:

1. **Rapid Endpoint Creation** - Automate HTTP method setup with multi-method support
2. **Configuration Reusability** - Save and load profiles for repeated deployments
3. **Security Auditing** - Concurrent analysis identifies unprotected endpoints
4. **Professional Logging** - Centralized error tracking with timestamped dumps
5. **Modular Architecture** - Clean separation of concerns across packages
6. **Type Safety** - Dataclasses and custom exceptions for robust code

**For questions or debugging**, check error dumps in `reports/` and review relevant function implementations referenced in this guide.
