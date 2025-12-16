"""
API Gateway operations using boto3.

All AWS API Gateway interactions happen through this module.
"""
import re
import boto3
from botocore.exceptions import ClientError


# Initialize boto3 client
apigateway = boto3.client('apigateway')


def create_resource_hierarchy(api_id, segments, full_path):
    """
    Create resource hierarchy in API Gateway.

    Args:
        api_id: REST API ID
        segments: List of path segments
        full_path: Full resource path

    Returns:
        Dict with success status and resource_id or error
    """
    try:
        # Get root resource
        root_id = _get_root_resource_id(api_id)
        if not root_id:
            return {
                "success": False,
                "error": "Could not find root resource"
            }

        parent_id = root_id
        current_path = ""
        created_count = 0
        skipped_count = 0

        for segment in segments:
            current_path += "/" + segment

            # Check if resource exists
            existing_id = _find_resource_by_path(api_id, current_path)

            if existing_id:
                print(f"  Resource {current_path} already exists: {existing_id}")
                parent_id = existing_id
                skipped_count += 1
            else:
                # Create new resource
                new_id = _create_resource(api_id, parent_id, segment)
                if not new_id:
                    return {
                        "success": False,
                        "error": f"Failed to create resource: {segment}"
                    }
                print(f"  Created resource {current_path}: {new_id}")
                parent_id = new_id
                created_count += 1

        return {
            "success": True,
            "resource_id": parent_id,
            "created": created_count,
            "skipped": skipped_count
        }

    except ClientError as e:
        return {
            "success": False,
            "error": f"AWS Error: {e.response['Error']['Message']}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def create_http_methods(api_id, resource_id, http_methods, payload):
    """
    Create HTTP methods for a resource.

    Args:
        api_id: REST API ID
        resource_id: Resource ID
        http_methods: List of HTTP methods
        payload: Full payload with auth config

    Returns:
        Dict with success status
    """
    try:
        auth_config = payload.get("authentication", {})
        auth_method = auth_config.get("method", "AUTHORIZER")
        authorizer_id = auth_config.get("authorizer_id")

        # Determine authorization type
        if auth_method == "API_KEY":
            authorization_type = "NONE"
            api_key_required = True
            authorizer_id = None
        elif auth_config.get("auth_type") == "NO_AUTH":
            authorization_type = "NONE"
            api_key_required = False
            authorizer_id = None
        else:
            authorization_type = "COGNITO_USER_POOLS"
            api_key_required = False

        # Extract path parameters from path
        path = payload["endpoint"]["api_gateway_path"]
        request_parameters = _extract_path_parameters(path)

        for method in http_methods:
            try:
                params = {
                    'restApiId': api_id,
                    'resourceId': resource_id,
                    'httpMethod': method,
                    'authorizationType': authorization_type,
                    'apiKeyRequired': api_key_required
                }

                if authorizer_id and authorization_type == "COGNITO_USER_POOLS":
                    params['authorizerId'] = authorizer_id

                if request_parameters:
                    params['requestParameters'] = request_parameters

                apigateway.put_method(**params)
                print(f"    ✓ Created method: {method}")

            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ConflictException':
                    print(f"    ⚠ Method {method} already exists")
                else:
                    raise

        return {"success": True}

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def configure_integrations(api_id, resource_id, http_methods, payload):
    """
    Configure VPC Link integrations for HTTP methods.

    Args:
        api_id: REST API ID
        resource_id: Resource ID
        http_methods: List of HTTP methods
        payload: Full payload with integration config

    Returns:
        Dict with success status
    """
    try:
        integration_config = payload.get("integration", {})
        backend_host = integration_config.get("backend_host")
        backend_path = payload["endpoint"]["full_backend_path"]
        connection_variable = integration_config.get("connection_variable")
        timeout_ms = integration_config.get("timeout_ms", 29000)
        passthrough = integration_config.get("passthrough_behavior", "WHEN_NO_MATCH")
        integration_type = integration_config.get("integration_type", "HTTP_PROXY")

        # Build integration URI
        integration_uri = f"{backend_host}{backend_path}"

        # Build request parameters (headers + path params)
        request_parameters = _build_integration_request_parameters(payload)

        for method in http_methods:
            try:
                # Connection ID reference using stage variable
                connection_id = f"${{stageVariables.{connection_variable}}}"

                apigateway.put_integration(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod=method,
                    type=integration_type,
                    integrationHttpMethod=method,
                    uri=integration_uri,
                    connectionType='VPC_LINK',
                    connectionId=connection_id,
                    requestParameters=request_parameters,
                    passthroughBehavior=passthrough,
                    timeoutInMillis=timeout_ms
                )

                # Configure method response
                apigateway.put_method_response(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod=method,
                    statusCode='200',
                    responseModels={'application/json': 'Empty'}
                )

                # Configure integration response
                apigateway.put_integration_response(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod=method,
                    statusCode='200',
                    responseTemplates={'application/json': ''}
                )

                print(f"    ✓ Configured integration: {method}")

            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ConflictException':
                    print(f"    ⚠ Integration {method} already exists")
                else:
                    raise

        return {"success": True}

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def create_cors_method(api_id, resource_id, cors_config):
    """
    Create OPTIONS method for CORS.

    Args:
        api_id: REST API ID
        resource_id: Resource ID
        cors_config: CORS configuration

    Returns:
        Dict with success status
    """
    try:
        if not cors_config.get("enabled", True):
            return {"success": True, "skipped": True}

        cors_headers = cors_config.get("headers", {
            "Access-Control-Allow-Headers": "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token,X-Api-Version'",
            "Access-Control-Allow-Methods": "'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT'",
            "Access-Control-Allow-Origin": "'*'"
        })

        # Create OPTIONS method
        try:
            apigateway.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE',
                apiKeyRequired=False
            )
        except ClientError as e:
            if e.response['Error']['Code'] != 'ConflictException':
                raise

        # Create MOCK integration
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            type='MOCK',
            requestTemplates={
                'application/json': '{"statusCode": 200}'
            },
            passthroughBehavior='WHEN_NO_MATCH',
            timeoutInMillis=29000
        )

        # Build response parameters
        response_params = {}
        for header_name in cors_headers.keys():
            response_params[f"method.response.header.{header_name}"] = True

        # Create method response
        apigateway.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters=response_params
        )

        # Build integration response parameters
        integration_params = {}
        for header_name, header_value in cors_headers.items():
            integration_params[f"method.response.header.{header_name}"] = header_value

        # Create integration response
        apigateway.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters=integration_params
        )

        print(f"    ✓ CORS configured")
        return {"success": True}

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def verify_integrations(api_id, resource_id, methods):
    """
    Verify that all methods have integrations configured.

    Args:
        api_id: REST API ID
        resource_id: Resource ID
        methods: List of methods to verify

    Returns:
        Dict with success status
    """
    try:
        for method in methods:
            apigateway.get_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=method
            )
            print(f"    ✓ Verified: {method}")

        return {"success": True}

    except ClientError as e:
        return {
            "success": False,
            "error": f"Integration verification failed: {e.response['Error']['Message']}"
        }


