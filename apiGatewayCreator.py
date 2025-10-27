#!/usr/bin/env python3
"""
API Gateway Resource Creator - Automatiza creación de endpoints HTTP en AWS.

Este módulo proporciona herramientas para crear recursos, métodos HTTP y
configurar integración con VPC Link y autenticación Cognito en AWS API Gateway.
"""

import configparser
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Importar módulos de soporte refactorizados
from common import (
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
    # exceptions
    APIGatewayException,
    AWSException,
    ConfigurationException,
    ProfileException,
    ValidationException,
    UserCancelledException,
    ResourceNotFoundException,
    # logging
    Logger,
    initialize_logger,
    get_logger,
    ANSIColors,
    # models
    APIConfig,
    EndpointConfig,
    MethodSpec,
    AWSResource,
)

# Inicializar logger global
# Los errores se guardan en la carpeta reports/
reports_dir = Path(__file__).parent / "reports"
reports_dir.mkdir(exist_ok=True)
logger = initialize_logger(
    use_colors=True,
    error_dump_dir=reports_dir
)

def print_menu_header(title: str) -> None:
    """
    Print a styled menu header with borders.

    Args:
        title: The menu title to display.
    """
    from logging_config import ANSIColors
    color = ANSIColors.CYAN
    reset = ANSIColors.RESET
    print(
        f"\n{color}┌{'─' * MENU_BORDER_WIDTH}┐{reset}"
    )
    print(f"{color}│ {title:<{MENU_BORDER_WIDTH - 1}}│{reset}")
    print(f"{color}└{'─' * MENU_BORDER_WIDTH}┘{reset}")


def print_menu_option(number: int, text: str, emoji: str = "▸") -> None:
    """
    Print a styled menu option.

    Args:
        number: Option number (1-based).
        text: Option text to display.
        emoji: Emoji prefix (default: "▸").
    """
    from logging_config import ANSIColors
    color = ANSIColors.GREEN
    reset = ANSIColors.RESET
    print(f"  {color}{emoji} {number}{reset} - {text}")


def print_summary_item(
    label: str,
    value: str,
    highlight: bool = False,
) -> None:
    """
    Print a styled summary item.

    Args:
        label: The label for the item.
        value: The value to display.
        highlight: Whether to highlight the value (default: False).
    """
    from logging_config import ANSIColors
    info_color = ANSIColors.CYAN
    highlight_color = ANSIColors.YELLOW
    value_color = ANSIColors.GREEN
    debug_color = ANSIColors.GRAY
    reset = ANSIColors.RESET

    if highlight:
        print(
            f"  {info_color}▸{reset} "
            f"{highlight_color}{label}:{reset} "
            f"{value_color}{value}{reset}"
        )
    else:
        print(
            f"  {info_color}▸{reset} "
            f"{label}: {debug_color}{value}{reset}"
        )


def print_box_message(message: str, style: str = "info") -> None:
    """
    Print a message in a box.

    Args:
        message: The message to display.
        style: Box style - "info", "success", "warning", or "error".
    """
    from logging_config import ANSIColors

    color_map = {
        "info": ANSIColors.CYAN,
        "success": ANSIColors.GREEN,
        "warning": ANSIColors.YELLOW,
        "error": ANSIColors.RED,
    }
    color = color_map.get(style, ANSIColors.CYAN)
    reset = ANSIColors.RESET

    lines = message.split('\n')
    max_len = max(len(line) for line in lines) if lines else 0

    print(f"\n{color}╔{'═' * (max_len + 2)}╗{reset}")
    for line in lines:
        print(f"{color}║ {line:<{max_len}} ║{reset}")
    print(f"{color}╚{'═' * (max_len + 2)}╝{reset}")


def clear_screen() -> None:
    """Limpiar la pantalla de forma segura en Windows y Unix."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


# ============================================================== ========
# SECCIÓN 1: GESTOR DE CONFIGURACIÓN
# ===================================================================

class ConfigManager:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(__file__).parent / config_dir
        self.method_configs = configparser.ConfigParser()
        self.auth_headers = configparser.ConfigParser()
        self.cors_headers = configparser.ConfigParser()
        self.response_templates = configparser.ConfigParser()
        
        self._load_configs()
    
    def _load_configs(self) -> None:
        """
        Load all configuration INI files.

        Raises:
            ConfigurationException: If configuration files cannot be loaded.
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
        """Obtiene la configuración para un método HTTP específico"""
        return dict(self.method_configs['DEFAULT'])
    
    def get_auth_headers(self, auth_type: str) -> Dict[str, str]:
        """Obtiene los headers de autorización según el tipo"""
        if auth_type not in self.auth_headers:
            return dict(self.auth_headers['NO_AUTH'])
        return dict(self.auth_headers[auth_type])
    
    def get_cors_headers(self, cors_type: str = "DEFAULT") -> Dict[str, str]:
        """Obtiene los headers CORS"""
        return dict(self.cors_headers[cors_type])
    
    def get_response_template(self, template_type: str = "DEFAULT") -> Dict[str, str]:
        """Obtiene los templates de respuesta"""
        return dict(self.response_templates[template_type])


class ProfileConfigManager:
    """Gestor de configuración que carga desde un perfil INI (no desde la carpeta config)"""

    def __init__(self, profile_config: configparser.ConfigParser):
        """
        Inicializar con una configuración de perfil cargada.

        Args:
            profile_config: ConfigParser con la configuración del perfil.
        """
        self.profile_config = profile_config
        self.method_configs = configparser.ConfigParser()
        self.auth_headers = configparser.ConfigParser()
        self.cors_headers = configparser.ConfigParser()

        self._load_from_profile()

    def _load_from_profile(self) -> None:
        """Cargar configuraciones desde el perfil INI"""
        try:
            # Cargar configuración de métodos si existe
            if 'METHOD_CONFIG' in self.profile_config:
                self.method_configs['DEFAULT'] = self.profile_config['METHOD_CONFIG']
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
                    self.auth_headers[auth_type] = self.profile_config[section]

            # Cargar headers CORS
            for section in self.profile_config.sections():
                if section.startswith('CORS_HEADERS_'):
                    cors_type = section.replace('CORS_HEADERS_', '')
                    self.cors_headers[cors_type] = self.profile_config[section]

            logger.debug("Configuración cargada desde perfil")
        except Exception as e:
            error_msg = "Error cargando configuración desde perfil"
            logger.dump_error(error_msg, e)
            logger.error(f"{error_msg}: {e}")

    def get_method_config(self, http_method: str) -> Dict[str, Any]:
        """Obtiene la configuración para un método HTTP específico"""
        return dict(self.method_configs.get('DEFAULT', {}))

    def get_auth_headers(self, auth_type: str) -> Dict[str, str]:
        """Obtiene los headers de autorización según el tipo"""
        if auth_type not in self.auth_headers:
            return dict(self.auth_headers.get('NO_AUTH', {}))
        return dict(self.auth_headers[auth_type])

    def get_cors_headers(self, cors_type: str = "DEFAULT") -> Dict[str, str]:
        """Obtiene los headers CORS"""
        return dict(self.cors_headers.get(cors_type, {}))

# ===================================================================
# SECCIÓN 2: LÓGICA INTERACTIVA PARA SELECCIÓN DE RECURSOS
# ===================================================================

