"""
Common - Módulos compartidos para API Gateway Creator y Security Check.

Contiene configuraciones, excepciones, logging y modelos de datos
utilizados por múltiples componentes.

Submódulos:
    - constants: Constantes globales (borders, mensajes, etc.)
    - exceptions: Excepciones personalizadas
    - logging_config: Sistema de logging con colores
    - models: Dataclasses para modelos de datos (APIConfig, EndpointConfig, etc.)
"""

from .constants import (
    MENU_BORDER_WIDTH,
    SECTION_SEPARATOR_CHAR,
    SECTION_SEPARATOR_LENGTH,
    CONFIG_TIMEOUT_MS,
    CONFIG_PASSTHROUGH_BEHAVIOR,
    CONFIG_INTEGRATION_TYPE,
    CONFIG_CONNECTION_TYPE,
    CONFIG_RESPONSE_STATUS_CODE,
    CONFIG_RESPONSE_MODEL,
    ERROR_INVALID_CHOICE,
    ERROR_INVALID_INPUT,
    ERROR_NO_PROFILES,
    SUCCESS_CONFIG_LOADED,
    AuthType,
)
from .exceptions import (
    APIGatewayException,
    AWSException,
    ConfigurationException,
    ProfileException,
    ValidationException,
    UserCancelledException,
    ResourceNotFoundException,
)
from .logging_config import (
    Logger,
    initialize_logger,
    get_logger,
    ANSIColors,
)
from .models import (
    APIConfig,
    EndpointConfig,
    MethodSpec,
    AWSResource,
)

__version__ = "2.1"
__all__ = [
    # constants
    "MENU_BORDER_WIDTH",
    "SECTION_SEPARATOR_CHAR",
    "SECTION_SEPARATOR_LENGTH",
    "CONFIG_TIMEOUT_MS",
    "CONFIG_PASSTHROUGH_BEHAVIOR",
    "CONFIG_INTEGRATION_TYPE",
    "CONFIG_CONNECTION_TYPE",
    "CONFIG_RESPONSE_STATUS_CODE",
    "CONFIG_RESPONSE_MODEL",
    "ERROR_INVALID_CHOICE",
    "ERROR_INVALID_INPUT",
    "ERROR_NO_PROFILES",
    "SUCCESS_CONFIG_LOADED",
    "AuthType",
    # exceptions
    "APIGatewayException",
    "AWSException",
    "ConfigurationException",
    "ProfileException",
    "ValidationException",
    "UserCancelledException",
    "ResourceNotFoundException",
    # logging
    "Logger",
    "initialize_logger",
    "get_logger",
    "ANSIColors",
    # models
    "APIConfig",
    "EndpointConfig",
    "MethodSpec",
    "AWSResource",
]