# ===================================================================
# PRIVATE HELPER FUNCTIONS
# ===================================================================

def _get_root_resource_id(api_id):
    """Get the root resource ID (/) of an API."""
    try:
        response = apigateway.get_resources(restApiId=api_id)
        for resource in response.get('items', []):
            if resource.get('path') == '/':
                return resource['id']
        return None
    except ClientError:
        return None


def _find_resource_by_path(api_id, path):
    """Find a resource by its path."""
    try:
        response = apigateway.get_resources(restApiId=api_id)
        for resource in response.get('items', []):
            if resource.get('path') == path:
                return resource['id']
        return None
    except ClientError:
        return None


def _create_resource(api_id, parent_id, path_part):
    """Create a single resource."""
    try:
        response = apigateway.create_resource(
            restApiId=api_id,
            parentId=parent_id,
            pathPart=path_part
        )
        return response['id']
    except ClientError:
        return None


def _extract_path_parameters(path):
    """Extract path parameters from path like /users/{id}."""
    params = {}
    param_matches = re.findall(r'\{(\w+)\}', path)
    for param in param_matches:
        params[f"method.request.path.{param}"] = True
    return params


def _build_integration_request_parameters(payload):
    """Build integration request parameters (headers + path params)."""
    params = {}

    # Add authorization headers
    auth_headers = payload.get("headers", {}).get("auth_headers", {})
    for header_name, header_value in auth_headers.items():
        params[f"integration.request.header.{header_name}"] = header_value

    # Add custom headers
    custom_headers = payload.get("headers", {}).get("custom_headers", {})
    for header_name, header_value in custom_headers.items():
        params[f"integration.request.header.{header_name}"] = header_value

    # Add path parameters mapping
    path = payload["endpoint"]["api_gateway_path"]
    param_matches = re.findall(r'\{(\w+)\}', path)
    for param in param_matches:
        params[f"integration.request.path.{param}"] = f"method.request.path.{param}"

    return params
