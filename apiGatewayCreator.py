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
# SECCIÓN 1: CONFIGURACIÓN Y CARGA DE ARCHIVOS .INI
# ===================================================================

def log_error(error_msg: str, exception: Exception = None):
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
        
        print(f"💾 Error guardado en: {error_file}")
        
    except Exception as log_err:
        print(f"❌ Error guardando log: {log_err}")
        print(f"❌ Error original: {error_msg}")
        if exception:
            print(f"❌ Excepción original: {exception}")

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
            print("✅ Archivos de configuración cargados exitosamente")
        except Exception as e:
            error_msg = f"Error cargando configuraciones desde {self.config_dir}"
            log_error(error_msg, e)
            print(f"❌ {error_msg}: {e}")
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
            log_error(f"{error_msg}\nSTDERR: {result.stderr}\nSTDOUT: {result.stdout}")
            print(f"❌ Error ejecutando el comando:\n{result.stderr}")
            return None
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError as e:
        error_msg = f"Error parseando JSON del comando: {command}"
        log_error(error_msg, e)
        print(f"❌ Error parseando JSON: {e}")
        return None
    except Exception as e:
        error_msg = f"Excepción inesperada ejecutando comando: {command}"
        log_error(error_msg, e)
        print(f"❌ Excepción inesperada: {e}")
        return None

def select_from_menu(prompt: str, items: List[Any], name_key: str = 'name', return_key: str = 'id') -> Optional[Any]:
    """
    Muestra un menú de opciones y retorna el valor de la clave especificada (o el objeto completo).
    Si return_key es None, retorna el objeto entero.
    """
    if not items:
        print(f"⚠️ No se encontraron items para '{prompt}'.")
        return None
    
    print(f"\n{prompt}")
    for i, item in enumerate(items):
        display_name = item.get(name_key, str(item)) if isinstance(item, dict) else str(item)
        print(f"  {i + 1} - {display_name}")
    
    while True:
        try:
            choice = int(input("Selecciona una opción: "))
            if 1 <= choice <= len(items):
                selected_item = items[choice - 1]
                return selected_item if not return_key else selected_item.get(return_key)
            else:
                print("❌ Opción inválida. Inténtalo de nuevo.")
        except ValueError:
            print("❌ Por favor, introduce un número.")

def select_api_grouped() -> Optional[str]:
    """Muestra un menú de APIs agrupadas por nombre base."""
    print("🔄 Obteniendo listado de APIs...")
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
    print("\nSelecciona el grupo de API:")
    for i, name in enumerate(sorted_group_names):
        print(f"  {i + 1} - {name}")

    selected_group_name = None
    while True:
        try:
            choice = int(input("Selecciona un grupo: "))
            if 1 <= choice <= len(sorted_group_names):
                selected_group_name = sorted_group_names[choice - 1]
                break
            else:
                print("❌ Opción inválida. Inténtalo de nuevo.")
        except ValueError:
            print("❌ Por favor, introduce un número.")

    apis_in_group = sorted(groups[selected_group_name], key=lambda x: x.get('name', ''))
    
    if len(apis_in_group) == 1:
        print(f"✅ Grupo con un solo miembro, seleccionando '{apis_in_group[0]['name']}' automáticamente.")
        return apis_in_group[0]['id']
        
    return select_from_menu("Selecciona la API específica del entorno:", apis_in_group, return_key='id')

def select_http_methods() -> List[str]:
    """Permite seleccionar múltiples métodos HTTP"""
    available_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
    print("\nSelecciona los métodos HTTP a crear (separados por comas):")
    for i, method in enumerate(available_methods):
        print(f"  {i + 1} - {method}")
    
    while True:
        try:
            choices = input("Ingresa los números separados por comas (ej: 1,2,3): ")
            indices = [int(x.strip()) - 1 for x in choices.split(',')]
            
            if all(0 <= idx < len(available_methods) for idx in indices):
                selected_methods = [available_methods[idx] for idx in indices]
                print(f"✅ Métodos seleccionados: {', '.join(selected_methods)}")
                return selected_methods
            else:
                print("❌ Alguna opción es inválida. Inténtalo de nuevo.")
        except ValueError:
            print("❌ Por favor, introduce números separados por comas.")

