# API Gateway Creator & Security Checker

Suite avanzada de herramientas para gestionar AWS API Gateway:
- **API Gateway Creator**: Crea métodos HTTP con configuraciones inteligentes
- **API Gateway Security Checker**: Auditoría de seguridad y análisis de endpoints

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
├── apiGatewayCreator.py                    # Script para crear endpoints
├── apiGatewaySecurityCheck.py              # 🆕 Script de auditoría de seguridad
├── config/
│   ├── method_configs.ini                  # Configuraciones por método HTTP
│   ├── auth_headers.ini                    # Headers de autorización
│   ├── cors_headers.ini                    # Headers CORS
│   └── response_templates.ini              # Templates de respuesta
├── profiles/                               # Perfiles de configuración guardados
│   ├── mi-api-dev.ini                     # Ejemplo de perfil
│   └── otro-perfil.ini                    # Otro perfil
├── reports/                                # 🆕 Reportes de auditoría y error logs
│   ├── MS-Discounts-Public-PROD_report_*.csv
│   ├── security_audit_report_*.csv
│   └── error_dump_*.log
├── common/                                 # 🆕 Módulos compartidos
│   ├── constants.py                       # Constantes globales
│   ├── exceptions.py                      # Excepciones personalizadas
│   ├── logging_config.py                  # Sistema de logging
│   └── models.py                          # Dataclasses
├── security_check/                         # 🆕 Módulo de auditoría
│   ├── api_filter.py                      # Filtrado de APIs
│   ├── concurrent_analyzer.py             # Análisis paralelo
│   └── metadata_collector.py              # Recolección de metadata
├── gateway_creator/                        # 🆕 Módulo de creación
│   ├── config_manager.py                  # Gestión de configuración
│   ├── ui_components.py                   # Componentes de UI
│   └── aws_manager.py                     # Gestor de AWS (stub)
└── README.md                               # Esta documentación
```

## 🆕 Auditoría de Seguridad

### Uso
```bash
python3 apiGatewaySecurityCheck.py
```

### Características
- ✅ **Análisis de autorización**: Identifica endpoints sin protección
- ✅ **Auditoría de authorizers**: Detalla nombre y tipo de cada authorizer
- ✅ **Filtrado automático**: Excluye APIs con sufijos -DEV y -CI
- ✅ **Whitelist de endpoints**: Excluye endpoints con autenticación en backend (config/whitelist.json)
- ✅ **Análisis secuencial por API**: APIs analizadas una por una (output limpio y ordenado)
- ✅ **Análisis paralelo de recursos**: Dentro de cada API, recursos en paralelo
- ✅ **Cache optimizado**: Escaneo de recursos paralelo (70% más rápido) + caching de authorizers paralelo (80% más rápido)
- ✅ **Reporte CSV**: Exportación detallada en tiempo real
- ✅ **Diferenciación API Key**: Columna separada para identificar endpoints con solo API Key
- ✅ **Interfaz interactiva**: Selección de API individual o todas
- ✅ **Pool configurable**: Un solo parámetro que escala automáticamente todo

### Flujo de Auditoría

```
1. Seleccionar API
   └─ Opción 1: Auditar API específica
   └─ Opción 2: Auditar todas las APIs

2. Configurar pool de recursos (1-10 workers)
   └─ Controla TODA la paralelización automáticamente

3. PARA CADA API (secuencial):

   a) Construcción optimizada de cache de authorizers
      └─ Fase 1: Escanea recursos en PARALELO (pool_size workers)
      └─ Fase 2: Cachea authorizers en PARALELO (pool_size/2 workers)
      └─ Tiempo: ~10-15 segundos (116 recursos)

   b) Análisis de recursos en paralelo (pool_size workers)
      └─ Procesa recursos simultáneamente
      └─ Genera reporte CSV en tiempo real
      └─ Muestra resumen por API

4. Resumen final
   └─ Total de APIs analizadas
   └─ Endpoints protegidos vs desprotegidos
   └─ Rate de éxito
