"""
Input validators for Lambda payload.

Validates JSON payload structure and required fields.
"""


def validate_payload(payload):
    """
    Validate the complete payload structure.

    Args:
        payload: JSON payload from client

    Returns:
        Dict with 'valid' (bool) and 'error' (str) if invalid
    """
    # Check operation
    if "operation" not in payload:
        return {"valid": False, "error": "Missing 'operation' field"}

    operation = payload["operation"]
    valid_operations = ["create_endpoint", "get_header_options"]
    if operation not in valid_operations:
        return {"valid": False, "error": f"Invalid operation: {operation}"}

    # Validate based on operation
    if operation == "create_endpoint":
        return _validate_create_endpoint(payload)
    elif operation == "get_header_options":
        return _validate_get_header_options(payload)

    return {"valid": True}


def _validate_create_endpoint(payload):
    """
    Validate create_endpoint payload.

    Args:
        payload: JSON payload

    Returns:
        Validation result
    """
    # Required sections
    required_sections = ["config", "endpoint", "integration"]

    for section in required_sections:
        if section not in payload:
            return {"valid": False, "error": f"Missing '{section}' section"}

    # Validate config section
    config = payload["config"]
    if "api_id" not in config:
        return {"valid": False, "error": "Missing 'config.api_id'"}

    # Validate endpoint section
    endpoint = payload["endpoint"]
    required_endpoint_fields = ["full_backend_path", "api_gateway_path", "http_methods"]

    for field in required_endpoint_fields:
        if field not in endpoint:
            return {"valid": False, "error": f"Missing 'endpoint.{field}'"}

    # Validate HTTP methods
    http_methods = endpoint["http_methods"]
    if not isinstance(http_methods, list) or len(http_methods) == 0:
        return {"valid": False, "error": "http_methods must be a non-empty list"}

    valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"]
    for method in http_methods:
        if method not in valid_methods:
            return {"valid": False, "error": f"Invalid HTTP method: {method}"}

    # Validate paths
    if not endpoint["full_backend_path"].startswith("/"):
        return {"valid": False, "error": "full_backend_path must start with /"}

    if not endpoint["api_gateway_path"].startswith("/"):
        return {"valid": False, "error": "api_gateway_path must start with /"}

    # Validate integration section
    integration = payload["integration"]
    required_integration_fields = ["connection_variable", "backend_host"]

    for field in required_integration_fields:
        if field not in integration:
            return {"valid": False, "error": f"Missing 'integration.{field}'"}

    # Validate authentication section (optional but if present, validate)
    if "authentication" in payload:
        auth = payload["authentication"]
        if "method" in auth:
            valid_auth_methods = ["AUTHORIZER", "API_KEY"]
            if auth["method"] not in valid_auth_methods:
                return {"valid": False, "error": f"Invalid auth method: {auth['method']}"}

            if auth["method"] == "AUTHORIZER" and "authorizer_id" not in auth:
                return {"valid": False, "error": "authorizer_id required for AUTHORIZER method"}

    return {"valid": True}


def _validate_get_header_options(payload):
    """
    Validate get_header_options payload.

    Args:
        payload: JSON payload

    Returns:
        Validation result
    """
    # Optional filter parameter
    if "filter" in payload:
        filter_param = payload["filter"]
        valid_filters = ["auth_headers", "cors_headers", "integration_config", "all"]

        if filter_param not in valid_filters:
            return {"valid": False, "error": f"Invalid filter: {filter_param}"}

    return {"valid": True}
