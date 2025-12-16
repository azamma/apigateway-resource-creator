"""
Header Selector - Interactive header selection from Lambda options.

Allows users to select headers dynamically from Lambda configuration.
"""
from typing import Dict, List, Any, Optional

from common import get_logger, ANSIColors
from lambda_client import get_lambda_client

logger = get_logger(__name__)


def select_headers_for_auth_type(auth_type: str) -> Dict[str, str]:
    """
    Display available headers for an auth type and let user select/modify.

    Args:
        auth_type: Authentication type (COGNITO_ADMIN, COGNITO_CUSTOMER, etc.)

    Returns:
        Dictionary of selected headers
    """
    logger.section(f"HEADERS PARA {auth_type}")

    # Get options from Lambda
    lambda_client = get_lambda_client()
    options = lambda_client.get_header_options("auth_headers")

    if not options or "auth_headers" not in options:
        logger.warning("No se pudieron obtener opciones de headers desde Lambda")
        logger.info("Usando valores por defecto...")
        return _get_default_headers(auth_type)

    auth_options = options["auth_headers"].get(auth_type, {})

    if not auth_options:
        logger.warning(f"No hay opciones disponibles para {auth_type}")
        return _get_default_headers(auth_type)

    headers_config = auth_options.get("headers", {})

    logger.info(f"📋 Headers disponibles para {auth_type}:")
    logger.info(f"   {auth_options.get('description', '')}\n")

    # Display available headers
    selected_headers = {}

    print(f"{ANSIColors.CYAN}Headers configurados:{ANSIColors.RESET}")
    for i, (header_name, header_info) in enumerate(headers_config.items(), 1):
        is_required = header_info.get("required", False)
        default_value = header_info.get("default", "")
        description = header_info.get("description", "")

        required_label = f"{ANSIColors.RED}*{ANSIColors.RESET}" if is_required else " "

        print(f"  {ANSIColors.GREEN}{i}{ANSIColors.RESET}{required_label} {header_name}")
        print(f"     {ANSIColors.GRAY}→ {description}{ANSIColors.RESET}")
        print(f"     {ANSIColors.GRAY}Default: {default_value}{ANSIColors.RESET}\n")

        # Auto-select required headers
        if is_required:
            selected_headers[header_name] = default_value

    # Ask if user wants to add custom headers
    print(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} ¿Deseas agregar headers personalizados? (s/n): ", end="")
    add_custom = input().strip().lower()

    if add_custom == 's':
        custom_headers = _add_custom_headers()
        selected_headers.update(custom_headers)

    # Remove CognitoPool if exists (not a real header)
    selected_headers.pop('CognitoPool', None)

    logger.success(f"✓ {len(selected_headers)} headers seleccionados")

    return selected_headers


def _add_custom_headers() -> Dict[str, str]:
    """
    Interactive loop to add custom headers.

    Returns:
        Dictionary of custom headers
    """
    custom_headers = {}

    while True:
        print(f"\n{ANSIColors.CYAN}Agregar header personalizado:{ANSIColors.RESET}")
        header_name = input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} Nombre del header (Enter para terminar): ").strip()

        if not header_name:
            break

        header_value = input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} Valor del header: ").strip()

        if not header_value:
            logger.warning("Valor vacío, header ignorado")
            continue

        custom_headers[header_name] = header_value
        logger.success(f"✓ Header '{header_name}' agregado")

    return custom_headers


def _get_default_headers(auth_type: str) -> Dict[str, str]:
    """
    Fallback: Get default headers if Lambda is unavailable.

    Args:
        auth_type: Authentication type

    Returns:
        Default headers dictionary
    """
    defaults = {
        "COGNITO_ADMIN": {
            "Claim-Email": "context.authorizer.claims.email",
            "Claim-User-Id": "context.authorizer.claims.custom:admin_id",
            "KNOWN-TOKEN-KEY": "stageVariables.knownTokenKey",
            "X-Amzn-Request-Id": "context.requestId"
        },
        "COGNITO_CUSTOMER": {
            "Claim-Email": "context.authorizer.claims.email",
            "Claim-User-Id": "context.authorizer.claims.custom:customer_id",
            "KNOWN-TOKEN-KEY": "stageVariables.knownTokenKey",
            "X-Amzn-Request-Id": "context.requestId"
        },
        "NO_AUTH": {
            "KNOWN-TOKEN-KEY": "stageVariables.knownTokenKey",
            "X-Amzn-Request-Id": "context.requestId"
        },
        "API_KEY": {
            "X-Amzn-Request-Id": "context.requestId"
        }
    }

    return defaults.get(auth_type, {})


def display_integration_options() -> Optional[Dict[str, Any]]:
    """
    Display integration configuration options from Lambda.

    Returns:
        Selected integration config or None
    """
    logger.section("OPCIONES DE INTEGRACIÓN")

    lambda_client = get_lambda_client()
    options = lambda_client.get_header_options("integration_config")

    if not options or "integration_config" not in options:
        logger.warning("No se pudieron obtener opciones de integración")
        return None

    config_options = options["integration_config"]

    print(f"{ANSIColors.CYAN}Opciones disponibles:{ANSIColors.RESET}\n")

    for key, value_info in config_options.items():
        default = value_info.get("default")
        description = value_info.get("description", "")

        print(f"  {ANSIColors.GREEN}▸{ANSIColors.RESET} {key}")
        print(f"     {ANSIColors.GRAY}{description}{ANSIColors.RESET}")
        print(f"     {ANSIColors.GRAY}Default: {default}{ANSIColors.RESET}")

        if "options" in value_info:
            options_list = value_info["options"]
            print(f"     {ANSIColors.GRAY}Opciones: {', '.join(options_list)}{ANSIColors.RESET}")

        print()

    logger.info("ℹ️  Usando valores por defecto para la integración")

    return {
        "timeout_ms": 29000,
        "passthrough_behavior": "WHEN_NO_MATCH",
        "integration_type": "HTTP_PROXY",
        "connection_type": "VPC_LINK"
    }
