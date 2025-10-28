# API Gateway Creator

Herramienta avanzada para automatizar la creación de endpoints en AWS API Gateway con configuración inteligente de métodos HTTP, integración VPC Link y autenticación Cognito.

## Características

- **Multi-método**: Crea múltiples métodos HTTP en una sola ejecución
- **Configuración flexible**: Archivos .ini para personalizar headers, autorización y respuestas
- **🆕 Perfiles de configuración**: Guarda y reutiliza configuraciones completas
- **🆕 Creación múltiple**: Crea varios endpoints sin reiniciar el script
- **🆕 Validación inteligente**: Verifica que los recursos guardados aún existan
- **Basado en patrones reales**: Configuraciones extraídas del análisis de APIs existentes
- **Autorización inteligente**: Soporte para Admin, Customer y APIs públicas
- **Interfaz interactiva**: Menús guiados para configuración fácil
- **🆕 Logging de errores**: Guarda errores detallados en archivos dump

## Estructura de Archivos

```
├── apiGatewayCreator.py                    # Script principal
├── config/
│   ├── method_configs.ini                  # Configuraciones por método HTTP
│   ├── auth_headers.ini                    # Headers de autorización
│   ├── cors_headers.ini                    # Headers CORS
│   └── response_templates.ini              # Templates de respuesta
├── gateway_creator/                        # Módulo de creación
│   ├── config_manager.py                   # Gestión de configuración
│   ├── aws_manager.py                      # Interfaz AWS
│   └── ui_components.py                    # Componentes de UI
├── common/                                 # Módulos compartidos
│   ├── constants.py                        # Constantes globales
│   ├── exceptions.py                       # Excepciones personalizadas
│   ├── logging_config.py                   # Sistema de logging
│   └── models.py                           # Dataclasses
├── profiles/                               # Perfiles de configuración guardados
├── reports/                                # Reportes de error
└── README.md                               # Esta documentación
```

## Creación de Endpoints

### Uso
```bash
python3 apiGatewayCreator.py
```

### 🆕 Nuevo Flujo Mejorado

#### **Opción 1: Cargar Perfil Existente**
1. **Selección de perfil**: Elige de perfiles guardados
2. **Validación automática**: Verifica que recursos aún existan
3. **Configuración del endpoint**: Solo path y métodos HTTP
4. **Creación múltiple**: Crea varios endpoints con la misma config

#### **Opción 2: Configuración Manual**
1. **Selección de API**: Elige de APIs agrupadas (excluye PROD automáticamente)
2. **Authorizer**: Elige el autorizador Cognito
3. **User Pool**: Selecciona el Cognito User Pool
4. **Stage**: Elige el stage y variables de entorno
5. **Variable de Stage para VPC Link**: Selecciona la variable que contiene el VPC Link ID
6. **Variable de Stage para Host**: Selecciona la variable que contiene el host del backend
7. **Autorización**: Elige tipo de auth (ADMIN/CUSTOMER/NO_AUTH)
8. **Guardar perfil**: Opción de guardar para reutilizar
9. **Configuración de endpoints**: Path y métodos para cada endpoint
10. **Bucle de creación**: Crea múltiples endpoints sin reiniciar

### Ejemplo de Ejecución

#### **🆕 Con Perfiles de Configuración:**
```
🚀 API Gateway Multi-Method Creator by Zamma 🚀
======================================================================

🔧 ¿Cómo deseas configurar la API?
  1 - Cargar perfil de configuración existente
  2 - Crear nueva configuración

📋 Perfiles de configuración disponibles:
  1 - discounts-dev
  2 - customer-api-dev
  3 - payments-prod

🔍 Validando configuración cargada...
  ✅ API
  ✅ VPC_LINK_VARIABLE
  ✅ AUTHORIZER
  ✅ COGNITO_POOL

🛠️ Configuración del endpoint:
Selecciona los métodos HTTP a crear: 2,3  # POST, PUT
Path COMPLETO del backend: /discounts/v2/campaigns/bulk

🎉 ¡Endpoint configurado exitosamente!

🔄 ¿Deseas crear otro endpoint con la misma configuración? (s/n): s

🛠️ Configuración del endpoint:
Path COMPLETO del backend: /discounts/v2/rewards/{id}
```