def run_aws_command(command: str) -> Optional[Dict[str, Any]]:
    """Ejecuta un comando de AWS y retorna el resultado en JSON."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            error_msg = f"Error ejecutando comando AWS: {command}"
            logger.dump_error(f"{error_msg}\nSTDERR: {result.stderr}\nSTDOUT: {result.stdout}")
            logger.error(f"Error al ejecutar comando:\n{result.stderr}")
            return None
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError as e:
        error_msg = f"Error parseando JSON del comando: {command}"
        logger.dump_error(error_msg, e)
        logger.error(f"Error parseando JSON: {e}")
        return None
    except Exception as e:
        error_msg = f"Excepción inesperada ejecutando comando: {command}"
        logger.dump_error(error_msg, e)
        logger.error(f"Excepción inesperada: {e}")
        return None

def select_from_menu(prompt: str, items: List[Any], name_key: str = 'name', return_key: str = 'id') -> Optional[Any]:
    """
    Muestra un menú de opciones y retorna el valor de la clave especificada (o el objeto completo).
    Si return_key es None, retorna el objeto entero.
    """
    if not items:
        logger.warning(f"No se encontraron elementos para '{prompt}'")
        return None

    clear_screen()
    print_menu_header(prompt)
    for i, item in enumerate(items):
        display_name = item.get(name_key, str(item)) if isinstance(item, dict) else str(item)
        print_menu_option(i + 1, display_name)

    while True:
        try:
            choice = int(input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} Selecciona una opción: "))
            if 1 <= choice <= len(items):
                selected_item = items[choice - 1]
                selected_display = selected_item.get(name_key, str(selected_item)) if isinstance(selected_item, dict) else str(selected_item)
                logger.success(f"Seleccionado: {selected_display}")
                return selected_item if not return_key else selected_item.get(return_key)
            else:
                logger.error("Opción inválida. Inténtalo de nuevo.")
        except ValueError:
            logger.error("Por favor, introduce un número.")

def select_api_grouped() -> Optional[str]:
    """Muestra un menú de APIs agrupadas por nombre base."""
    logger.info("Obteniendo listado de APIs...")
    apis_data = run_aws_command("aws apigateway get-rest-apis")
    if not apis_data or 'items' not in apis_data: return None

    groups = {}

    for api in apis_data['items']:
        name = api.get('name', '')
        if not name: continue

        parts = name.rsplit('-', 1)
        if len(parts) == 2 and parts[1].upper() in ['CI', 'DEV', 'PROD']:
            env = parts[1].upper()
            base_name = parts[0]
        else:
            base_name = name

        if base_name not in groups: groups[base_name] = []
        groups[base_name].append(api)

    sorted_group_names = sorted(groups.keys())
    clear_screen()
    print_menu_header("Selecciona el grupo de API")
    for i, name in enumerate(sorted_group_names):
        print_menu_option(i + 1, name, emoji="📦")

    selected_group_name = None
    while True:
        try:
            choice = int(input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} Selecciona un grupo: "))
            if 1 <= choice <= len(sorted_group_names):
                selected_group_name = sorted_group_names[choice - 1]
                logger.success(f"Grupo seleccionado: {selected_group_name}")
                break
            else:
                logger.error("Opción inválida. Inténtalo de nuevo.")
        except ValueError:
            logger.error("Por favor, introduce un número.")

    apis_in_group = sorted(groups[selected_group_name], key=lambda x: x.get('name', ''))

    if len(apis_in_group) == 1:
        logger.success(f"Grupo con un solo miembro, seleccionando automáticamente '{apis_in_group[0]['name']}'")
        return apis_in_group[0]['id']

    return select_from_menu("🌐 Selecciona la API específica del entorno", apis_in_group, return_key='id')

def select_http_methods() -> List[str]:
    """Permite seleccionar múltiples métodos HTTP"""
    available_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
    method_emojis = {'GET': '📥', 'POST': '📤', 'PUT': '✏️', 'DELETE': '🗑️', 'PATCH': '🔧'}

    clear_screen()
    print_menu_header("Selecciona los métodos HTTP a crear (separados por comas)")
    for i, method in enumerate(available_methods):
        emoji = method_emojis.get(method, '▸')
        print_menu_option(i + 1, method, emoji=emoji)

    while True:
        try:
            choices = input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} Ingresa los números (ej: 1,2,3): ")
            indices = [int(x.strip()) - 1 for x in choices.split(',')]

            if all(0 <= idx < len(available_methods) for idx in indices):
                selected_methods = [available_methods[idx] for idx in indices]
                logger.success(f"Métodos seleccionados: {', '.join(selected_methods)}")
                return selected_methods
            else:
                logger.error("Algunas opciones son inválidas. Inténtalo de nuevo.")
        except ValueError:
            logger.error("Por favor, introduce números separados por comas.")

def select_auth_type() -> str:
    """Selecciona el tipo de autorización"""
    auth_types = ['COGNITO_ADMIN', 'COGNITO_CUSTOMER', 'NO_AUTH']
    descriptions = {
        'COGNITO_ADMIN': 'Para el admin',
        'COGNITO_CUSTOMER': 'Para la app o la web',
        'NO_AUTH': 'Sin autorización (APIs públicas)'
    }
    auth_emojis = {
        'COGNITO_ADMIN': '👤',
        'COGNITO_CUSTOMER': '👥',
        'NO_AUTH': '🔓'
    }

    clear_screen()
    print_menu_header("Selecciona el tipo de autorización")
    for i, auth_type in enumerate(auth_types):
        emoji = auth_emojis.get(auth_type, '▸')
        text = f"{auth_type}: {ANSIColors.GRAY}{descriptions[auth_type]}{ANSIColors.RESET}"
        print_menu_option(i + 1, text, emoji=emoji)

    while True:
        try:
            choice = int(input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} Selecciona el tipo de autorización: "))
            if 1 <= choice <= len(auth_types):
                selected = auth_types[choice - 1]
                logger.success(f"Tipo de autorización: {selected}")
                return selected
            else:
                logger.error("Opción inválida. Inténtalo de nuevo.")
        except ValueError:
            logger.error("Por favor, introduce un número.")

def select_cors_type() -> str:
    """Selecciona el tipo de CORS"""
    return "DEFAULT"  # Por ahora solo DEFAULT, pero es extensible

def edit_headers_interactive(headers: Dict[str, str], title: str) -> Dict[str, str]:
    """
    Permite editar un diccionario de headers de forma interactiva.

    Args:
        headers: Diccionario de headers actuales
        title: Título de la sección

    Returns:
        Diccionario editado de headers
    """
    edited_headers = dict(headers)

    while True:
        clear_screen()
        logger.section(f"EDITAR {title}")

        # Mostrar headers actuales
        if edited_headers:
            print(f"\n{ANSIColors.CYAN}Headers actuales:{ANSIColors.RESET}")
            for i, (key, value) in enumerate(edited_headers.items(), 1):
                print(f"  {i}. {ANSIColors.GREEN}{key}{ANSIColors.RESET} = {ANSIColors.GRAY}{value}{ANSIColors.RESET}")
        else:
            print(f"\n{ANSIColors.YELLOW}No hay headers agregados aún.{ANSIColors.RESET}")

        print(f"\n{ANSIColors.CYAN}¿Qué deseas hacer?{ANSIColors.RESET}")
        print(f"  {ANSIColors.GREEN}1{ANSIColors.RESET} - Agregar header")
        if edited_headers:
            print(f"  {ANSIColors.GREEN}2{ANSIColors.RESET} - Quitar header")
        print(f"  {ANSIColors.GREEN}3{ANSIColors.RESET} - Guardar y continuar")

        choice = input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} Selecciona (1-3): ").strip()

        if choice == '1':
            # Agregar header
            clear_screen()
            header_name = input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} Nombre del header: ").strip()
            if not header_name:
                logger.error("Nombre de header no válido")
                input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} Presiona Enter para continuar...")
                continue

            header_value = input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} Valor del header: ").strip()
            if not header_value:
                logger.error("Valor de header no válido")
                input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} Presiona Enter para continuar...")
                continue

            edited_headers[header_name] = header_value
            logger.success(f"Header '{header_name}' agregado")

        elif choice == '2' and edited_headers:
            # Quitar header
            clear_screen()
            print(f"{ANSIColors.CYAN}Selecciona el header a quitar:{ANSIColors.RESET}")
            header_keys = list(edited_headers.keys())
            for i, key in enumerate(header_keys, 1):
                print(f"  {i}. {key}")

            try:
                remove_choice = int(input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} Selecciona (1-{len(header_keys)}): ").strip())
                if 1 <= remove_choice <= len(header_keys):
                    removed_key = header_keys[remove_choice - 1]
                    del edited_headers[removed_key]
                    logger.success(f"Header '{removed_key}' removido")
                else:
                    logger.error("Opción inválida")
            except ValueError:
                logger.error("Opción inválida")

            input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} Presiona Enter para continuar...")

        elif choice == '3':
            # Guardar y continuar
            break
        else:
            logger.error("Opción inválida")
            input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} Presiona Enter para continuar...")

    return edited_headers


def edit_method_config_interactive(method_config: Dict[str, str], title: str) -> Dict[str, str]:
    """
    Permite editar la configuración de métodos de forma interactiva.

    Args:
        method_config: Diccionario de configuración de métodos
        title: Título de la sección

    Returns:
        Diccionario editado
    """
    edited_config = dict(method_config)

    while True:
        clear_screen()
        logger.section(f"EDITAR {title}")

        # Mostrar configuración actual
        print(f"\n{ANSIColors.CYAN}Configuración actual:{ANSIColors.RESET}")
        for i, (key, value) in enumerate(edited_config.items(), 1):
            print(f"  {i}. {ANSIColors.GREEN}{key}{ANSIColors.RESET} = {ANSIColors.GRAY}{value}{ANSIColors.RESET}")

        print(f"\n{ANSIColors.CYAN}¿Deseas modificar algo?{ANSIColors.RESET}")
        print(f"  {ANSIColors.GREEN}1{ANSIColors.RESET} - Modificar un valor")
        print(f"  {ANSIColors.GREEN}2{ANSIColors.RESET} - Guardar y continuar")

        choice = input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} Selecciona (1-2): ").strip()

        if choice == '1':
            # Modificar valor
            clear_screen()
            print(f"{ANSIColors.CYAN}Selecciona qué modificar:{ANSIColors.RESET}")
            config_keys = list(edited_config.keys())
            for i, key in enumerate(config_keys, 1):
                print(f"  {i}. {key} = {edited_config[key]}")

            try:
                modify_choice = int(input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} Selecciona (1-{len(config_keys)}): ").strip())
                if 1 <= modify_choice <= len(config_keys):
                    key_to_modify = config_keys[modify_choice - 1]
                    new_value = input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} Nuevo valor para '{key_to_modify}': ").strip()
                    if new_value:
                        edited_config[key_to_modify] = new_value
                        logger.success(f"'{key_to_modify}' actualizado")
                    else:
                        logger.error("Valor no válido")
                else:
                    logger.error("Opción inválida")
            except ValueError:
                logger.error("Opción inválida")

            input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} Presiona Enter para continuar...")

        elif choice == '2':
            # Guardar y continuar
            break
        else:
            logger.error("Opción inválida")
            input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} Presiona Enter para continuar...")

    return edited_config

def list_configuration_profiles() -> List[str]:
    """Lista los archivos de configuración de perfiles disponibles"""
    profiles_dir = Path(__file__).parent / "profiles"
    if not profiles_dir.exists():
        return []
    
    profiles = []
    for file in profiles_dir.glob("*.ini"):
        profiles.append(file.stem)
    return profiles

def save_configuration_profile(config: Dict[str, Any], config_manager: ConfigManager) -> bool:
    """Guarda un perfil de configuración en un archivo INI, replicando headers de config"""
    profiles_dir = Path(__file__).parent / "profiles"
    profiles_dir.mkdir(exist_ok=True)

    clear_screen()
    logger.section("GUARDAR PERFIL DE CONFIGURACIÓN")

    auth_type = config['AUTH_TYPE']
    cors_type = config['CORS_TYPE']

    # Pregunta si desea modificar la configuración por defecto
    print(f"\n{ANSIColors.CYAN}¿Deseas modificar la configuración por defecto antes de guardar? (s/n):{ANSIColors.RESET}")
    edit_config = input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} ").lower()

    # Copiar configuración por defecto
    final_auth_headers = dict(config_manager.auth_headers[auth_type]) if auth_type in config_manager.auth_headers else {}
    final_cors_headers = dict(config_manager.cors_headers[cors_type]) if cors_type in config_manager.cors_headers else {}
    final_method_config = dict(config_manager.method_configs['DEFAULT']) if 'DEFAULT' in config_manager.method_configs else {}

    # Si desea editar, entrar al editor interactivo
    if edit_config == 's':
        # Editar headers de autorización
        if final_auth_headers:
            clear_screen()
            logger.section(f"HEADERS DE AUTORIZACIÓN ({auth_type})")
            print(f"\n{ANSIColors.CYAN}Configuración actual:{ANSIColors.RESET}")
            for key, value in final_auth_headers.items():
                print(f"  {ANSIColors.GREEN}{key}{ANSIColors.RESET} = {ANSIColors.GRAY}{value}{ANSIColors.RESET}")
            print(f"\n{ANSIColors.CYAN}¿Deseas modificar los headers de autorización? (s/n):{ANSIColors.RESET}")
            if input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} ").lower() == 's':
                final_auth_headers = edit_headers_interactive(final_auth_headers, f"HEADERS DE AUTORIZACIÓN ({auth_type})")

        # Editar headers CORS
        if final_cors_headers:
            clear_screen()
            print(f"\n{ANSIColors.CYAN}¿Deseas modificar los headers CORS? (s/n):{ANSIColors.RESET}")
            if input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} ").lower() == 's':
                final_cors_headers = edit_headers_interactive(final_cors_headers, f"HEADERS CORS ({cors_type})")

        # Editar configuración de métodos
        if final_method_config:
            clear_screen()
            print(f"\n{ANSIColors.CYAN}¿Deseas modificar la configuración de métodos HTTP? (s/n):{ANSIColors.RESET}")
            if input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} ").lower() == 's':
                final_method_config = edit_method_config_interactive(final_method_config, "CONFIGURACIÓN DE MÉTODOS HTTP")

    # Pedir nombre del perfil
    clear_screen()
    logger.section("GUARDAR PERFIL")
    profile_name = input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} Introduce el nombre del perfil (sin extensión): ").strip()
    if not profile_name:
        logger.error("Nombre de perfil inválido")
        return False

    profile_file = profiles_dir / f"{profile_name}.ini"

    try:
        profile_config = configparser.ConfigParser()

        # Sección PROFILE con config base
        profile_config['PROFILE'] = {
            'api_id': config['API_ID'],
            'connection_variable': config['CONNECTION_VARIABLE'],
            'authorizer_id': config['AUTHORIZER_ID'],
            'cognito_pool': config['COGNITO_POOL'],
            'backend_host': config['BACKEND_HOST'],
            'auth_type': config['AUTH_TYPE'],
            'cors_type': config['CORS_TYPE']
        }

        # Guardar headers de autorización editados
        if final_auth_headers:
            profile_config[f'AUTH_HEADERS_{auth_type}'] = final_auth_headers

        # Guardar headers CORS editados
        if final_cors_headers:
            profile_config[f'CORS_HEADERS_{cors_type}'] = final_cors_headers

        # Guardar configuración de métodos editada
        if final_method_config:
            profile_config['METHOD_CONFIG'] = final_method_config

        with open(profile_file, 'w') as f:
            profile_config.write(f)

        clear_screen()
        logger.success(f"Perfil '{profile_name}' guardado exitosamente")
        logger.success(f"✓ Configuración base")
        if final_auth_headers:
            logger.success(f"✓ Headers de autorización ({auth_type})")
        if final_cors_headers:
            logger.success(f"✓ Headers CORS ({cors_type})")
        if final_method_config:
            logger.success(f"✓ Configuración de métodos HTTP")
        return True

    except Exception as e:
        error_msg = f"Error guardando perfil de configuración"
        logger.dump_error(error_msg, e)
        logger.error(f"{error_msg}: {e}")
        return False

def load_configuration_profile(profile_name: str) -> Optional[Dict[str, Any]]:
    """Carga un perfil de configuración desde archivo INI"""
    profiles_dir = Path(__file__).parent / "profiles"
    profile_file = profiles_dir / f"{profile_name}.ini"

    if not profile_file.exists():
        logger.error(f"Perfil {profile_name} no encontrado")
        return None

    try:
        profile_config = configparser.ConfigParser()
        profile_config.read(profile_file)

        if 'PROFILE' not in profile_config:
            logger.error(f"Archivo de perfil {profile_name} mal formateado")
            return None

        config = {
            'API_ID': profile_config['PROFILE']['api_id'],
            'CONNECTION_VARIABLE': profile_config['PROFILE']['connection_variable'],
            'AUTHORIZER_ID': profile_config['PROFILE']['authorizer_id'],
            'COGNITO_POOL': profile_config['PROFILE']['cognito_pool'],
            'BACKEND_HOST': profile_config['PROFILE']['backend_host'],
            'AUTH_TYPE': profile_config['PROFILE']['auth_type'],
            'CORS_TYPE': profile_config['PROFILE']['cors_type'],
            '_profile_config': profile_config  # Guardar referencia al ConfigParser
        }

        logger.success(f"Perfil {profile_name} cargado exitosamente")
        return config

    except Exception as e:
        error_msg = f"Error cargando perfil {profile_name}"
        logger.dump_error(error_msg, e)
        logger.error(f"{error_msg}: {e}")
        return None


def get_profile_config_manager(config: Dict[str, Any]) -> Optional[ProfileConfigManager]:
    """
    Obtiene un ProfileConfigManager desde la configuración cargada del perfil.

    Args:
        config: Diccionario de configuración que contiene _profile_config.

    Returns:
        ProfileConfigManager o None si no se puede crear.
    """
    if '_profile_config' not in config:
        logger.warning("Configuración del perfil no contiene _profile_config")
        return None

    try:
        profile_config_manager = ProfileConfigManager(config['_profile_config'])
        return profile_config_manager
    except Exception as e:
        logger.error(f"Error creando ProfileConfigManager: {e}")
        return None

def validate_configuration_profile(config: Dict[str, Any]) -> Dict[str, bool]:
    """Valida que los recursos de un perfil aún existan"""
    logger.info("Validando configuración cargada...")
    validation_results = {}

    # Validar API
    logger.debug("Verificando API...")
    api_data = run_aws_command(f"aws apigateway get-rest-api --rest-api-id {config['API_ID']}")
    validation_results['API'] = api_data is not None
    if validation_results['API']:
        logger.debug("  ✓ API encontrada")
    else:
        logger.debug("  ✗ API no encontrada")

    # Validar que la stage variable existe
    logger.debug("Verificando variable de stage...")
    stages_data = run_aws_command(f"aws apigateway get-stages --rest-api-id {config['API_ID']}")
    validation_results['CONFIG_CONNECTION_TYPE_VARIABLE'] = False
    if stages_data and 'item' in stages_data:
        for stage in stages_data['item']:
            stage_vars = stage.get('variables', {})
            if config['CONNECTION_VARIABLE'] in stage_vars:
                validation_results['CONFIG_CONNECTION_TYPE_VARIABLE'] = True
                break
    if validation_results['CONFIG_CONNECTION_TYPE_VARIABLE']:
        logger.debug("  ✓ Variable VPC Link encontrada")
    else:
        logger.debug("  ✗ Variable VPC Link no encontrada")

    # Validar Authorizer
    logger.debug("Verificando Authorizer...")
    authorizers = run_aws_command(f"aws apigateway get-authorizers --rest-api-id {config['API_ID']}")
    validation_results['AUTHORIZER'] = False
    if authorizers and 'items' in authorizers:
        validation_results['AUTHORIZER'] = any(auth['id'] == config['AUTHORIZER_ID'] for auth in authorizers['items'])
    if validation_results['AUTHORIZER']:
        logger.debug("  ✓ Authorizer encontrado")
    else:
        logger.debug("  ✗ Authorizer no encontrado")

    # Validar Cognito Pool
    logger.debug("Verificando Cognito Pool...")
    pools = run_aws_command("aws cognito-idp list-user-pools --max-results 60")
    validation_results['COGNITO_POOL'] = False
    if pools and 'UserPools' in pools:
        validation_results['COGNITO_POOL'] = any(pool['Name'] == config['COGNITO_POOL'] for pool in pools['UserPools'])
    if validation_results['COGNITO_POOL']:
        logger.debug("  ✓ Cognito Pool encontrado")
    else:
        logger.debug("  ✗ Cognito Pool no encontrado")

    return validation_results

def select_configuration_source() -> Optional[Dict[str, Any]]:
    """Permite elegir entre cargar perfil existente o crear nueva configuración"""
    profiles = list_configuration_profiles()

    if profiles:
        print_menu_header("¿Cómo deseas configurar la API?")
        print_menu_option(1, "Cargar perfil de configuración existente", emoji="📂")
        print_menu_option(2, "Crear nueva configuración", emoji="⚙️")

        while True:
            try:
                choice = int(input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} Selecciona una opción: "))
                if choice == 1:
                    return select_existing_profile(profiles)
                elif choice == 2:
                    return get_interactive_config()
                else:
                    logger.error("Opción inválida. Inténtalo de nuevo.")
            except ValueError:
                logger.error("Por favor, introduce un número.")
    else:
        logger.warning("No se encontraron perfiles existentes")
        logger.info("Procediendo con configuración manual...")
        return get_interactive_config()

def main_menu() -> Optional[str]:
    """Menú principal que permite elegir entre cargar perfil o crear nuevo perfil"""
    print_menu_header("MENÚ PRINCIPAL")
    print_menu_option(1, "Cargar perfil existente y crear recursos", emoji="📂")
    print_menu_option(2, "Crear nuevo perfil (sin crear recursos)", emoji="⚙️")

    while True:
        try:
            choice = int(input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} Selecciona una opción: "))
            if choice == 1:
                return "load_profile"
            elif choice == 2:
                return "create_profile"
            else:
                logger.error("Opción inválida. Inténtalo de nuevo.")
        except ValueError:
            logger.error("Por favor, introduce un número.")

def load_profile_workflow() -> Optional[Dict[str, Any]]:
    """Workflow para cargar un perfil existente y crear recursos"""
    profiles = list_configuration_profiles()

    if not profiles:
        logger.warning("No se encontraron perfiles existentes")
        return None

    return select_existing_profile(profiles)

def create_profile_workflow(config_manager: ConfigManager) -> bool:
    """Workflow para crear un nuevo perfil sin crear recursos"""
    logger.section("CREAR NUEVO PERFIL")

    config = get_interactive_config(config_manager)
    if not config:
        return False

    save_profile = input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} ¿Deseas guardar esta configuración como perfil? (s/n): ").lower()
    if save_profile == 's':
        if save_configuration_profile(config, config_manager):
            logger.success("Perfil guardado exitosamente. Puedes usarlo para crear recursos en el futuro.")
            return True

    return False

def select_existing_profile(profiles: List[str]) -> Optional[Dict[str, Any]]:
    """Permite seleccionar un perfil existente de la lista"""
    clear_screen()
    print_menu_header("📋 Perfiles de configuración disponibles")
    for i, profile in enumerate(profiles):
        print_menu_option(i + 1, profile, emoji="📄")

    while True:
        try:
            choice = int(input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} Selecciona un perfil: "))
            if 1 <= choice <= len(profiles):
                selected_profile = profiles[choice - 1]
                config = load_configuration_profile(selected_profile)

                if config:
                    return validate_and_confirm_profile(config, selected_profile)
                return None
            else:
                logger.error("Opción inválida. Inténtalo de nuevo.")
        except ValueError:
            logger.error("Por favor, introduce un número.")

def validate_and_confirm_profile(config: Dict[str, Any], profile_name: str) -> Optional[Dict[str, Any]]:
    """Valida un perfil cargado y permite al usuario confirmarlo o modificarlo"""
    # Validar recursos
    validation_results = validate_configuration_profile(config)

    # Mostrar resumen de validación
    print(f"\n{ANSIColors.CYAN}📊 Resultados de Validación para '{profile_name}':{ANSIColors.RESET}")
    for resource, is_valid in validation_results.items():
        if is_valid:
            print(f"  {ANSIColors.GREEN}✓{ANSIColors.RESET} {resource}")
        else:
            print(f"  {ANSIColors.RED}✗{ANSIColors.RESET} {resource}")

    # Si hay errores, avisar
    invalid_resources = [k for k, v in validation_results.items() if not v]
    if invalid_resources:
        print_box_message(f"Recursos inválidos: {', '.join(invalid_resources)}\nNecesitas reconfigurar estos elementos.", style="warning")

        retry = input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} ¿Deseas intentar reconfigurar manualmente? (s/n): ").lower()
        if retry == 's':
            return None
        else:
            return None

    # Mostrar resumen de la configuración
    logger.section(f"RESUMEN DEL PERFIL: {profile_name}")
    print_summary_item("API ID", config['API_ID'])
    print_summary_item("Variable de Conexión", config['CONNECTION_VARIABLE'])
    print_summary_item("ID de Authorizer", config['AUTHORIZER_ID'])
    print_summary_item("Cognito Pool", config['COGNITO_POOL'])
    print_summary_item("Host de Backend", config['BACKEND_HOST'], highlight=True)
    print_summary_item("Tipo de Autorización", config['AUTH_TYPE'])
    print_summary_item("Tipo de CORS", config['CORS_TYPE'])

    print_menu_header("¿Qué deseas hacer?")
    print_menu_option(1, "Continuar con esta configuración", emoji="✅")
    print_menu_option(2, "Seleccionar otro perfil", emoji="🔄")
    print_menu_option(3, "Crear nueva configuración manualmente", emoji="⚙️")

    while True:
        try:
            choice = int(input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} Selecciona una opción: "))
            if choice == 1:
                logger.success("Continuando con esta configuración")
                return config
            elif choice == 2:
                profiles = list_configuration_profiles()
                return select_existing_profile(profiles)
            elif choice == 3:
                return get_interactive_config()
            else:
                logger.error("Opción inválida. Inténtalo de nuevo.")
        except ValueError:
            logger.error("Por favor, introduce un número.")

def print_headers_summary(headers: Dict[str, str], title: str = "Headers Configurados"):
    """Muestra un resumen formateado de los headers"""
    print(f"\n{ANSIColors.CYAN}📋 {title}:{ANSIColors.RESET}")
    if not headers:
        print(f"  {ANSIColors.GRAY}(sin headers adicionales){ANSIColors.RESET}")
        return
    for i, (key, value) in enumerate(headers.items(), 1):
        print(f"  {ANSIColors.GREEN}▸{ANSIColors.RESET} {key}: {ANSIColors.GRAY}{value}{ANSIColors.RESET}")

def manage_headers(config_manager: ConfigManager, auth_type: str) -> Dict[str, str]:
    """Permite al usuario gestionar headers (agregar, quitar) para un endpoint"""
    # Obtener headers de autorización base según el tipo de autenticación
    base_headers = config_manager.get_auth_headers(auth_type).copy()

    # Remover la clave CognitoPool si existe (no es un header real)
    base_headers.pop('CognitoPool', None)

    custom_headers = {}

    while True:
        # Mostrar headers actuales
        all_headers = {**base_headers, **custom_headers}
        print_headers_summary(all_headers, "Headers Actuales")

        print_menu_header("Gestión de Headers")
        print_menu_option(1, "Agregar nuevo header", emoji="➕")
        print_menu_option(2, "Remover header", emoji="➖")
        print_menu_option(3, "Continuar con estos headers", emoji="✅")

        try:
            choice = int(input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} Selecciona una opción: "))

            if choice == 1:
                # Agregar nuevo header
                header_name = input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} Nombre del header: ").strip()
                if not header_name:
                    logger.error("El nombre del header no puede estar vacío")
                    continue

                header_value = input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} Valor del header: ").strip()
                if not header_value:
                    logger.error("El valor del header no puede estar vacío")
                    continue

                custom_headers[header_name] = header_value
                logger.success(f"Header '{header_name}' agregado")

            elif choice == 2:
                # Remover header
                if not all_headers:
                    logger.warning("No hay headers para remover")
                    continue

                print_menu_header("Selecciona el header a remover")
                items = list(all_headers.items())
                for i, (key, value) in enumerate(items):
                    print_menu_option(i + 1, f"{key}", emoji="🗑️")

                try:
                    remove_choice = int(input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} Selecciona el header a remover: "))
                    if 1 <= remove_choice <= len(items):
                        key_to_remove = items[remove_choice - 1][0]

                        # Solo permitir remover headers personalizados
                        if key_to_remove in custom_headers:
                            del custom_headers[key_to_remove]
                            logger.success(f"Header '{key_to_remove}' removido")
                        else:
                            logger.warning("No puedes remover headers de autorización base")
                    else:
                        logger.error("Opción inválida")
                except ValueError:
                    logger.error("Por favor, introduce un número válido")

            elif choice == 3:
                logger.success("Configuración de headers finalizada")
                return custom_headers

            else:
                logger.error("Opción inválida")

        except ValueError:
            logger.error("Por favor, introduce un número válido")

def get_endpoint_and_methods(reuse_methods: List[str] = None, config_manager: ConfigManager = None, auth_type: str = None) -> Optional[Dict[str, Any]]:
    """Solicita configuración del endpoint, métodos y headers para usar con configuración existente"""
    logger.section("CONFIGURACIÓN DEL ENDPOINT")

    # Si es el primer endpoint o el usuario quiere cambiar métodos
    if reuse_methods is None:
        http_methods = select_http_methods()
    else:
        logger.info(f"📋 Reutilizando métodos base: {', '.join(reuse_methods)}")
        change_methods = input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} ¿Deseas cambiar los métodos para este endpoint? (s/n): ").lower()
        if change_methods == 's':
            http_methods = select_http_methods()
        else:
            http_methods = reuse_methods

    print(f"\n{ANSIColors.CYAN}Por favor, introduce el siguiente valor:{ANSIColors.RESET}")
    full_backend_path = input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} Path COMPLETO del backend (ej: /discounts/b2c/campaigns/{{id}}): ")

    # Gestión de headers si se proporciona config_manager y auth_type
    custom_headers = {}
    if config_manager and auth_type:
        print()
        manage_headers_choice = input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} ¿Deseas gestionar headers para este endpoint? (s/n): ").lower()
        if manage_headers_choice == 's':
            custom_headers = manage_headers(config_manager, auth_type)

    return {
        "HTTP_METHODS": http_methods,
        "FULL_BACKEND_PATH": full_backend_path,
        "CUSTOM_HEADERS": custom_headers
    }

def get_interactive_config(config_manager: ConfigManager) -> Optional[Dict[str, Any]]:
    """Guía al usuario a través de menús para obtener la configuración completa."""
    api_id = select_api_grouped()
    if not api_id: return None

    authorizers_data = run_aws_command(f"aws apigateway get-authorizers --rest-api-id {api_id}")
    if not authorizers_data or 'items' not in authorizers_data: return None
    authorizer_id = select_from_menu("Selecciona el Authorizer:", authorizers_data['items'], return_key='id')
    if not authorizer_id: return None

    user_pools_data = run_aws_command("aws cognito-idp list-user-pools --max-results 60")
    if not user_pools_data or 'UserPools' not in user_pools_data: return None
    cognito_pool = select_from_menu("Selecciona el Cognito User Pool:", user_pools_data['UserPools'], name_key='Name', return_key='Name')
    if not cognito_pool: return None

    # Seleccionar Stage
    stages_data = run_aws_command(f"aws apigateway get-stages --rest-api-id {api_id}")
    if not stages_data or 'item' not in stages_data: return None

    selected_stage = select_from_menu("Selecciona la Etapa (Stage) de la API:", stages_data['item'], name_key='stageName', return_key=None)
    if not selected_stage: return None

    # Extraer variables de etapa
    stage_variables = selected_stage.get('variables', {})
    if not stage_variables:
        print(f"{ANSIColors.WARNING}⚠️  La etapa '{selected_stage['stageName']}' no tiene variables definidas.{ANSIColors.RESET}")
        print(f"\n{ANSIColors.CYAN}Por favor, introduce los siguientes valores:{ANSIColors.RESET}")
        connection_variable = input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} Nombre de la variable de etapa para VPC Link (ej: vpcLinkId): ").strip()
        if not connection_variable:
            logger.error("La variable de conexión es requerida")
            return None

        backend_host = input(f"{ANSIColors.YELLOW}→{ANSIColors.RESET} Host del backend (ej: https://${{stageVariables.urlBackend}}): ").strip()
        if not backend_host:
            logger.error("El host del backend es requerido")
            return None
    else:
        print(f"\n{ANSIColors.CYAN}📋 Variables de etapa disponibles:{ANSIColors.RESET}")
        for key, value in stage_variables.items():
            print(f"  {ANSIColors.GRAY}▸{ANSIColors.RESET} {key}: {value}")

        connection_variable = select_from_menu("Selecciona la Variable de Etapa para el VPC Link:", list(stage_variables.keys()), name_key=None, return_key=None)
        if not connection_variable: return None

        variable_name = select_from_menu("Selecciona la Variable de Etapa para el host del backend:", list(stage_variables.keys()), name_key=None, return_key=None)
        if not variable_name: return None
        backend_host = f"https://${{stageVariables.{variable_name}}}"

    # Selección de tipo de autorización
    auth_type = select_auth_type()

    # Selección de tipo de CORS
    cors_type = select_cors_type()

    config = {
        "API_ID": api_id,
        "CONNECTION_VARIABLE": connection_variable,
        "AUTHORIZER_ID": authorizer_id,
        "COGNITO_POOL": cognito_pool,
        "BACKEND_HOST": backend_host,
        "AUTH_TYPE": auth_type,
        "CORS_TYPE": cors_type
    }

    clear_screen()
    logger.section("RESUMEN DE LA CONFIGURACIÓN")
    print_summary_item("API ID", config["API_ID"])
    print_summary_item("Variable de Conexión", config["CONNECTION_VARIABLE"])
    print_summary_item("ID de Authorizer", config["AUTHORIZER_ID"])
    print_summary_item("Cognito Pool", config["COGNITO_POOL"])
    print_summary_item("Host de Backend", config["BACKEND_HOST"], highlight=True)
    print_summary_item("Tipo de Autorización", config["AUTH_TYPE"])
    print_summary_item("Tipo de CORS", config["CORS_TYPE"])

    confirm = input(f"\n{ANSIColors.YELLOW}→{ANSIColors.RESET} ¿La configuración es correcta? (s/n): ").lower()
    if confirm == 's':
        logger.success("Configuración confirmada")
        return config
    else:
        logger.warning("Operación cancelada")
        return None

# ===================================================================
# SECCIÓN 3: LÓGICA DE API GATEWAY (CLASE PRINCIPAL)
# ===================================================================

class APIGatewayManager:
    def __init__(self, api_id: str, connection_variable: str, authorizer_id: str, config_manager: ConfigManager):
        self.api_id = api_id
        self.connection_variable = connection_variable
        self.authorizer_id = authorizer_id
        self.config = config_manager
        
    def run_command(self, command: str, description: str, ignore_conflict: bool = False) -> Dict:
        logger.info(f"{description}...")

        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)

            if result.returncode == 0:
                logger.success(description)
                response = json.loads(result.stdout) if result.stdout.strip() else {}
                return {"success": True, "data": response}
            else:
                if ignore_conflict and "ConflictException" in result.stderr:
                    logger.warning(f"{description} - Ya existe, continuando...")
                    return {"success": True, "data": {}, "existed": True}
                else:
                    error_msg = f"Error en {description} - Comando: {command}"
                    logger.dump_error(f"{error_msg}\nSTDERR: {result.stderr}\nSTDOUT: {result.stdout}")
                    logger.error(f"{description} - Error: {result.stderr}")
                    return {"success": False, "error": result.stderr}

        except json.JSONDecodeError as e:
            error_msg = f"Error parseando JSON en {description} - Comando: {command}"
            logger.dump_error(error_msg, e)
            logger.error(f"Error parseando JSON en {description}")
            return {"success": False, "error": "JSON parse error"}
        except Exception as e:
            error_msg = f"Excepción en {description} - Comando: {command}"
            logger.dump_error(error_msg, e)
            logger.error(f"Excepción en {description}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_root_resource_id(self) -> Optional[str]:
        command = f"aws apigateway get-resources --rest-api-id {self.api_id}"
        result = self.run_command(command, "Obteniendo recursos")
        
        if result["success"]:
            resources = result["data"].get("items", [])
            root_resource = next((r for r in resources if r["path"] == "/"), None)
            if root_resource:
                return root_resource["id"]
        return None
    
    def parse_uri_path(self, uri_path: str) -> List[Dict]:
        clean_path = uri_path.strip("/")
        segments = clean_path.split("/") if clean_path else []
        
        path_parts = []
        current_path = ""
        
        for segment in segments:
            current_path += "/" + segment
            
            if "{" in segment and "}" in segment:
                param_name = re.findall(r'\{(\w+)\}', segment)[0]
                path_parts.append({
                    "path": current_path, "segment": segment, "is_param": True, "param_name": param_name
                })
            else:
                path_parts.append({
                    "path": current_path, "segment": segment, "is_param": False
                })
        return path_parts
    
    def find_resource_by_path(self, target_path: str) -> Optional[str]:
        command = f"aws apigateway get-resources --rest-api-id {self.api_id}"
        result = self.run_command(command, f"Buscando recurso para path: {target_path}")

        if result["success"]:
            resources = result["data"].get("items", [])
            resource = next((r for r in resources if r["path"] == target_path), None)
            if resource:
                logger.debug(f"  ✓ Recurso encontrado: {resource['id']} -> {target_path}")
                return resource["id"]
        return None

    def create_resource(self, parent_id: str, path_part: str) -> Optional[str]:
        command = f"""aws apigateway create-resource --rest-api-id {self.api_id} --parent-id {parent_id} --path-part {path_part}"""
        result = self.run_command(command, f"Creando recurso: {path_part}")

        if result["success"]:
            resource_id = result["data"]["id"]
            logger.debug(f"  ✓ Recurso creado: {resource_id} -> {path_part}")
            return resource_id
        return None
    
    def ensure_resources_exist(self, uri_path: str) -> Optional[str]:
        """Asegura que todos los recursos existan, pidiendo confirmación antes de crear."""
        path_parts = self.parse_uri_path(uri_path)

        if not path_parts:
            return self.get_root_resource_id()

        logger.info(f"Analizando path de API Gateway: {uri_path}")
        logger.debug(f"Segmentos a crear: {[p['segment'] for p in path_parts]}")

        parent_id = self.get_root_resource_id()
        final_resource_id = parent_id

        for i, part in enumerate(path_parts):
            existing_id = self.find_resource_by_path(part["path"])

            if existing_id:
                final_resource_id = existing_id
                parent_id = existing_id
            else:
                prompt = f"\nEl recurso '{part['segment']}' no existe. ¿Crearlo? (s/n): "
                confirm = input(prompt).lower()

                if confirm != 's':
                    logger.warning("Creación cancelada por el usuario")
                    return None

                new_id = self.create_resource(parent_id, part["segment"])
                if new_id:
                    logger.info(f"  ➕ Configurando método OPTIONS por defecto para nuevo recurso: {part['segment']}")
                    self.create_options_method(new_id, "DEFAULT")
                    final_resource_id = new_id
                    parent_id = new_id
                else:
                    logger.error(f"Error creando recurso para {part['segment']}")
                    return None
        return final_resource_id
    
    def extract_path_parameters(self, uri_path: str) -> Dict[str, bool]:
        params = {}
        param_matches = re.findall(r'\{(\w+)\}', uri_path)
        for param in param_matches:
            params[f"method.request.path.{param}"] = True
        return params
    
    def create_http_method(self, resource_id: str, http_method: str, resource_path: str, backend_path: str, backend_host: str, auth_type: str, cognito_pool: str = None, custom_headers: Dict[str, str] = None):
        """
        Crea un método HTTP completo usando configuraciones .ini
        """
        method_config = self.config.get_method_config(http_method)

        # Determinar tipo de autorización
        if auth_type == "NO_AUTH":
            authorization_type = "NONE"
            authorizer_id = None
        else:
            authorization_type = "COGNITO_USER_POOLS"
            authorizer_id = self.authorizer_id

        if not authorizer_id and authorization_type == "COGNITO_USER_POOLS":
            logger.error(f"No se ha especificado ID de autorizador para {http_method}")
            return False

        # Los parámetros se extraen de la RUTA DE RECURSOS
        path_params = self.extract_path_parameters(resource_path)

        # Obtener headers de autorización
        auth_headers = {}
        if auth_type != "NO_AUTH":
            auth_headers = self.config.get_auth_headers(auth_type)
            # Reemplazar el placeholder del cognito pool si existe
            for key, value in auth_headers.items():
                if key == "CognitoPool" and cognito_pool:
                    auth_headers[key] = f"'{cognito_pool}'"
        else:
            auth_headers = self.config.get_auth_headers("NO_AUTH")

        # Remover CognitoPool si existe (no es un header real)
        auth_headers.pop('CognitoPool', None)

        # Agregar headers personalizados si existen
        if custom_headers:
            auth_headers.update(custom_headers)
        
        # Crear método
        method_command = f"""aws apigateway put-method --rest-api-id {self.api_id} --resource-id {resource_id} --http-method {http_method} --authorization-type {authorization_type}"""
        
        if authorizer_id:
            method_command += f" --authorizer-id {authorizer_id}"
            
        method_command += " --no-api-key-required"
        
        if path_params:
            params_json = json.dumps(path_params).replace('"', '\\"')
            method_command += f' --request-parameters "{params_json}"'
        
        result = self.run_command(method_command, f"Creando método {http_method}", ignore_conflict=True)
        if not result["success"]:
            return False
        
        # Preparar headers de integración (solo auth headers)
        integration_headers = auth_headers.copy()
        
        # Preparar path parameters para URL path parameters (no headers)
        path_parameters = {}
        param_matches = re.findall(r'\{(\w+)\}', resource_path)
        for param in param_matches:
            path_parameters[f"integration.request.path.{param}"] = f"method.request.path.{param}"
        
        # Agregar prefijo solo a los headers de autorización
        prefixed_headers = {}
        for key, value in integration_headers.items():
            if not key.startswith('integration.request.header.'):
                prefixed_headers[f"integration.request.header.{key}"] = value
            else:
                prefixed_headers[key] = value
        
        # Combinar headers y path parameters
        all_request_parameters = {}
        all_request_parameters.update(prefixed_headers)  # Headers de auth
        all_request_parameters.update(path_parameters)   # Path parameters
        
        params_json = json.dumps(all_request_parameters).replace('"', '\\"')
        
        # La URI de integración se arma con la RUTA COMPLETA DEL BACKEND
        full_backend_uri = f"{backend_host}{backend_path}"
        logger.debug(f"  🔗 URI de Integración: {full_backend_uri}")
        
        # Usar stage variable para connection-id
        connection_id_ref = f"${{stageVariables.{self.connection_variable}}}"

        integration_command = f"""aws apigateway put-integration --rest-api-id {self.api_id} --resource-id {resource_id} --http-method {http_method} --type {method_config['integration_type']} --integration-http-method {http_method} --uri "{full_backend_uri}" --connection-type {method_config['connection_type']} --connection-id "{connection_id_ref}" --request-parameters "{params_json}" --passthrough-behavior {method_config['passthrough_behavior']} --timeout-in-millis {method_config['timeout_millis']}"""
        
        result = self.run_command(integration_command, f"Configurando integración {http_method}")
        if not result["success"]:
            return False
        
        # Configurar respuesta del método
        models_json = json.dumps({"application/json": method_config['response_model']}).replace('"', '\\"')
        method_response_command = f"""aws apigateway put-method-response --rest-api-id {self.api_id} --resource-id {resource_id} --http-method {http_method} --status-code {method_config['response_status_code']} --response-models "{models_json}" """
        self.run_command(method_response_command, f"Configurando respuesta {http_method}", ignore_conflict=True)
        
        # Configurar respuesta de integración
        templates_dict = self.config.get_response_template()
        templates_json_str = json.dumps(templates_dict).replace('"', '\\"')
        integration_response_command = f"""aws apigateway put-integration-response --rest-api-id {self.api_id} --resource-id {resource_id} --http-method {http_method} --status-code {method_config['response_status_code']} --response-templates "{templates_json_str}" """
        return self.run_command(integration_response_command, f"Configurando respuesta de integración {http_method}", ignore_conflict=True)["success"]
    
    def create_options_method(self, resource_id: str, cors_type: str = "DEFAULT"):
        # Construir headers CORS desde configuración .ini
        cors_config = self.config.get_cors_headers(cors_type)
        cors_headers = {}
        
        for key, value in cors_config.items():
            # Convertir formato .ini a formato AWS API Gateway
            header_name = f"method.response.header.{key}"
            cors_headers[header_name] = value
            
        method_command = f"""aws apigateway put-method --rest-api-id {self.api_id} --resource-id {resource_id} --http-method OPTIONS --authorization-type NONE --no-api-key-required"""
        self.run_command(method_command, "Creando método OPTIONS", ignore_conflict=True)
        
        request_templates = {"application/json": '{"statusCode": 200}'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(request_templates, temp_file, indent=2)
            temp_filename = temp_file.name
        
        try:
            integration_command = f"""aws apigateway put-integration --rest-api-id {self.api_id} --resource-id {resource_id} --http-method OPTIONS --type MOCK --request-templates file://{temp_filename} --passthrough-behavior WHEN_NO_MATCH --timeout-in-millis CONFIG_TIMEOUT_MS"""
            result = self.run_command(integration_command, "Configurando integración OPTIONS")
            if not result["success"]: return False
        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
        
        # Generar response_params dinámicamente desde la configuración
        response_params = {}
        for key in cors_config.keys():
            header_name = f"method.response.header.{key}"
            response_params[header_name] = True
        params_json = json.dumps(response_params).replace('"', '\\"')
        method_response_command = f"""aws apigateway put-method-response --rest-api-id {self.api_id} --resource-id {resource_id} --http-method OPTIONS --status-code 200 --response-parameters "{params_json}" """
        self.run_command(method_response_command, "Configurando respuesta OPTIONS", ignore_conflict=True)
        
        cors_json = json.dumps(cors_headers).replace('"', '\\"')
        integration_response_command = f"""aws apigateway put-integration-response --rest-api-id {self.api_id} --resource-id {resource_id} --http-method OPTIONS --status-code 200 --response-parameters "{cors_json}" """
        return self.run_command(integration_response_command, "Configurando headers CORS", ignore_conflict=True)["success"]
    
    def verify_methods_integration(self, resource_id: str, http_methods: List[str]) -> bool:
        print("🔍 Verificando integraciones de métodos...")
        results = []
        
        for method in http_methods:
            command = f"aws apigateway get-integration --rest-api-id {self.api_id} --resource-id {resource_id} --http-method {method}"
            result = self.run_command(command, f"Verificando integración {method}")
            results.append(result["success"])
        
        options_command = f"aws apigateway get-integration --rest-api-id {self.api_id} --resource-id {resource_id} --http-method OPTIONS"
        options_result = self.run_command(options_command, "Verificando integración OPTIONS")
        results.append(options_result["success"])
        
        return all(results)

