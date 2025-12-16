"""
Endpoint Creator using Lambda.

Replaces write operations with Lambda invocations.
"""
from typing import Dict, Any, Optional

from common import get_logger, ANSIColors
from lambda_client import get_lambda_client
from header_selector import select_headers_for_auth_type, display_integration_options

logger = get_logger(__name__)


def create_endpoint_via_lambda(
    base_config: Dict[str, Any],
    endpoint_config: Dict[str, Any]
) -> bool:
    """
    Create endpoint via Lambda instead of direct AWS CLI.

    Args:
        base_config: Base configuration (API, auth, etc.)
        endpoint_config: Endpoint configuration (path, methods, headers)

    Returns:
        True if successful, False otherwise
    """
    logger.section("CREANDO ENDPOINT VÍA LAMBDA")

    # Prepare payload
    payload = _build_lambda_payload(base_config, endpoint_config)

    # Display summary
    _display_creation_summary(payload)

    # Confirm with user
    confirm = input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} ¿Proceder con la creación? (s/n): ").strip().lower()

    if confirm != 's':
        logger.warning("Creación cancelada por el usuario")
        return False

    # Invoke Lambda
    logger.info("\n📤 Enviando request a Lambda...")

    lambda_client = get_lambda_client()
    response = lambda_client.create_endpoint(payload)

    if not response:
        logger.error("❌ Error comunicándose con Lambda")
        return False

    # Display results
    return _display_lambda_response(response)