def select_auth_type() -> str:
    """Selecciona el tipo de autorización"""
    auth_types = ['COGNITO_ADMIN', 'COGNITO_CUSTOMER', 'NO_AUTH']
    descriptions = {
        'COGNITO_ADMIN': 'Para APIs administrativas (admin_id)',
        'COGNITO_CUSTOMER': 'Para APIs de cliente (customer_id)',
        'NO_AUTH': 'Sin autorización (APIs públicas)'
    }
    
    print("\nSelecciona el tipo de autorización:")
    for i, auth_type in enumerate(auth_types):
        print(f"  {i + 1} - {auth_type}: {descriptions[auth_type]}")
    
    while True:
        try:
            choice = int(input("Selecciona el tipo de autorización: "))
            if 1 <= choice <= len(auth_types):
                return auth_types[choice - 1]
            else:
                print("❌ Opción inválida. Inténtalo de nuevo.")
        except ValueError:
            print("❌ Por favor, introduce un número.")

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
    
    profile_name = input("\n📁 Introduce el nombre del perfil (sin extensión): ").strip()
    if not profile_name:
        print("❌ Nombre de perfil inválido")
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
        
        print(f"✅ Perfil guardado como: {profile_file}")
        return True
        
    except Exception as e:
        error_msg = f"Error guardando perfil de configuración"
        log_error(error_msg, e)
        print(f"❌ {error_msg}: {e}")
        return False

def load_configuration_profile(profile_name: str) -> Optional[Dict[str, Any]]:
    """Carga un perfil de configuración desde archivo INI"""
    profiles_dir = Path(__file__).parent / "profiles"
    profile_file = profiles_dir / f"{profile_name}.ini"
    
    if not profile_file.exists():
        print(f"❌ Perfil {profile_name} no encontrado")
        return None
    
    try:
        profile_config = configparser.ConfigParser()
        profile_config.read(profile_file)
        
        if 'PROFILE' not in profile_config:
            print(f"❌ Archivo de perfil {profile_name} mal formateado")
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
        
        print(f"✅ Perfil {profile_name} cargado exitosamente")
        return config
        
    except Exception as e:
        error_msg = f"Error cargando perfil {profile_name}"
        log_error(error_msg, e)
        print(f"❌ {error_msg}: {e}")
        return None

def validate_configuration_profile(config: Dict[str, Any]) -> Dict[str, bool]:
    """Valida que los recursos de un perfil aún existan"""
    print("🔍 Validando configuración cargada...")
    validation_results = {}

    # Validar API
    api_data = run_aws_command(f"aws apigateway get-rest-api --rest-api-id {config['API_ID']}")
    validation_results['API'] = api_data is not None

    # Validar que la stage variable existe
    stages_data = run_aws_command(f"aws apigateway get-stages --rest-api-id {config['API_ID']}")
    validation_results['VPC_LINK_VARIABLE'] = False
    if stages_data and 'item' in stages_data:
        for stage in stages_data['item']:
            stage_vars = stage.get('variables', {})
            if config['CONNECTION_VARIABLE'] in stage_vars:
                validation_results['VPC_LINK_VARIABLE'] = True
                break

    # Validar Authorizer
    authorizers = run_aws_command(f"aws apigateway get-authorizers --rest-api-id {config['API_ID']}")
    validation_results['AUTHORIZER'] = False
    if authorizers and 'items' in authorizers:
        validation_results['AUTHORIZER'] = any(auth['id'] == config['AUTHORIZER_ID'] for auth in authorizers['items'])

    # Validar Cognito Pool
    pools = run_aws_command("aws cognito-idp list-user-pools --max-results 60")
    validation_results['COGNITO_POOL'] = False
    if pools and 'UserPools' in pools:
        validation_results['COGNITO_POOL'] = any(pool['Name'] == config['COGNITO_POOL'] for pool in pools['UserPools'])

    return validation_results

def select_configuration_source() -> Optional[Dict[str, Any]]:
    """Permite elegir entre cargar perfil existente o crear nueva configuración"""
    profiles = list_configuration_profiles()
    
    print("\n🔧 ¿Cómo deseas configurar la API?")
    
    if profiles:
        print("  1 - Cargar perfil de configuración existente")
        print("  2 - Crear nueva configuración")
        
        while True:
            try:
                choice = int(input("Selecciona una opción: "))
                if choice == 1:
                    return select_existing_profile(profiles)
                elif choice == 2:
                    return get_interactive_config()
                else:
                    print("❌ Opción inválida. Inténtalo de nuevo.")
            except ValueError:
                print("❌ Por favor, introduce un número.")
    else:
        print("  No se encontraron perfiles existentes.")
        print("  Procediendo con configuración manual...")
        return get_interactive_config()

def select_existing_profile(profiles: List[str]) -> Optional[Dict[str, Any]]:
    """Permite seleccionar un perfil existente de la lista"""
    print("\n📋 Perfiles de configuración disponibles:")
    for i, profile in enumerate(profiles):
        print(f"  {i + 1} - {profile}")
    
    while True:
        try:
            choice = int(input("Selecciona un perfil: "))
            if 1 <= choice <= len(profiles):
                selected_profile = profiles[choice - 1]
                config = load_configuration_profile(selected_profile)
                
                if config:
                    return validate_and_confirm_profile(config, selected_profile)
                return None
            else:
                print("❌ Opción inválida. Inténtalo de nuevo.")
        except ValueError:
            print("❌ Por favor, introduce un número.")