def create_endpoint_workflow(manager: APIGatewayManager, base_config: Dict[str, Any], endpoint_config: Dict[str, Any]) -> bool:
    """Flujo completo de creación de un endpoint"""
    FULL_BACKEND_PATH = endpoint_config["FULL_BACKEND_PATH"]
    HTTP_METHODS = endpoint_config["HTTP_METHODS"]
    CUSTOM_HEADERS = endpoint_config.get("CUSTOM_HEADERS", {})

    # Separación de rutas
    path_parts = FULL_BACKEND_PATH.strip("/").split("/")
    if len(path_parts) > 1:
        api_resource_path = "/" + "/".join(path_parts[1:])
    else:
        api_resource_path = FULL_BACKEND_PATH

    logger.info(f"   → Path de API Gateway: {api_resource_path}")
    logger.info(f"   → Path de integración Backend: {FULL_BACKEND_PATH}")
    logger.info(f"   → Métodos HTTP: {', '.join(HTTP_METHODS)}")
    logger.info(f"   → Tipo de autorización: {base_config['AUTH_TYPE']}")

    # Mostrar headers personalizados si existen
    if CUSTOM_HEADERS:
        print_headers_summary(CUSTOM_HEADERS, "Headers Personalizados")

    print("=" * 70)

    # Crear recursos necesarios
    final_resource_id = manager.ensure_resources_exist(api_resource_path)
    if not final_resource_id:
        logger.error("No se pudo crear el recurso")
        return False

    logger.success(f"ID de recurso final: {final_resource_id}")

    # Crear métodos HTTP seleccionados
    success_count = 0
    for http_method in HTTP_METHODS:
        logger.info(f"Configurando método {http_method}...")
        method_success = manager.create_http_method(
            final_resource_id,
            http_method,
            api_resource_path,
            FULL_BACKEND_PATH,
            base_config["BACKEND_HOST"],
            base_config["AUTH_TYPE"],
            base_config["COGNITO_POOL"],
            CUSTOM_HEADERS if CUSTOM_HEADERS else None
        )

        if method_success:
            logger.success(f"Método {http_method} configurado exitosamente")
            success_count += 1
        else:
            logger.error(f"Error configurando método {http_method}")

    # Configurar OPTIONS (CORS)
    logger.info("Configurando método OPTIONS (CORS)...")
    options_success = manager.create_options_method(final_resource_id, base_config["CORS_TYPE"])
    if options_success:
        logger.success("Método OPTIONS (CORS) configurado exitosamente")
    else:
        logger.warning("Error configurando OPTIONS")

    logger.info("Verificando integraciones finales...")
    if manager.verify_methods_integration(final_resource_id, HTTP_METHODS):
        logger.section("ENDPOINT CREADO EXITOSAMENTE")
        logger.success(f"{success_count}/{len(HTTP_METHODS)} métodos creados exitosamente")
        return True
    else:
        logger.error("Error verificando integraciones del recurso")
        return False