#### **Configuración Manual:**
```
🔧 ¿Cómo deseas configurar la API?
  1 - Cargar perfil de configuración existente
  2 - Crear nueva configuración

Selecciona el grupo de API:
  1 - MS-Discounts-Public
  2 - MS-Customer-Public

Selecciona el tipo de autorización:
  1 - COGNITO_ADMIN: Para APIs administrativas (admin_id)
  2 - COGNITO_CUSTOMER: Para APIs de cliente (customer_id)
  3 - NO_AUTH: Sin autorización (APIs públicas)

💾 ¿Deseas guardar esta configuración como perfil? (s/n): s
📁 Introduce el nombre del perfil: mi-nueva-api
```

## 🆕 Perfiles de Configuración

Los perfiles permiten guardar y reutilizar configuraciones completas de APIs, incluyendo:

- API ID
- Nombre de la variable de stage para VPC Link
- Authorizer ID y Cognito Pool
- Backend Host (con variable de stage)
- Tipo de autorización
- Configuración de CORS

### Ejemplo de Perfil (`profiles/mi-api-dev.ini`):
```ini
[PROFILE]
api_id = yyrwhkxsz4
connection_variable = vpcLinkId
authorizer_id = wiyx5b
cognito_pool = customer
backend_host = https://${stageVariables.urlDiscountsPrivate}
auth_type = COGNITO_CUSTOMER
cors_type = DEFAULT
```

### Ventajas de los Perfiles:
- **⚡ Rapidez**: Configuración inmediata
- **🔄 Reutilización**: Una vez configurado, usado múltiples veces
- **✅ Validación**: Verifica automáticamente que recursos existan
- **🛡️ Consistencia**: Same configuration across multiple endpoints

## Configuraciones

### method_configs.ini

Define comportamientos específicos por método HTTP:

```ini
[POST]
requires_body = true
typical_auth = COGNITO_USER_POOLS
cache_enabled = false
content_types = application/json
```

### auth_headers.ini

Headers de autorización por tipo:

```ini
[COGNITO_ADMIN]
Claim-Email = context.authorizer.claims.email
Claim-User-Id = context.authorizer.claims.custom:admin_id
CognitoPool = 'admin'
```

### cors_headers.ini

Configuraciones CORS:

```ini
[DEFAULT]
Access-Control-Allow-Methods = 'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT'
Access-Control-Allow-Origin = '*'
```

## Diferencias con apiGatewayGETcreator

| Característica | GET Creator | Multi Creator |
|----------------|-------------|---------------|
| Métodos | Solo GET | GET, POST, PUT, DELETE, PATCH |
| Configuración | Hardcoded | Archivos .ini configurables |
| Autorización | Solo Cognito | Cognito + No Auth |
| Headers | Fijos customer | Admin/Customer/Public |
| Selección | Manual | Multi-selección interactiva |

## Patrones Implementados

Basado en análisis de APIs reales, implementa:

- **Headers estándar**: KNOWN-TOKEN-KEY, X-Amzn-Request-Id
- **Claims Cognito**: email, admin_id/customer_id según tipo
- **Timeouts**: 29,000ms estándar
- **Passthrough**: WHEN_NO_MATCH para body handling
- **CORS**: Headers completos para OPTIONS
- **VPC Link**: Conexión privada estándar

## Ventajas

1. **🚀 Eficiencia Extrema**: Crea múltiples endpoints sin reiniciar
2. **💾 Reutilización**: Perfiles guardados para configuraciones recurrentes
3. **✅ Validación Inteligente**: Verifica recursos antes de usar
4. **🔄 Flujo Continuo**: Bucle para crear múltiples endpoints
5. **📊 Consistencia**: Configuraciones basadas en patrones reales
6. **🔧 Flexibilidad**: Personalizable via archivos .ini
7. **🛠️ Mantenibilidad**: Separación clara de configuraciones
8. **📈 Escalabilidad**: Fácil agregar nuevos tipos de auth/headers
9. **🐛 Debug Mejorado**: Logs detallados de errores con timestamp

## Casos de Uso

- **APIs CRUD completas**: POST/PUT/DELETE en una sola ejecución
- **APIs administrativas**: Con headers admin_id y autorización Cognito
- **APIs públicas**: Sin autorización, headers mínimos
- **APIs híbridas**: Diferentes métodos con diferentes configuraciones

## Troubleshooting

