#!/usr/bin/env python3
import subprocess
import json
import sys
import re
import tempfile
import os
import configparser
import traceback
import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# ===================================================================
# SECCIÓN 0: SISTEMA DE LOGGING CON COLORES
# ===================================================================

# Color codes for better log visibility
class Colors:
    RESET = '\033[0m'
    INFO = '\033[0;36m'      # Cyan
    SUCCESS = '\033[0;32m'   # Green
    WARNING = '\033[0;33m'   # Yellow
    ERROR = '\033[0;31m'     # Red
    DEBUG = '\033[0;90m'     # Gray

def log_info(msg: str):
    """Log info message in cyan"""
    print(f"{Colors.INFO}[INFO]{Colors.RESET} {msg}")

def log_success(msg: str):
    """Log success message in green"""
    print(f"{Colors.SUCCESS}[SUCCESS]{Colors.RESET} {msg}")

def log_warning(msg: str):
    """Log warning message in yellow"""
    print(f"{Colors.WARNING}[WARNING]{Colors.RESET} {msg}")

def log_error(msg: str):
    """Log error message in red"""
    print(f"{Colors.ERROR}[ERROR]{Colors.RESET} {msg}")

def log_debug(msg: str):
    """Log debug message in gray"""
    print(f"{Colors.DEBUG}[DEBUG]{Colors.RESET} {msg}")

def log_section(title: str):
    """Log section separator with title"""
    print()
    print(f"{Colors.INFO}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.INFO}  {title}{Colors.RESET}")
    print(f"{Colors.INFO}{'═' * 70}{Colors.RESET}")

def print_menu_header(title: str):
    """Print a styled menu header"""
    print(f"\n{Colors.INFO}┌{'─' * 68}┐{Colors.RESET}")
    print(f"{Colors.INFO}│ {title:<67}│{Colors.RESET}")
    print(f"{Colors.INFO}└{'─' * 68}┘{Colors.RESET}")

def print_menu_option(number: int, text: str, emoji: str = "▸"):
    """Print a styled menu option"""
    print(f"  {Colors.SUCCESS}{emoji} {number}{Colors.RESET} - {text}")

def print_summary_item(label: str, value: str, highlight: bool = False):
    """Print a styled summary item"""
    if highlight:
        print(f"  {Colors.INFO}▸{Colors.RESET} {Colors.WARNING}{label}:{Colors.RESET} {Colors.SUCCESS}{value}{Colors.RESET}")
    else:
        print(f"  {Colors.INFO}▸{Colors.RESET} {label}: {Colors.DEBUG}{value}{Colors.RESET}")

def print_box_message(message: str, style: str = "info"):
    """Print a message in a box"""
    color = {
        "info": Colors.INFO,
        "success": Colors.SUCCESS,
        "warning": Colors.WARNING,
        "error": Colors.ERROR
    }.get(style, Colors.INFO)

    lines = message.split('\n')
    max_len = max(len(line) for line in lines)

    print(f"\n{color}╔{'═' * (max_len + 2)}╗{Colors.RESET}")
    for line in lines:
        print(f"{color}║ {line:<{max_len}} ║{Colors.RESET}")
    print(f"{color}╚{'═' * (max_len + 2)}╝{Colors.RESET}")

# ===================================================================
# SECCIÓN 1: CONFIGURACIÓN Y CARGA DE ARCHIVOS .INI
# ===================================================================