```

### Optimizaciones Implementadas

| Aspecto | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Análisis de APIs | Paralelo (confuso) | Secuencial (limpio) | Mejor UX |
| Cache de recursos | Secuencial | Paralelo (10 workers) | ~70% más rápido |
| Cache de authorizers | Secuencial | Paralelo (auto-escala) | ~80% más rápido |
| Tiempo total cache | 30-35s | 10-15s | 60-70% más rápido |
| Pool configurable | No | Sí (auto-escala) | Total control |

### Salida del Reporte CSV

Columns:
- **api**: Nombre de la API
- **method**: Método HTTP (GET, POST, PUT, DELETE, PATCH)
- **path**: Ruta del endpoint
- **is_authorized**: YES/NO (tiene autorización mediante Cognito, Lambda, AWS IAM, etc. - NO incluye API Key)
- **authorization_type**: Tipo de autorización (NONE, COGNITO_USER_POOLS, CUSTOM, AWS_IAM)
- **specific_auth_type**: Tipo específico identificado (ADMIN, CUSTOMER, NONE, etc.)
- **authorizer_name**: Nombre del authorizer configurado (AdminProd, CustomerPROD, etc.)
- **api_key**: YES/NO (¿Requiere API Key?)
- **whitelisted**: YES/NO (¿Está en la whitelist de config/whitelist.json?)

Ejemplo:
```csv
api,method,path,is_authorized,authorization_type,specific_auth_type,authorizer_name,api_key,whitelisted
MS-Discounts-Public-PROD,PUT,/bo/campaigns/campaign-active,YES,COGNITO_USER_POOLS,ADMIN,AdminProd,NO,NO
MS-Discounts-Public-PROD,POST,/customer/rewards/valid-cash-wallet,NO,NONE,NONE,,NO,NO
MS-Discounts-Public-PROD,GET,/b2c/campaigns/referral,YES,COGNITO_USER_POOLS,CUSTOMER,CustomerPROD,NO,NO
MS-Discounts-Public-PROD,DELETE,/public/data,NO,NONE,NONE,,YES,NO
MS-Auth-Server-Public-PROD,POST,/oauth/token,NO,NONE,NONE,,NO,YES
```

### Interpretación de Resultados

| Caso | is_authorized | api_key | whitelisted | authorization_type | Acción |
|------|---|---|---|---|---|
| Endpoint protegido por Cognito Admin | YES | NO | NO | COGNITO_USER_POOLS | ✅ Seguro |
| Endpoint protegido por Lambda | YES | NO | NO | CUSTOM | ✅ Seguro |
| Endpoint sin autorización | NO | NO | NO | NONE | ⚠️ Revisar |
| Endpoint con solo API Key | NO | YES | NO | NONE | ⚠️ Débil (API Key alone) |
| API pública | NO | NO | NO | NONE | ⚠️ Intencional? |
| Endpoint en whitelist (backend auth) | NO | NO | YES | NONE | ✅ Excluido (tiene auth en MS) |

**Nota importante**: `is_authorized` muestra **solo autorización robusta** (Cognito, Lambda, AWS IAM). **API Key se reporta por separado** en la columna `api_key` para permitir un análisis granular de la seguridad.

### 🆕 Whitelist de Endpoints

#### Propósito
Excluir endpoints que tienen autenticación implementada **directamente en el microservicio** (no en API Gateway), evitando falsos positivos en el reporte de seguridad.

#### Ubicación
`config/whitelist.json`

#### Formato
```json
{
  "whitelist": {
    "MS-Auth-Server-Public-PROD": [
      "/oauth/token",
      "/oauth/authorize",
      "/auth/login"
    ],
    "MS-jumio-Public-PROD": [
      "/jumio/verification/*",
      "/jumio/status"
    ]
  }
}
```

#### Características
- **Coincidencia exacta**: `/oauth/token` coincide solo con esa ruta exacta
- **Patrones con wildcard**: `/jumio/verification/*` coincide con `/jumio/verification/123`, etc.
- **Auto-carga**: Se carga automáticamente al iniciar el análisis
- **Exclusión de CSV**: Los endpoints en whitelist **NO aparecen en el reporte CSV**

#### Cómo usar
1. Ejecuta el security check y ve los nombres de las APIs
2. Identifica endpoints que tienen autenticación en backend
3. Edita `config/whitelist.json` y agrega el API name y los endpoint paths
4. Ejecuta el security check de nuevo - ahora esos endpoints estarán excluidos

#### Ejemplo real
```json
{
  "whitelist": {
    "MS-Auth-Server-Public-PROD": [
      "/oauth/token",
      "/oauth/validate"
    ],
    "MS-Customer-Public-PROD": [
      "/customer/register",
      "/customer/login",
      "/customer/*/profile"
    ]
  }
}
```

---

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