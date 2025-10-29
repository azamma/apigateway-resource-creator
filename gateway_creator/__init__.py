"""
API Gateway Creator - Package

Módulos para automatizar la creación de recursos, métodos HTTP y
configurar integración con VPC Link y autenticación Cognito en AWS API Gateway.

Estructura del paquete:
    - config_manager: ConfigManager, ProfileConfigManager
    - ui_components: Componentes visuales (menús, cajas, etc.)
    - aws_manager: APIGatewayManager (orquestador de operaciones)

Ejemplo de uso:
    >>> from gateway_creator import ConfigManager, APIGatewayManager
    >>> config = ConfigManager()
    >>> manager = APIGatewayManager(api_id, conn_var, auth_id, config)
"""

from .config_manager import ConfigManager, ProfileConfigManager
from .aws_manager import APIGatewayManager
from .ui_components import (
    print_menu_header,
    print_menu_option,
    print_summary_item,
    print_box_message,
    clear_screen,
)

__version__ = "2.1"
__author__ = "API Gateway Creator Contributors"
__all__ = [
    "ConfigManager",
    "ProfileConfigManager",
    "APIGatewayManager",
    "print_menu_header",
    "print_menu_option",
    "print_summary_item",
    "print_box_message",
    "clear_screen",
]