def _build_lambda_payload(
    base_config: Dict[str, Any],
    endpoint_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build Lambda payload from configurations.

    Args:
        base_config: Base configuration
        endpoint_config: Endpoint configuration

    Returns:
        Lambda payload dictionary
    """
    full_backend_path = endpoint_config["FULL_BACKEND_PATH"]
    http_methods = endpoint_config["HTTP_METHODS"]
    custom_headers = endpoint_config.get("CUSTOM_HEADERS", {})

    # Calculate API Gateway path (strip first segment)
    path_parts = full_backend_path.strip("/").split("/")
    if len(path_parts) > 1:
        api_gateway_path = "/" + "/".join(path_parts[1:])
    else:
        api_gateway_path = full_backend_path

    # Get auth headers based on auth type
    auth_type = base_config.get("AUTH_TYPE", "NO_AUTH")

    # Combine default auth headers with custom headers
    auth_headers = select_headers_for_auth_type(auth_type)
    all_headers = {**auth_headers, **custom_headers}

    # Get integration options
    integration_options = display_integration_options()

    if not integration_options:
        integration_options = {
            "timeout_ms": 29000,
            "passthrough_behavior": "WHEN_NO_MATCH",
            "integration_type": "HTTP_PROXY",
            "connection_type": "VPC_LINK"
        }

    # Build payload
    payload = {
        "config": {
            "api_id": base_config["API_ID"],
            "api_name": base_config.get("API_NAME", ""),
            "stage": base_config.get("STAGE", "ci")
        },
        "authentication": {
            "method": base_config.get("AUTH_METHOD", "AUTHORIZER"),
            "authorizer_id": base_config.get("AUTHORIZER_ID"),
            "auth_type": auth_type,
            "cognito_pool": base_config.get("COGNITO_POOL")
        },
        "endpoint": {
            "full_backend_path": full_backend_path,
            "api_gateway_path": api_gateway_path,
            "http_methods": http_methods
        },
        "integration": {
            "connection_variable": base_config["CONNECTION_VARIABLE"],
            "backend_host": base_config["BACKEND_HOST"],
            **integration_options
        },
        "headers": {
            "auth_headers": auth_headers,
            "custom_headers": custom_headers
        },
        "cors": {
            "enabled": True,
            "type": base_config.get("CORS_TYPE", "DEFAULT"),
            "headers": {
                "Access-Control-Allow-Headers": "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token,X-Api-Version'",
                "Access-Control-Allow-Methods": "'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT'",
                "Access-Control-Allow-Origin": "'*'"
            }
        }
    }

    return payload


def _display_creation_summary(payload: Dict[str, Any]) -> None:
    """
    Display summary of what will be created.

    Args:
        payload: Lambda payload
    """
    logger.section("RESUMEN DE CREACIÓN")

    config = payload["config"]
    endpoint = payload["endpoint"]
    auth = payload["authentication"]
    integration = payload["integration"]

    print(f"\n{ANSIColors.CYAN}🌐 API Gateway:{ANSIColors.RESET}")
    print(f"  {ANSIColors.GRAY}API ID:{ANSIColors.RESET} {config['api_id']}")
    print(f"  {ANSIColors.GRAY}Stage:{ANSIColors.RESET} {config['stage']}")

    print(f"\n{ANSIColors.CYAN}📍 Endpoint:{ANSIColors.RESET}")
    print(f"  {ANSIColors.GRAY}Path Backend:{ANSIColors.RESET} {endpoint['full_backend_path']}")
    print(f"  {ANSIColors.GRAY}Path API GW:{ANSIColors.RESET} {endpoint['api_gateway_path']}")
    print(f"  {ANSIColors.GRAY}Métodos:{ANSIColors.RESET} {', '.join(endpoint['http_methods'])}")

    print(f"\n{ANSIColors.CYAN}🔐 Autenticación:{ANSIColors.RESET}")
    print(f"  {ANSIColors.GRAY}Método:{ANSIColors.RESET} {auth['method']}")
    print(f"  {ANSIColors.GRAY}Tipo:{ANSIColors.RESET} {auth['auth_type']}")

    if auth.get('authorizer_id'):
        print(f"  {ANSIColors.GRAY}Authorizer ID:{ANSIColors.RESET} {auth['authorizer_id']}")

    print(f"\n{ANSIColors.CYAN}🔗 Integración:{ANSIColors.RESET}")
    print(f"  {ANSIColors.GRAY}Backend Host:{ANSIColors.RESET} {integration['backend_host']}")
    print(f"  {ANSIColors.GRAY}VPC Link Variable:{ANSIColors.RESET} {integration['connection_variable']}")
    print(f"  {ANSIColors.GRAY}Timeout:{ANSIColors.RESET} {integration['timeout_ms']}ms")

    headers_count = len(payload["headers"]["auth_headers"]) + len(payload["headers"]["custom_headers"])
    print(f"\n{ANSIColors.CYAN}📋 Headers:{ANSIColors.RESET} {headers_count} configurados")


def _display_lambda_response(response: Dict[str, Any]) -> bool:
    """
    Display Lambda response with steps progress.

    Args:
        response: Lambda response

    Returns:
        True if successful, False otherwise
    """
    success = response.get("success", False)

    if not success:
        logger.error(f"\n❌ ERROR: {response.get('error', 'Unknown error')}")
        logger.error(f"Error Code: {response.get('error_code', 'UNKNOWN')}")

        if "failed_step" in response:
            logger.error(f"Failed at step: {response['failed_step']}")

        # Display completed steps
        steps = response.get("steps", [])
        if steps:
            logger.info("\nSteps completados antes del error:")
            _display_steps(steps)

        return False

    # Success
    logger.section("✅ ENDPOINT CREADO EXITOSAMENTE")

    resource_id = response.get("resource_id", "N/A")
    logger.success(f"Resource ID: {resource_id}")

    # Display steps
    steps = response.get("steps", [])
    if steps:
        logger.info("\n📊 Pasos ejecutados:")
        _display_steps(steps)

    # Display warnings
    warnings = response.get("warnings", [])
    if warnings:
        logger.warning("\n⚠️  Advertencias:")
        for warning in warnings:
            logger.warning(f"  • {warning}")

    logger.success(f"\n{response.get('message', 'Operación completada')}")

    return True


def _display_steps(steps: list) -> None:
    """
    Display execution steps with status.

    Args:
        steps: List of step dictionaries
    """
    for step in steps:
        name = step.get("name", "unknown")
        status = step.get("status", "unknown")

        if status == "ok":
            icon = f"{ANSIColors.GREEN}✓{ANSIColors.RESET}"
        elif status == "failed":
            icon = f"{ANSIColors.RED}✗{ANSIColors.RESET}"
        else:
            icon = f"{ANSIColors.YELLOW}○{ANSIColors.RESET}"

        # Format step name
        step_display = name.replace("_", " ").title()

        # Additional info
        info = []
        if "count" in step:
            info.append(f"count={step['count']}")
        if "created" in step:
            info.append(f"created={step['created']}")
        if "skipped" in step:
            info.append(f"skipped={step['skipped']}")

        info_str = f" ({', '.join(info)})" if info else ""

        print(f"  {icon} {step_display}{info_str}")