def save_error_dump(error_msg: str, exception: Exception = None):
    """Guarda errores en un archivo de dump con timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    error_file = Path(__file__).parent / f"error_dump_{timestamp}.log"

    try:
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"=== ERROR DUMP - {datetime.datetime.now().isoformat()} ===\n\n")
            f.write(f"Error Message: {error_msg}\n\n")

            if exception:
                f.write(f"Exception Type: {type(exception).__name__}\n")
                f.write(f"Exception Message: {str(exception)}\n\n")
                f.write("Full Traceback:\n")
                f.write(traceback.format_exc())
                f.write("\n")

            f.write("=== END ERROR DUMP ===\n")

        log_debug(f"Dump de error guardado en: {error_file}")

    except Exception as log_err:
        log_error(f"Error al guardar dump de error: {log_err}")
        log_error(f"Error original: {error_msg}")
        if exception:
            log_error(f"Excepción original: {exception}")

class ConfigManager:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(__file__).parent / config_dir
        self.method_configs = configparser.ConfigParser()
        self.auth_headers = configparser.ConfigParser()
        self.cors_headers = configparser.ConfigParser()
        self.response_templates = configparser.ConfigParser()
        
        self._load_configs()
    
    def _load_configs(self):
        """Carga todos los archivos de configuración .ini"""
        try:
            self.method_configs.read(self.config_dir / "method_configs.ini")
            self.auth_headers.read(self.config_dir / "auth_headers.ini")
            self.cors_headers.read(self.config_dir / "cors_headers.ini")
            self.response_templates.read(self.config_dir / "response_templates.ini")
            log_success("Archivos de configuración cargados exitosamente")
        except Exception as e:
            error_msg = f"Error cargando configuraciones desde {self.config_dir}"
            save_error_dump(error_msg, e)
            log_error(f"{error_msg}: {e}")
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
            save_error_dump(f"{error_msg}\nSTDERR: {result.stderr}\nSTDOUT: {result.stdout}")
            log_error(f"Error al ejecutar comando:\n{result.stderr}")
            return None
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError as e:
        error_msg = f"Error parseando JSON del comando: {command}"
        save_error_dump(error_msg, e)
        log_error(f"Error parseando JSON: {e}")
        return None
    except Exception as e:
        error_msg = f"Excepción inesperada ejecutando comando: {command}"
        save_error_dump(error_msg, e)
        log_error(f"Excepción inesperada: {e}")
        return None

def select_from_menu(prompt: str, items: List[Any], name_key: str = 'name', return_key: str = 'id') -> Optional[Any]:
    """
    Muestra un menú de opciones y retorna el valor de la clave especificada (o el objeto completo).
    Si return_key es None, retorna el objeto entero.
    """
    if not items:
        log_warning(f"No se encontraron elementos para '{prompt}'")
        return None

    print_menu_header(prompt)
    for i, item in enumerate(items):
        display_name = item.get(name_key, str(item)) if isinstance(item, dict) else str(item)
        print_menu_option(i + 1, display_name)

    while True:
        try:
            choice = int(input(f"\n{Colors.WARNING}→{Colors.RESET} Selecciona una opción: "))
            if 1 <= choice <= len(items):
                selected_item = items[choice - 1]
                selected_display = selected_item.get(name_key, str(selected_item)) if isinstance(selected_item, dict) else str(selected_item)
                log_success(f"Seleccionado: {selected_display}")
                return selected_item if not return_key else selected_item.get(return_key)
            else:
                log_error("Opción inválida. Inténtalo de nuevo.")
        except ValueError:
            log_error("Por favor, introduce un número.")

def select_api_grouped() -> Optional[str]:
    """Muestra un menú de APIs agrupadas por nombre base."""
    log_info("Obteniendo listado de APIs...")
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
    print_menu_header("Selecciona el grupo de API")
    for i, name in enumerate(sorted_group_names):
        print_menu_option(i + 1, name, emoji="📦")

    selected_group_name = None
    while True:
        try:
            choice = int(input(f"\n{Colors.WARNING}→{Colors.RESET} Selecciona un grupo: "))
            if 1 <= choice <= len(sorted_group_names):
                selected_group_name = sorted_group_names[choice - 1]
                log_success(f"Grupo seleccionado: {selected_group_name}")
                break
            else:
                log_error("Opción inválida. Inténtalo de nuevo.")
        except ValueError:
            log_error("Por favor, introduce un número.")

    apis_in_group = sorted(groups[selected_group_name], key=lambda x: x.get('name', ''))

    if len(apis_in_group) == 1:
        log_success(f"Grupo con un solo miembro, seleccionando automáticamente '{apis_in_group[0]['name']}'")
        return apis_in_group[0]['id']

    return select_from_menu("🌐 Selecciona la API específica del entorno", apis_in_group, return_key='id')

def select_http_methods() -> List[str]:
    """Permite seleccionar múltiples métodos HTTP"""
    available_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
    method_emojis = {'GET': '📥', 'POST': '📤', 'PUT': '✏️', 'DELETE': '🗑️', 'PATCH': '🔧'}

    print_menu_header("Selecciona los métodos HTTP a crear (separados por comas)")
    for i, method in enumerate(available_methods):
        emoji = method_emojis.get(method, '▸')
        print_menu_option(i + 1, method, emoji=emoji)

    while True:
        try:
            choices = input(f"\n{Colors.WARNING}→{Colors.RESET} Ingresa los números (ej: 1,2,3): ")
            indices = [int(x.strip()) - 1 for x in choices.split(',')]

            if all(0 <= idx < len(available_methods) for idx in indices):
                selected_methods = [available_methods[idx] for idx in indices]
                log_success(f"Métodos seleccionados: {', '.join(selected_methods)}")
                return selected_methods
            else:
                log_error("Algunas opciones son inválidas. Inténtalo de nuevo.")
        except ValueError:
            log_error("Por favor, introduce números separados por comas.")

def select_auth_type() -> str:
    """Selecciona el tipo de autorización"""
    auth_types = ['COGNITO_ADMIN', 'COGNITO_CUSTOMER', 'NO_AUTH']
    descriptions = {
        'COGNITO_ADMIN': 'Para APIs administrativas (admin_id)',
        'COGNITO_CUSTOMER': 'Para APIs de cliente (customer_id)',
        'NO_AUTH': 'Sin autorización (APIs públicas)'
    }
    auth_emojis = {
        'COGNITO_ADMIN': '👤',
        'COGNITO_CUSTOMER': '👥',
        'NO_AUTH': '🔓'
    }

    print_menu_header("Selecciona el tipo de autorización")
    for i, auth_type in enumerate(auth_types):
        emoji = auth_emojis.get(auth_type, '▸')
        text = f"{auth_type}: {Colors.DEBUG}{descriptions[auth_type]}{Colors.RESET}"
        print_menu_option(i + 1, text, emoji=emoji)

    while True:
        try:
            choice = int(input(f"\n{Colors.WARNING}→{Colors.RESET} Selecciona el tipo de autorización: "))
            if 1 <= choice <= len(auth_types):
                selected = auth_types[choice - 1]
                log_success(f"Tipo de autorización: {selected}")
                return selected
            else:
                log_error("Opción inválida. Inténtalo de nuevo.")
        except ValueError:
            log_error("Por favor, introduce un número.")

def select_cors_type() -> str:
    """Selecciona el tipo de CORS"""
    return "DEFAULT"  # Por ahora solo DEFAULT, pero es extensible

def list_configuration_profiles() -> List[str]:
    """Lista los archivos de configuración de perfiles disponibles"""
    profiles_dir = Path(__file__).parent / "profiles"
    if not profiles_dir.exists():
        return []
    
    profiles = []
    for file in profiles_dir.glob("*.ini"):
        profiles.append(file.stem)
    return profiles

def save_configuration_profile(config: Dict[str, Any]) -> bool:
    """Guarda un perfil de configuración en un archivo INI"""
    profiles_dir = Path(__file__).parent / "profiles"
    profiles_dir.mkdir(exist_ok=True)

    profile_name = input("\nIntroduce el nombre del perfil (sin extensión): ").strip()
    if not profile_name:
        log_error("Invalid profile name")
        return False

    profile_file = profiles_dir / f"{profile_name}.ini"

    try:
        profile_config = configparser.ConfigParser()
        profile_config['PROFILE'] = {
            'api_id': config['API_ID'],
            'connection_variable': config['CONNECTION_VARIABLE'],
            'authorizer_id': config['AUTHORIZER_ID'],
            'cognito_pool': config['COGNITO_POOL'],
            'backend_host': config['BACKEND_HOST'],
            'auth_type': config['AUTH_TYPE'],
            'cors_type': config['CORS_TYPE']
        }

        with open(profile_file, 'w') as f:
            profile_config.write(f)

        log_success(f"Perfil guardado como: {profile_file}")
        return True

    except Exception as e:
        error_msg = f"Error guardando perfil de configuración"
        save_error_dump(error_msg, e)
        log_error(f"{error_msg}: {e}")
        return False

def load_configuration_profile(profile_name: str) -> Optional[Dict[str, Any]]:
    """Carga un perfil de configuración desde archivo INI"""
    profiles_dir = Path(__file__).parent / "profiles"
    profile_file = profiles_dir / f"{profile_name}.ini"

    if not profile_file.exists():
        log_error(f"Perfil {profile_name} no encontrado")
        return None

    try:
        profile_config = configparser.ConfigParser()
        profile_config.read(profile_file)

        if 'PROFILE' not in profile_config:
            log_error(f"Archivo de perfil {profile_name} mal formateado")
            return None

        config = {
            'API_ID': profile_config['PROFILE']['api_id'],
            'CONNECTION_VARIABLE': profile_config['PROFILE']['connection_variable'],
            'AUTHORIZER_ID': profile_config['PROFILE']['authorizer_id'],
            'COGNITO_POOL': profile_config['PROFILE']['cognito_pool'],
            'BACKEND_HOST': profile_config['PROFILE']['backend_host'],
            'AUTH_TYPE': profile_config['PROFILE']['auth_type'],
            'CORS_TYPE': profile_config['PROFILE']['cors_type']
        }

        log_success(f"Perfil {profile_name} cargado exitosamente")
        return config

    except Exception as e:
        error_msg = f"Error cargando perfil {profile_name}"
        save_error_dump(error_msg, e)
        log_error(f"{error_msg}: {e}")
        return None

def validate_configuration_profile(config: Dict[str, Any]) -> Dict[str, bool]:
    """Valida que los recursos de un perfil aún existan"""
    log_info("Validando configuración cargada...")
    validation_results = {}

    # Validar API
    log_debug("Verificando API...")
    api_data = run_aws_command(f"aws apigateway get-rest-api --rest-api-id {config['API_ID']}")
    validation_results['API'] = api_data is not None
    if validation_results['API']:
        log_debug("  ✓ API encontrada")
    else:
        log_debug("  ✗ API no encontrada")

    # Validar que la stage variable existe
    log_debug("Verificando variable de stage...")
    stages_data = run_aws_command(f"aws apigateway get-stages --rest-api-id {config['API_ID']}")
    validation_results['VPC_LINK_VARIABLE'] = False
    if stages_data and 'item' in stages_data:
        for stage in stages_data['item']:
            stage_vars = stage.get('variables', {})
            if config['CONNECTION_VARIABLE'] in stage_vars:
                validation_results['VPC_LINK_VARIABLE'] = True
                break
    if validation_results['VPC_LINK_VARIABLE']:
        log_debug("  ✓ Variable VPC Link encontrada")
    else:
        log_debug("  ✗ Variable VPC Link no encontrada")

    # Validar Authorizer
    log_debug("Verificando Authorizer...")
    authorizers = run_aws_command(f"aws apigateway get-authorizers --rest-api-id {config['API_ID']}")
    validation_results['AUTHORIZER'] = False
    if authorizers and 'items' in authorizers:
        validation_results['AUTHORIZER'] = any(auth['id'] == config['AUTHORIZER_ID'] for auth in authorizers['items'])
    if validation_results['AUTHORIZER']:
        log_debug("  ✓ Authorizer encontrado")
    else:
        log_debug("  ✗ Authorizer no encontrado")

    # Validar Cognito Pool
    log_debug("Verificando Cognito Pool...")
    pools = run_aws_command("aws cognito-idp list-user-pools --max-results 60")
    validation_results['COGNITO_POOL'] = False
    if pools and 'UserPools' in pools:
        validation_results['COGNITO_POOL'] = any(pool['Name'] == config['COGNITO_POOL'] for pool in pools['UserPools'])
    if validation_results['COGNITO_POOL']:
        log_debug("  ✓ Cognito Pool encontrado")
    else:
        log_debug("  ✗ Cognito Pool no encontrado")

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
                choice = int(input(f"\n{Colors.WARNING}→{Colors.RESET} Selecciona una opción: "))
                if choice == 1:
                    return select_existing_profile(profiles)
                elif choice == 2:
                    return get_interactive_config()
                else:
                    log_error("Opción inválida. Inténtalo de nuevo.")
            except ValueError:
                log_error("Por favor, introduce un número.")
    else:
        log_warning("No se encontraron perfiles existentes")
        log_info("Procediendo con configuración manual...")
        return get_interactive_config()

def select_existing_profile(profiles: List[str]) -> Optional[Dict[str, Any]]:
    """Permite seleccionar un perfil existente de la lista"""
    print_menu_header("📋 Perfiles de configuración disponibles")
    for i, profile in enumerate(profiles):
        print_menu_option(i + 1, profile, emoji="📄")

    while True:
        try:
            choice = int(input(f"\n{Colors.WARNING}→{Colors.RESET} Selecciona un perfil: "))
            if 1 <= choice <= len(profiles):
                selected_profile = profiles[choice - 1]
                config = load_configuration_profile(selected_profile)

                if config:
                    return validate_and_confirm_profile(config, selected_profile)
                return None
            else:
                log_error("Opción inválida. Inténtalo de nuevo.")
        except ValueError:
            log_error("Por favor, introduce un número.")

def validate_and_confirm_profile(config: Dict[str, Any], profile_name: str) -> Optional[Dict[str, Any]]:
    """Valida un perfil cargado y permite al usuario confirmarlo o modificarlo"""
    # Validar recursos
    validation_results = validate_configuration_profile(config)
    
    # Mostrar resumen de validación
    print(f"\n{Colors.INFO}📊 Resultados de Validación para '{profile_name}':{Colors.RESET}")
    for resource, is_valid in validation_results.items():
        if is_valid:
            print(f"  {Colors.SUCCESS}✓{Colors.RESET} {resource}")
        else:
            print(f"  {Colors.ERROR}✗{Colors.RESET} {resource}")

    # Si hay errores, avisar
    invalid_resources = [k for k, v in validation_results.items() if not v]
    if invalid_resources:
        print_box_message(f"Recursos inválidos: {', '.join(invalid_resources)}\nNecesitas reconfigurar estos elementos.", style="warning")

        retry = input(f"\n{Colors.WARNING}→{Colors.RESET} ¿Deseas intentar reconfigurar manualmente? (s/n): ").lower()
        if retry == 's':
            return get_interactive_config()
        else:
            return None

    # Mostrar resumen de la configuración
    log_section(f"RESUMEN DEL PERFIL: {profile_name}")
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
            choice = int(input(f"\n{Colors.WARNING}→{Colors.RESET} Selecciona una opción: "))
            if choice == 1:
                log_success("Continuando con esta configuración")
                return config
            elif choice == 2:
                profiles = list_configuration_profiles()
                return select_existing_profile(profiles)
            elif choice == 3:
                return get_interactive_config()
            else:
                log_error("Opción inválida. Inténtalo de nuevo.")
        except ValueError:
            log_error("Por favor, introduce un número.")

def get_endpoint_and_methods(reuse_methods: List[str] = None) -> Optional[Dict[str, Any]]:
    """Solicita solo el endpoint y opcionalmente métodos para usar con configuración existente"""
    log_section("CONFIGURACIÓN DEL ENDPOINT")

    # Si es el primer endpoint o el usuario quiere cambiar métodos
    if reuse_methods is None:
        http_methods = select_http_methods()
    else:
        log_info(f"📋 Reutilizando métodos base: {', '.join(reuse_methods)}")
        change_methods = input(f"{Colors.WARNING}→{Colors.RESET} ¿Deseas cambiar los métodos para este endpoint? (s/n): ").lower()
        if change_methods == 's':
            http_methods = select_http_methods()
        else:
            http_methods = reuse_methods

    print(f"\n{Colors.INFO}Por favor, introduce el siguiente valor:{Colors.RESET}")
    full_backend_path = input(f"{Colors.WARNING}→{Colors.RESET} Path COMPLETO del backend (ej: /discounts/b2c/campaigns/{{id}}): ")
    
    return {
        "HTTP_METHODS": http_methods,
        "FULL_BACKEND_PATH": full_backend_path
    }

def get_interactive_config() -> Optional[Dict[str, Any]]:
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

    stages_data = run_aws_command(f"aws apigateway get-stages --rest-api-id {api_id}")
    if not stages_data or 'item' not in stages_data: return None

    selected_stage = select_from_menu("Selecciona la Etapa (Stage) de la API:", stages_data['item'], name_key='stageName', return_key=None)
    if not selected_stage: return None

    stage_variables = selected_stage.get('variables', {})
    if not stage_variables:
        print(f"⚠️ La etapa '{selected_stage['stageName']}' no tiene variables definidas.")
        connection_variable = input("Nombre de la variable de etapa para VPC Link (ej: vpcLinkId): ")
        backend_host = input("Host del backend (ej: https://mi.backend.com): ")
    else:
        print("\n📋 Variables de etapa disponibles:")
        for key, value in stage_variables.items():
            print(f"  - {key}: {value}")

        connection_variable = select_from_menu("Selecciona la Variable de Etapa para el VPC Link:", list(stage_variables.keys()), name_key=None, return_key=None)
        if not connection_variable: return None

        variable_name = select_from_menu("Selecciona la Variable de Etapa para el host del backend:", list(stage_variables.keys()), name_key=None, return_key=None)
        if not variable_name: return None
        backend_host = f"https://${{stageVariables.{variable_name}}}"
    
    # Selección de métodos HTTP
    http_methods = select_http_methods()
    
    # Selección de tipo de autorización
    auth_type = select_auth_type()
    
    # Selección de tipo de CORS
    cors_type = select_cors_type()
    
    print("\nPor favor, introduce los siguientes valores:")
    full_backend_path = input("Path COMPLETO del backend (ej: /discounts/b2c/campaigns/{id}): ")

    config = {
        "API_ID": api_id,
        "CONNECTION_VARIABLE": connection_variable,
        "AUTHORIZER_ID": authorizer_id,
        "FULL_BACKEND_PATH": full_backend_path,
        "COGNITO_POOL": cognito_pool,
        "BACKEND_HOST": backend_host,
        "HTTP_METHODS": http_methods,
        "AUTH_TYPE": auth_type,
        "CORS_TYPE": cors_type
    }
    
    log_section("RESUMEN DE LA CONFIGURACIÓN")
    print_summary_item("API ID", config["API_ID"])
    print_summary_item("Variable de Conexión", config["CONNECTION_VARIABLE"])
    print_summary_item("ID de Authorizer", config["AUTHORIZER_ID"])
    print_summary_item("Cognito Pool", config["COGNITO_POOL"])
    print_summary_item("Host de Backend", config["BACKEND_HOST"], highlight=True)
    print_summary_item("Path de Backend", config["FULL_BACKEND_PATH"], highlight=True)
    print_summary_item("Métodos HTTP", ', '.join(config["HTTP_METHODS"]), highlight=True)
    print_summary_item("Tipo de Autorización", config["AUTH_TYPE"])
    print_summary_item("Tipo de CORS", config["CORS_TYPE"])

    confirm = input(f"\n{Colors.WARNING}→{Colors.RESET} ¿La configuración es correcta? (s/n): ").lower()
    if confirm == 's':
        log_success("Configuración confirmada")
        return config
    else:
        log_warning("Operación cancelada")
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
        log_info(f"{description}...")

        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)

            if result.returncode == 0:
                log_success(description)
                response = json.loads(result.stdout) if result.stdout.strip() else {}
                return {"success": True, "data": response}
            else:
                if ignore_conflict and "ConflictException" in result.stderr:
                    log_warning(f"{description} - Ya existe, continuando...")
                    return {"success": True, "data": {}, "existed": True}
                else:
                    error_msg = f"Error en {description} - Comando: {command}"
                    save_error_dump(f"{error_msg}\nSTDERR: {result.stderr}\nSTDOUT: {result.stdout}")
                    log_error(f"{description} - Error: {result.stderr}")
                    return {"success": False, "error": result.stderr}

        except json.JSONDecodeError as e:
            error_msg = f"Error parseando JSON en {description} - Comando: {command}"
            save_error_dump(error_msg, e)
            log_error(f"Error parseando JSON en {description}")
            return {"success": False, "error": "JSON parse error"}
        except Exception as e:
            error_msg = f"Excepción en {description} - Comando: {command}"
            save_error_dump(error_msg, e)
            log_error(f"Excepción en {description}: {e}")
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
                log_debug(f"  ✓ Recurso encontrado: {resource['id']} -> {target_path}")
                return resource["id"]
        return None

    def create_resource(self, parent_id: str, path_part: str) -> Optional[str]:
        command = f"""aws apigateway create-resource --rest-api-id {self.api_id} --parent-id {parent_id} --path-part {path_part}"""
        result = self.run_command(command, f"Creando recurso: {path_part}")

        if result["success"]:
            resource_id = result["data"]["id"]
            log_debug(f"  ✓ Recurso creado: {resource_id} -> {path_part}")
            return resource_id
        return None
    
    def ensure_resources_exist(self, uri_path: str) -> Optional[str]:
        """Asegura que todos los recursos existan, pidiendo confirmación antes de crear."""
        path_parts = self.parse_uri_path(uri_path)

        if not path_parts:
            return self.get_root_resource_id()

        log_info(f"Analizando path de API Gateway: {uri_path}")
        log_debug(f"Segmentos a crear: {[p['segment'] for p in path_parts]}")

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
                    log_warning("Creación cancelada por el usuario")
                    return None

                new_id = self.create_resource(parent_id, part["segment"])
                if new_id:
                    log_info(f"  ➕ Configurando método OPTIONS por defecto para nuevo recurso: {part['segment']}")
                    self.create_options_method(new_id, "DEFAULT")
                    final_resource_id = new_id
                    parent_id = new_id
                else:
                    log_error(f"Error creando recurso para {part['segment']}")
                    return None
        return final_resource_id
    
    def extract_path_parameters(self, uri_path: str) -> Dict[str, bool]:
        params = {}
        param_matches = re.findall(r'\{(\w+)\}', uri_path)
        for param in param_matches:
            params[f"method.request.path.{param}"] = True
        return params
    
    def create_http_method(self, resource_id: str, http_method: str, resource_path: str, backend_path: str, backend_host: str, auth_type: str, cognito_pool: str = None):
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
            log_error(f"No se ha especificado ID de autorizador para {http_method}")
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
        log_debug(f"  🔗 URI de Integración: {full_backend_uri}")
        
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
            integration_command = f"""aws apigateway put-integration --rest-api-id {self.api_id} --resource-id {resource_id} --http-method OPTIONS --type MOCK --request-templates file://{temp_filename} --passthrough-behavior WHEN_NO_MATCH --timeout-in-millis 29000"""
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

    # Separación de rutas
    path_parts = FULL_BACKEND_PATH.strip("/").split("/")
    if len(path_parts) > 1:
        api_resource_path = "/" + "/".join(path_parts[1:])
    else:
        api_resource_path = FULL_BACKEND_PATH

    log_info(f"   → Path de API Gateway: {api_resource_path}")
    log_info(f"   → Path de integración Backend: {FULL_BACKEND_PATH}")
    log_info(f"   → Métodos HTTP: {', '.join(HTTP_METHODS)}")
    log_info(f"   → Tipo de autorización: {base_config['AUTH_TYPE']}")
    print("=" * 70)

    # Crear recursos necesarios
    final_resource_id = manager.ensure_resources_exist(api_resource_path)
    if not final_resource_id:
        log_error("No se pudo crear el recurso")
        return False

    log_success(f"ID de recurso final: {final_resource_id}")

    # Crear métodos HTTP seleccionados
    success_count = 0
    for http_method in HTTP_METHODS:
        log_info(f"Configurando método {http_method}...")
        method_success = manager.create_http_method(
            final_resource_id,
            http_method,
            api_resource_path,
            FULL_BACKEND_PATH,
            base_config["BACKEND_HOST"],
            base_config["AUTH_TYPE"],
            base_config["COGNITO_POOL"]
        )

        if method_success:
            log_success(f"Método {http_method} configurado exitosamente")
            success_count += 1
        else:
            log_error(f"Error configurando método {http_method}")

    # Configurar OPTIONS (CORS)
    log_info("Configurando método OPTIONS (CORS)...")
    options_success = manager.create_options_method(final_resource_id, base_config["CORS_TYPE"])
    if options_success:
        log_success("Método OPTIONS (CORS) configurado exitosamente")
    else:
        log_warning("Error configurando OPTIONS")

    log_info("Verificando integraciones finales...")
    if manager.verify_methods_integration(final_resource_id, HTTP_METHODS):
        log_section("ENDPOINT CREADO EXITOSAMENTE")
        log_success(f"{success_count}/{len(HTTP_METHODS)} métodos creados exitosamente")
        return True
    else:
        log_error("Error verificando integraciones del recurso")
        return False

