"""
Constants for API Gateway Resource Creator.

Este módulo centraliza todas las constantes del proyecto para evitar
magic numbers/strings y facilitar el mantenimiento.
"""

from enum import Enum

# ============================================================================
# AWS API Gateway Configuration
# ============================================================================

# Timeouts
CONFIG_TIMEOUT_MS: int = 29000
"""Default timeout in milliseconds for AWS API Gateway integrations."""

# Method Configuration
CONFIG_PASSTHROUGH_BEHAVIOR: str = "WHEN_NO_MATCH"
"""Default passthrough behavior for API Gateway integrations."""

CONFIG_INTEGRATION_TYPE: str = "HTTP_PROXY"
"""Default integration type for API Gateway methods."""

CONFIG_CONNECTION_TYPE: str = "VPC_LINK"
"""Default connection type for API Gateway integrations."""

CONFIG_RESPONSE_STATUS_CODE: str = "200"
"""Default response status code for API Gateway methods."""

CONFIG_RESPONSE_MODEL: str = "Empty"
"""Default response model for API Gateway methods."""

# ============================================================================
# UI Configuration
# ============================================================================

MENU_WIDTH: int = 70
"""Standard menu width for UI rendering."""

MENU_BORDER_WIDTH: int = 68
"""Menu border width for balanced formatting."""

MENU_SEPARATOR_CHAR: str = "─"
"""Character used for menu separators."""

SECTION_SEPARATOR_CHAR: str = "═"
"""Character used for section separators."""

SECTION_SEPARATOR_LENGTH: int = 70
"""Length of section separators."""

# ============================================================================
# File Paths and Extensions
# ============================================================================

DEFAULT_CONFIG_DIR: str = "config"
"""Default configuration directory name."""

DEFAULT_PROFILES_DIR: str = "profiles"
"""Default profiles directory name."""

PROFILE_EXTENSION: str = ".ini"
"""File extension for profile configuration files."""

ERROR_DUMP_PREFIX: str = "error_dump"
"""Prefix for error dump files."""

ERROR_DUMP_EXTENSION: str = ".log"
"""Extension for error dump files."""

SECURITY_REPORT_PREFIX: str = "security_report"
"""Prefix for security report files."""

SECURITY_REPORT_EXTENSION: str = ".json"
"""Extension for security report files."""

TIMESTAMP_FORMAT: str = "%Y%m%d_%H%M%S"
"""Format for timestamp in file names."""

DATETIME_FORMAT: str = "%Y-%m-%dT%H:%M:%S"
"""Format for datetime in logs."""

# ============================================================================
# Authorization Types
# ============================================================================


class AuthType(str, Enum):
    """Enumeration of supported authorization types."""

    COGNITO_ADMIN = "COGNITO_ADMIN"
    """Authorization using Cognito with admin claims."""

    COGNITO_CUSTOMER = "COGNITO_CUSTOMER"
    """Authorization using Cognito with customer claims."""

    NO_AUTH = "NO_AUTH"
    """No authorization required."""


# ============================================================================
# CORS Configuration
# ============================================================================

DEFAULT_CORS_TYPE: str = "DEFAULT"
"""Default CORS configuration type."""

# ============================================================================
# AWS CLI Strings
# ============================================================================

AWS_CLI_REGION_PARAM: str = "--region"
"""AWS CLI parameter for region specification."""

AWS_APIGATEWAY_SERVICE: str = "apigateway"
"""AWS service name for API Gateway."""

AWS_COGNITO_SERVICE: str = "cognito-idp"
"""AWS service name for Cognito IDP."""

# ============================================================================
# Error Messages
# ============================================================================

ERROR_INVALID_CHOICE: str = "Opción inválida. Inténtalo de nuevo."
"""Error message for invalid menu selection."""

ERROR_INVALID_INPUT: str = "Por favor, introduce un número."
"""Error message for invalid numeric input."""

ERROR_NO_PROFILES: str = "No se encontraron perfiles existentes"
"""Error message when no profiles are available."""

ERROR_NO_ITEMS: str = "No se encontraron elementos para"
"""Error message when no items found in menu."""

# ============================================================================
# Success Messages
# ============================================================================

SUCCESS_CONFIG_LOADED: str = "Archivos de configuración cargados exitosamente"
"""Success message for configuration loading."""

SUCCESS_PROFILE_SAVED: str = "Perfil guardado como: {}"
"""Success message template for profile saving."""

SUCCESS_PROFILE_LOADED: str = "Perfil {} cargado exitosamente"
"""Success message template for profile loading."""

SUCCESS_HEADER_ADDED: str = "Header '{}' agregado"
"""Success message template for header addition."""

SUCCESS_HEADER_REMOVED: str = "Header '{}' removido"
"""Success message template for header removal."""

# ============================================================================
# UI Labels and Prompts
# ============================================================================

PROMPT_SELECT_OPTION: str = "→ Selecciona una opción: "
"""Prompt text for menu selection."""

PROMPT_ENTER_VALUE: str = "→ Introduce un valor: "
"""Prompt text for value entry."""

LABEL_PROFILE_NAME: str = "Introduce el nombre del perfil (sin extensión): "
"""Label for profile name input."""

LABEL_HEADER_NAME: str = "Nombre del header: "
"""Label for header name input."""

LABEL_HEADER_VALUE: str = "Valor del header: "
"""Label for header value input."""

LABEL_BACKEND_PATH: str = (
    "Path COMPLETO del backend (ej: /discounts/b2c/campaigns/{id}): "
)
"""Label for backend path input."""

LABEL_CONNECTION_VARIABLE: str = (
    "Nombre de la variable de etapa para VPC Link (ej: vpcLinkId): "
)
"""Label for connection variable input."""

LABEL_BACKEND_HOST: str = (
    "Host del backend (ej: https://${stageVariables.urlBackend}): "
)
"""Label for backend host input."""

# ============================================================================
# Default Values and Constants
# ============================================================================

DEFAULT_MAX_RETRIES: int = 3
"""Default number of retries for failed operations."""

DEFAULT_CACHE_TTL_SECONDS: int = 300
"""Default cache time-to-live in seconds."""

MAX_PROFILE_NAME_LENGTH: int = 255
"""Maximum length for profile names."""

MAX_HEADER_NAME_LENGTH: int = 128
"""Maximum length for header names."""

MAX_HEADER_VALUE_LENGTH: int = 1024
"""Maximum length for header values."""

# ============================================================================
# Regular Expressions
# ============================================================================

REGEX_PARAMETER_PLACEHOLDER: str = r"\{(\w+)\}"
"""Regex pattern for finding {param} placeholders in paths."""

REGEX_STAGE_VARIABLE_REFERENCE: str = r"\$\{stageVariables\.(\w+)\}"
"""Regex pattern for stage variable references."""

REGEX_AWS_HEADER_PREFIX: str = r"integration\.request\.header\."
"""Regex pattern for AWS integration header prefix."""
