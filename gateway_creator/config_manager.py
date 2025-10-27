"""
Configuration Manager - Gestión de configuraciones para API Gateway Creator.

Módulos para cargar y gestionar configuraciones de métodos HTTP,
headers de autorización, CORS y templates de respuesta.
"""

import configparser
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from common import SUCCESS_CONFIG_LOADED, get_logger

logger = get_logger(__name__)


class ConfigManager:
    """
    Gestor de configuración que carga archivos INI de la carpeta 'config/'.

    Carga y proporciona acceso a configuraciones de:
    - Métodos HTTP
    - Headers de autorización
    - Headers CORS
    - Templates de respuesta
    """

    def __init__(self, config_dir: str = "config") -> None:
        """
        Inicializa el gestor de configuración.

        Args:
            config_dir: Ruta relativa de la carpeta de configuración
                       (default: "config").

        Raises:
            ConfigurationException: Si no se pueden cargar los archivos.

        Example:
            >>> manager = ConfigManager()
            >>> auth_headers = manager.get_auth_headers('COGNITO_ADMIN')
        """
        self.config_dir = Path(__file__).parent.parent / config_dir
        self.method_configs = configparser.ConfigParser()
        self.auth_headers = configparser.ConfigParser()
        self.cors_headers = configparser.ConfigParser()
        self.response_templates = configparser.ConfigParser()

        self._load_configs()

    def _load_configs(self) -> None:
        """
        Carga todos los archivos INI de configuración.

        Raises:
            SystemExit: Si hay error cargando las configuraciones.
        """
        try:
            self.method_configs.read(
                self.config_dir / "method_configs.ini"
            )
            self.auth_headers.read(self.config_dir / "auth_headers.ini")
            self.cors_headers.read(self.config_dir / "cors_headers.ini")
            self.response_templates.read(
                self.config_dir / "response_templates.ini"
            )
            logger.debug(SUCCESS_CONFIG_LOADED)
        except Exception as e:
            error_msg = (
                f"Error cargando configuraciones desde {self.config_dir}"
            )
            logger.dump_error(error_msg, e)
            logger.error(f"{error_msg}: {e}")
            sys.exit(1)

    def get_method_config(self, http_method: str) -> Dict[str, Any]:
        """
        Obtiene la configuración para un método HTTP específico.

        Args:
            http_method: Método HTTP (GET, POST, etc.).

        Returns:
            Diccionario con la configuración del método.

        Example:
            >>> config = manager.get_method_config('GET')
            >>> config['timeout_ms']
            '29000'
        """
        return dict(self.method_configs.get('DEFAULT', {}))

    def get_auth_headers(self, auth_type: str) -> Dict[str, str]:
        """
        Obtiene los headers de autorización según el tipo.

        Args:
            auth_type: Tipo de autorización (COGNITO_ADMIN, COGNITO_CUSTOMER, etc.).

        Returns:
            Diccionario con los headers de autorización.
            Si el tipo no existe, retorna headers de NO_AUTH.

        Example:
            >>> headers = manager.get_auth_headers('COGNITO_ADMIN')
        """
        if auth_type not in self.auth_headers:
            return dict(self.auth_headers.get('NO_AUTH', {}))
        return dict(self.auth_headers[auth_type])

    def get_cors_headers(self, cors_type: str = "DEFAULT") -> Dict[str, str]:
        """
        Obtiene los headers CORS.

        Args:
            cors_type: Tipo de configuración CORS (default: "DEFAULT").

        Returns:
            Diccionario con los headers CORS.

        Example:
            >>> cors = manager.get_cors_headers()
        """
        return dict(self.cors_headers.get(cors_type, {}))

    def get_response_template(
        self,
        template_type: str = "DEFAULT"
    ) -> Dict[str, str]:
        """
        Obtiene los templates de respuesta.

        Args:
            template_type: Tipo de template (default: "DEFAULT").

        Returns:
            Diccionario con los templates de respuesta.

        Example:
            >>> templates = manager.get_response_template()
        """
        return dict(self.response_templates.get(template_type, {}))


class ProfileConfigManager:
    """
    Gestor de configuración que carga desde un perfil INI.

    Diferencia de ConfigManager: carga configuración desde un archivo
    de perfil específico en lugar de la carpeta 'config/'.
    """

    def __init__(self, profile_config: configparser.ConfigParser) -> None:
        """
        Inicializa con una configuración de perfil cargada.

        Args:
            profile_config: ConfigParser con la configuración del perfil.

        Example:
            >>> config = configparser.ConfigParser()
            >>> config.read('profiles/dev-api.ini')
            >>> manager = ProfileConfigManager(config)
        """
        self.profile_config = profile_config
        self.method_configs = configparser.ConfigParser()
        self.auth_headers = configparser.ConfigParser()
        self.cors_headers = configparser.ConfigParser()

        self._load_from_profile()

    def _load_from_profile(self) -> None:
        """
        Carga configuraciones desde el perfil INI.

        Procesa secciones como METHOD_CONFIG, AUTH_HEADERS_*, CORS_HEADERS_*.
        """
        try:
            # Cargar configuración de métodos si existe
            if 'METHOD_CONFIG' in self.profile_config:
                self.method_configs['DEFAULT'] = (
                    self.profile_config['METHOD_CONFIG']
                )
            else:
                # Valores por defecto
                self.method_configs['DEFAULT'] = {
                    'timeout_ms': '29000',
                    'passthrough_behavior': 'WHEN_NO_MATCH',
                    'integration_type': 'HTTP_PROXY',
                    'connection_type': 'VPC_LINK'
                }

            # Cargar headers de autorización
            for section in self.profile_config.sections():
                if section.startswith('AUTH_HEADERS_'):
                    auth_type = section.replace('AUTH_HEADERS_', '')
                    self.auth_headers[auth_type] = (
                        self.profile_config[section]
                    )

            # Cargar headers CORS
            for section in self.profile_config.sections():
                if section.startswith('CORS_HEADERS_'):
                    cors_type = section.replace('CORS_HEADERS_', '')
                    self.cors_headers[cors_type] = (
                        self.profile_config[section]
                    )

            logger.debug("Configuración cargada desde perfil")
        except Exception as e:
            error_msg = "Error cargando configuración desde perfil"
            logger.dump_error(error_msg, e)
            logger.error(f"{error_msg}: {e}")

    def get_method_config(self, http_method: str) -> Dict[str, Any]:
        """
        Obtiene la configuración para un método HTTP específico.

        Args:
            http_method: Método HTTP (GET, POST, etc.).

        Returns:
            Diccionario con la configuración del método.
        """
        return dict(self.method_configs.get('DEFAULT', {}))

    def get_auth_headers(self, auth_type: str) -> Dict[str, str]:
        """
        Obtiene los headers de autorización según el tipo.

        Args:
            auth_type: Tipo de autorización (COGNITO_ADMIN, etc.).

        Returns:
            Diccionario con los headers de autorización.
        """
        if auth_type not in self.auth_headers:
            return dict(self.auth_headers.get('NO_AUTH', {}))
        return dict(self.auth_headers[auth_type])

    def get_cors_headers(self, cors_type: str = "DEFAULT") -> Dict[str, str]:
        """
        Obtiene los headers CORS.

        Args:
            cors_type: Tipo de configuración CORS (default: "DEFAULT").

        Returns:
            Diccionario con los headers CORS.
        """
        return dict(self.cors_headers.get(cors_type, {}))