def main():
    try:
        log_section("API GATEWAY MULTI-METHOD CREATOR by Zamma")

        # Inicializar gestor de configuraciones
        config_manager = ConfigManager()
        
        # Seleccionar fuente de configuración (perfil o manual)
        base_config = select_configuration_source()
        if not base_config:
            sys.exit(1)

        # Extraer configuración base
        API_ID = base_config["API_ID"]
        CONNECTION_VARIABLE = base_config["CONNECTION_VARIABLE"]
        AUTHORIZER_ID = base_config["AUTHORIZER_ID"]

        # Crear manager con configuración base
        manager = APIGatewayManager(API_ID, CONNECTION_VARIABLE, AUTHORIZER_ID, config_manager)
        
        # Variables para controlar el flujo
        profile_saved = False
        first_endpoint = True
        base_methods = None
        
        # Bucle principal para crear múltiples endpoints
        while True:
            log_section("CONFIGURACIÓN DE NUEVO ENDPOINT")
            
            # Obtener configuración del endpoint
            if first_endpoint:
                # Primer endpoint: podría incluir métodos si viene de configuración manual
                if "HTTP_METHODS" in base_config:
                    # Viene de configuración manual, ya tiene métodos
                    endpoint_config = {
                        "HTTP_METHODS": base_config["HTTP_METHODS"],
                        "FULL_BACKEND_PATH": base_config["FULL_BACKEND_PATH"]
                    }
                    base_methods = base_config["HTTP_METHODS"]
                else:
                    # Viene de perfil cargado, pedir métodos
                    endpoint_config = get_endpoint_and_methods()
                    if endpoint_config:
                        base_methods = endpoint_config["HTTP_METHODS"]
                first_endpoint = False
            else:
                # Siguientes endpoints: reutilizar métodos base
                endpoint_config = get_endpoint_and_methods(base_methods)
            
            if not endpoint_config:
                break
            
            # Crear el endpoint
            success = create_endpoint_workflow(manager, base_config, endpoint_config)
            
            # Preguntar si desea guardar perfil (solo la primera vez y si es exitoso)
            if success and not profile_saved:
                save_profile = input("\n💾 ¿Deseas guardar esta configuración como perfil? (s/n): ").lower()
                if save_profile == 's':
                    if save_configuration_profile(base_config):
                        profile_saved = True
            
            # Preguntar si desea crear otro endpoint
            create_another = input("\n🔄 ¿Deseas crear otro endpoint con la misma configuración? (s/n): ").lower()
            if create_another != 's':
                break
        
        log_section("PROCESO COMPLETADO")
        log_success("¡Gracias por usar API Gateway Creator!")

    except KeyboardInterrupt:
        error_msg = "Proceso interrumpido por el usuario (Ctrl+C)"
        save_error_dump(error_msg)
        log_warning(error_msg)
        sys.exit(1)
    except Exception as e:
        error_msg = "Error inesperado en función principal"
        save_error_dump(error_msg, e)
        log_error(f"{error_msg}: {e}")
        log_info("Revisa el archivo de dump de error para más detalles")
        sys.exit(1)

if __name__ == "__main__":
    main()