- **Error de configuración**: Verifica que existan los archivos .ini en `/config/`
- **Error de autorización**: Asegúrate de que el Authorizer ID sea válido
- **Error de VPC Link**: Verifica que el VPC Link esté activo
- **Conflictos**: El script maneja automáticamente recursos existentes

## Extensión

Para agregar nuevos tipos de autorización o headers:

1. Edita `auth_headers.ini` con la nueva sección
2. Actualiza la función `select_auth_type()` en el script
3. Opcionalmente modifica `method_configs.ini` para comportamientos específicos

---

## 🆕 Historial de Cambios - v2.1

### Nuevas Características

#### API Gateway Security Checker (`apiGatewaySecurityCheck.py`)
- ✨ Auditoría completa de endpoints sin autorización
- ✨ Detalle de authorizers y sus tipos específicos (ADMIN/CUSTOMER)
- ✨ Análisis concurrente configurable con ThreadPoolExecutor
- ✨ Cache de authorizers para evitar race conditions
- ✨ Filtrado automático de APIs -DEV y -CI
- ✨ Exportación a CSV sin dependencias de fecha
- ✨ Interfaz interactiva con menú guiado
- ✨ Resumen de ejecución y estadísticas

#### Reorganización de Módulos
- 📦 Nuevo paquete `common/`: Constantes, excepciones, logging, modelos
- 📦 Nuevo paquete `security_check/`: Filtrado, análisis concurrente, metadata
- 📦 Nuevo paquete `gateway_creator/`: UI, configuración, AWS manager
- 🎯 Mejor separación de responsabilidades
- 🎯 Código reutilizable y mantenible
- 🎯 Importaciones limpias y organizadas

#### Mejoras de Reportes
- 📊 Carpeta centralizada `/reports/` para todos los reportes y error logs
- 📊 Nombres de archivo inteligentes (por API o genérico)
- 📊 Reporte CSV con:
  - Nombre del API
  - Método HTTP
  - Path del endpoint
  - Estado de autorización
  - Tipo de autorización
  - Nombre del authorizer
  - Tipo específico (ADMIN/CUSTOMER/etc.)

#### Cambios de Rendimiento
- ⚡ Análisis paralelo de recursos (configurable)
- ⚡ Pool size configurable (1-10 workers)
- ⚡ Cache de authorizers (evita 100+ llamadas redundantes a AWS)
- ⚡ Actualización de reporte en tiempo real
- ⚡ Procesamiento sin bloqueos

### Cambios Técnicos

**Antes:**
- Análisis secuencial de recursos
- Llamadas duplicadas para cada authorizer por método
- Race conditions en análisis paralelo
- Reporte con fecha de análisis (no del recurso)
- Logs DEBUG en consola

**Después:**
- Análisis paralelo con cache de authorizers
- Una llamada por authorizer único
- Race conditions evitadas con cache sincronizado
- Reporte CSV limpio sin fechas
- Salida limpia sin DEBUG

### Requisitos

```bash
# AWS CLI configurado y con credenciales válidas
aws sts get-caller-identity

# Permisos IAM necesarios
- apigateway:GetRestApis
- apigateway:GetResources
- apigateway:GetMethod
- apigateway:GetAuthorizer
- cognito-idp:ListUserPools (opcional)

# Python 3.7+
python3 --version
```

### Compatibilidad

- ✅ Python 3.7, 3.8, 3.9, 3.10, 3.11, 3.12
- ✅ AWS CLI v2 (recomendado)
- ✅ WSL2 en Windows
- ✅ Linux (Ubuntu, Debian, etc.)
- ✅ macOS
- ✅ Cualquier región AWS

---

## 📈 Métricas de Rendimiento

Con 116 recursos y 4 authorizers únicos:
- **Tiempo de cache**: ~30-35 segundos (primero sincroniza con AWS)
- **Tiempo de análisis**: ~25-40 segundos (paralelo)
- **Tiempo total**: ~60-75 segundos
- **Recursos procesados/segundo**: 2-3 (paralelo vs ~0.5 secuencial)
- **Mejora de rendimiento**: 4x más rápido que análisis secuencial

---

## 🤝 Contribuciones

Para mejorar el proyecto:

1. Reporta bugs y feature requests en issues
2. Propone nuevos tipos de authorizers
3. Mejora la documentación
4. Agrega más modelos de configuración
5. Optimiza el rendimiento del análisis

---

## 📝 Licencia

© 2024 - Herramientas de API Gateway. Uso interno autorizado.