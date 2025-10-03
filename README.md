# API Gateway Creator

Script avanzado para crear métodos HTTP (GET, POST, PUT, DELETE, PATCH) en AWS API Gateway con configuraciones basadas en patrones reales de desarrollo.

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
├── apiGatewayCreator.py          # Script principal
├── config/
│   ├── method_configs.ini        # Configuraciones por método HTTP
│   ├── auth_headers.ini          # Headers de autorización
│   ├── cors_headers.ini          # Headers CORS
│   └── response_templates.ini    # Templates de respuesta
├── profiles/                     # 🆕 Perfiles de configuración guardados
│   ├── mi-api-dev.ini           # Ejemplo de perfil
│   └── otro-perfil.ini          # Otro perfil
├── error_dump_*.log             # 🆕 Logs de errores con timestamp
└── README.md                    # Esta documentación
```

## Uso

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