def main():
    try:
        logger.section("API GATEWAY MULTI-METHOD CREATOR by Zamma")

        # Inicializar gestor de configuraciones
        config_manager = ConfigManager()

        # Mostrar menú principal
        choice = main_menu()
        if not choice:
            sys.exit(1)

        if choice == "create_profile":
            # Workflow para crear nuevo perfil (sin crear recursos)
            if create_profile_workflow(config_manager):
                logger.section("PROCESO COMPLETADO")
                logger.success("¡Perfil creado exitosamente!")
            else:
                logger.warning("El perfil no fue guardado")
            sys.exit(0)

        elif choice == "load_profile":
            # Workflow para cargar perfil existente y crear recursos
            base_config = load_profile_workflow()
            if not base_config:
                logger.error("No se pudo cargar un perfil válido")
                sys.exit(1)

            # Extraer configuración base
            API_ID = base_config["API_ID"]
            CONNECTION_VARIABLE = base_config["CONNECTION_VARIABLE"]
            AUTHORIZER_ID = base_config["AUTHORIZER_ID"]

            # Crear manager con configuración base
            manager = APIGatewayManager(API_ID, CONNECTION_VARIABLE, AUTHORIZER_ID, config_manager)

            # Variables para controlar el flujo
            first_endpoint = True
            base_methods = None

            # Bucle principal para crear múltiples endpoints
            while True:
                logger.section("CONFIGURACIÓN DE NUEVO ENDPOINT")

                # Obtener configuración del endpoint
                if first_endpoint:
                    # Primer endpoint: viene de perfil cargado, pedir métodos
                    endpoint_config = get_endpoint_and_methods(None, config_manager, base_config["AUTH_TYPE"])
                    if endpoint_config:
                        base_methods = endpoint_config["HTTP_METHODS"]
                    first_endpoint = False
                else:
                    # Siguientes endpoints: reutilizar métodos base
                    endpoint_config = get_endpoint_and_methods(base_methods, config_manager, base_config["AUTH_TYPE"])

                if not endpoint_config:
                    break

                # Crear el endpoint
                success = create_endpoint_workflow(manager, base_config, endpoint_config)

                # Preguntar si desea crear otro endpoint
                create_another = input("\n🔄 ¿Deseas crear otro endpoint con la misma configuración? (s/n): ").lower()
                if create_another != 's':
                    break

            logger.section("PROCESO COMPLETADO")
            logger.success("¡Gracias por usar API Gateway Creator!")

    except KeyboardInterrupt:
        error_msg = "Proceso interrumpido por el usuario (Ctrl+C)"
        logger.dump_error(error_msg)
        logger.warning(error_msg)
        sys.exit(1)
    except Exception as e:
        error_msg = "Error inesperado en función principal"
        logger.dump_error(error_msg, e)
        logger.error(f"{error_msg}: {e}")
        logger.info("Revisa el archivo de dump de error para más detalles")
        sys.exit(1)

if __name__ == "__main__":
    main()