def validate_and_confirm_profile(config: Dict[str, Any], profile_name: str) -> Optional[Dict[str, Any]]:
    """Valida un perfil cargado y permite al usuario confirmarlo o modificarlo"""
    # Validar recursos
    validation_results = validate_configuration_profile(config)
    
    # Mostrar resumen de validación
    print(f"\n📊 Validación del perfil '{profile_name}':")
    for resource, is_valid in validation_results.items():
        status = "✅" if is_valid else "❌"
        print(f"  {status} {resource}")
    
    # Si hay errores, avisar
    invalid_resources = [k for k, v in validation_results.items() if not v]
    if invalid_resources:
        print(f"\n⚠️ Los siguientes recursos no son válidos: {', '.join(invalid_resources)}")
        print("   Necesitarás reconfigurar estos elementos.")
        
        retry = input("\n¿Deseas intentar reconfigurar manualmente? (s/n): ").lower()
        if retry == 's':
            return get_interactive_config()
        else:
            return None
    
    # Mostrar resumen de la configuración
    print(f"\n" + "="*70)
    print(f"Resumen del Perfil '{profile_name}':")
    print(f"  - API ID: {config['API_ID']}")
    print(f"  - Connection Variable: {config['CONNECTION_VARIABLE']}")
    print(f"  - Authorizer ID: {config['AUTHORIZER_ID']}")
    print(f"  - Cognito Pool: {config['COGNITO_POOL']}")
    print(f"  - Backend Host: {config['BACKEND_HOST']}")
    print(f"  - Auth Type: {config['AUTH_TYPE']}")
    print(f"  - CORS Type: {config['CORS_TYPE']}")
    print("="*70)
    
    print("\n¿Qué deseas hacer?")
    print("  1 - Continuar con esta configuración")
    print("  2 - Seleccionar otro perfil")
    print("  3 - Crear nueva configuración manualmente")
    
    while True:
        try:
            choice = int(input("Selecciona una opción: "))
            if choice == 1:
                return config
            elif choice == 2:
                profiles = list_configuration_profiles()
                return select_existing_profile(profiles) 
            elif choice == 3:
                return get_interactive_config()
            else:
                print("❌ Opción inválida. Inténtalo de nuevo.")
        except ValueError:
            print("❌ Por favor, introduce un número.")

def get_endpoint_and_methods(reuse_methods: List[str] = None) -> Optional[Dict[str, Any]]:
    """Solicita solo el endpoint y opcionalmente métodos para usar con configuración existente"""
    print("\n🛠️ Configuración del endpoint:")
    
    # Si es el primer endpoint o el usuario quiere cambiar métodos
    if reuse_methods is None:
        http_methods = select_http_methods()
    else:
        print(f"📋 Reutilizando métodos de la configuración base: {', '.join(reuse_methods)}")
        change_methods = input("¿Deseas cambiar los métodos para este endpoint? (s/n): ").lower()
        if change_methods == 's':
            http_methods = select_http_methods()
        else:
            http_methods = reuse_methods
    
    print("\nPor favor, introduce el siguiente valor:")
    full_backend_path = input("Path COMPLETO del backend (ej: /discounts/b2c/campaigns/{id}): ")
    
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
    
    print("\n" + "="*70)
    print("Resumen de la Configuración:")
    for key, value in config.items():
        if key == "HTTP_METHODS":
            print(f"  - {key}: {', '.join(value)}")
        else:
            print(f"  - {key}: {value}")
    print("="*70)
    
    confirm = input("\n¿La configuración es correcta? (s/n): ").lower()
    if confirm == 's':
        return config
    else:
        print("Operación cancelada.")
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
        print(f"🔄 {description}...")
        
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                print(f"✅ {description} - Exitoso")
                response = json.loads(result.stdout) if result.stdout.strip() else {}
                return {"success": True, "data": response}
            else:
                if ignore_conflict and "ConflictException" in result.stderr:
                    print(f"⚠️ {description} - Ya existe, continuando...")
                    return {"success": True, "data": {}, "existed": True}
                else:
                    error_msg = f"Error en {description} - Comando: {command}"
                    log_error(f"{error_msg}\nSTDERR: {result.stderr}\nSTDOUT: {result.stdout}")
                    print(f"❌ {description} - Error: {result.stderr}")
                    return {"success": False, "error": result.stderr}
                    
        except json.JSONDecodeError as e:
            error_msg = f"Error parseando JSON en {description} - Comando: {command}"
            log_error(error_msg, e)
            print(f"❌ Error parseando JSON en {description}")
            return {"success": False, "error": "JSON parse error"}
        except Exception as e:
            error_msg = f"Excepción en {description} - Comando: {command}"
            log_error(error_msg, e)
            print(f"❌ Excepción en {description}: {e}")
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
                print(f"✅ Recurso encontrado: {resource['id']} -> {target_path}")
                return resource["id"]
        return None
    
    def create_resource(self, parent_id: str, path_part: str) -> Optional[str]:
        command = f"""aws apigateway create-resource --rest-api-id {self.api_id} --parent-id {parent_id} --path-part {path_part}"""
        result = self.run_command(command, f"Creando recurso: {path_part}")
        
        if result["success"]:
            resource_id = result["data"]["id"]
            print(f"✅ Recurso creado: {resource_id} -> {path_part}")
            return resource_id
        return None
    
    def ensure_resources_exist(self, uri_path: str) -> Optional[str]:
        """Asegura que todos los recursos existan, pidiendo confirmación antes de crear."""
        path_parts = self.parse_uri_path(uri_path)
        
        if not path_parts:
            return self.get_root_resource_id()
        
        print(f"📍 Analizando path de API Gateway: {uri_path}")
        print(f"📋 Segmentos a crear: {[p['segment'] for p in path_parts]}")
        
        parent_id = self.get_root_resource_id()
        final_resource_id = parent_id
        
        for i, part in enumerate(path_parts):
            existing_id = self.find_resource_by_path(part["path"])
            
            if existing_id:
                final_resource_id = existing_id
                parent_id = existing_id
            else:
                prompt = f"\n⚠️  El recurso '{part['segment']}' no existe. ¿Desea crearlo? (s/n): "
                confirm = input(prompt).lower()
                
                if confirm != 's':
                    print("❌ Creación cancelada por el usuario.")
                    return None
                
                new_id = self.create_resource(parent_id, part["segment"])
                if new_id:
                    print(f"➕ Configurando método OPTIONS por defecto para el nuevo recurso: {part['segment']}")
                    self.create_options_method(new_id, "DEFAULT")
                    final_resource_id = new_id
                    parent_id = new_id
                else:
                    print(f"❌ Error creando recurso para {part['segment']}")
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
            print(f"❌ No se ha especificado un ID de autorizador para {http_method}.")
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
        print(f"🔗 Configurando URI de integración hacia: {full_backend_uri}")
        
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

    print(f"   -> Ruta de API Gateway a crear: {api_resource_path}")
    print(f"   -> Ruta de Backend a integrar: {FULL_BACKEND_PATH}")
    print(f"   -> Métodos HTTP a crear: {', '.join(HTTP_METHODS)}")
    print(f"   -> Tipo de autorización: {base_config['AUTH_TYPE']}")
    print("=" * 70)

    # Crear recursos necesarios
    final_resource_id = manager.ensure_resources_exist(api_resource_path)
    if not final_resource_id:
        print("❌ No se pudo crear el recurso.")
        return False
    
    print(f"✅ Recurso final ID: {final_resource_id}")
    
    # Crear métodos HTTP seleccionados
    success_count = 0
    for http_method in HTTP_METHODS:
        print(f"\n🔧 Configurando método {http_method}...")
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
            print(f"✅ Método {http_method} configurado correctamente")
            success_count += 1
        else:
            print(f"❌ Error configurando método {http_method}")

    # Configurar OPTIONS (CORS)
    print(f"\n🔧 Configurando método OPTIONS (CORS)...")
    options_success = manager.create_options_method(final_resource_id, base_config["CORS_TYPE"])
    if options_success:
        print("✅ Método OPTIONS (CORS) configurado correctamente")
    else:
        print("⚠️ Warning: Error configurando OPTIONS.")
    
    print(f"\n🔍 Verificando integraciones finales...")
    if manager.verify_methods_integration(final_resource_id, HTTP_METHODS):
        print(f"🎉 ¡Endpoint configurado exitosamente!")
        print(f"✅ {success_count}/{len(HTTP_METHODS)} métodos creados correctamente")
        return True
    else:
        print("❌ Error verificando integraciones del recurso creado")
        return False

def main():
    try:
        print("🚀 API Gateway Multi-Method Creator by Zamma 🚀")
        print("=" * 70)
        
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
            print("\n" + "="*70)
            
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
        
        print("\n🏁 Proceso completado. ¡Gracias por usar API Gateway Creator!")
            
    except KeyboardInterrupt:
        error_msg = "Proceso interrumpido por el usuario (Ctrl+C)"
        log_error(error_msg)
        print(f"\n⚠️ {error_msg}")
        sys.exit(1)
    except Exception as e:
        error_msg = "Error inesperado en función principal"
        log_error(error_msg, e)
        print(f"\n❌ {error_msg}: {e}")
        print("💾 Revisa el archivo de error dump para más detalles.")
        sys.exit(1)

if __name__ == "__main__":
    main()