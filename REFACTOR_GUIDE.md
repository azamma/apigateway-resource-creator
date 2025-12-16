# 🔄 Guía de Refactorización - Nueva Arquitectura

## 📋 Resumen de Cambios

El script `apiGatewayCreator.py` ha sido refactorizado para usar una **arquitectura híbrida**:

- ✅ **Operaciones READ**: Directas con AWS CLI (listado de APIs, recursos, etc.)
- ✅ **Operaciones WRITE**: Delegadas a Lambda serverless (creación de recursos, métodos, integraciones)

---

## 🏗️ Nueva Arquitectura

```
┌─────────────────────────────────────────┐
│          USER PC (Cliente CLI)          │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │   apiGatewayCreator.py            │  │
│  │                                   │  │
│  │   READ Operations (AWS CLI)       │  │
│  │   ├─ list APIs                    │  │
│  │   ├─ get resources                │  │
│  │   ├─ select options               │  │
│  │   └─ validate configs             │  │
│  │                                   │  │
│  │   WRITE Operations (Lambda)       │  │
│  │   └─ lambda_client.py             │  │
│  └───────────────┬───────────────────┘  │
│                  │                       │
└──────────────────┼───────────────────────┘
                   │
                   │ JSON Payload
                   ▼
          ┌────────────────────┐
          │   AWS LAMBDA       │
          │                    │
          │  create_endpoint() │
          │  get_header_opts() │
          └─────────┬──────────┘
                    │
                    │ boto3 SDK
                    ▼
          ┌────────────────────┐
          │  AWS API GATEWAY   │
          │                    │
          │  ✓ Resources       │
          │  ✓ Methods         │
          │  ✓ Integrations    │
          │  ✓ CORS            │
          └────────────────────┘
```

---

## 📦 Nuevos Módulos Creados

### 1. **lambda_client.py**
**Propósito**: Cliente para invocar Lambda function

**Funciones principales**:
```python
# Obtener opciones de headers dinámicamente
options = lambda_client.get_header_options("auth_headers")

# Crear endpoint vía Lambda
response = lambda_client.create_endpoint(payload)
```

**Configuración**:
```bash
# Variable de entorno (opcional)
export LAMBDA_FUNCTION_NAME="apigateway-resource-creator-ci"

# O editar get_lambda_function_name() en lambda_client.py
```

---

### 2. **header_selector.py**
**Propósito**: Selección interactiva de headers desde opciones de Lambda

**Funciones principales**:
```python
# Mostrar headers disponibles y permitir selección
headers = select_headers_for_auth_type("COGNITO_CUSTOMER")

# Mostrar opciones de integración
integration_config = display_integration_options()
```

**Características**:
- Headers dinámicos desde Lambda (no hardcodeados)
- Marcado visual de headers requeridos
- Opción para agregar headers personalizados
- Fallback a valores por defecto si Lambda no responde

---

### 3. **endpoint_creator_lambda.py**
**Propósito**: Orquestador de creación de endpoints vía Lambda

**Función principal**:
```python
success = create_endpoint_via_lambda(base_config, endpoint_config)
```

**Flujo**:
1. Construir payload Lambda desde configuración local
2. Obtener headers dinámicamente
3. Mostrar resumen de lo que se va a crear
4. Confirmar con usuario
5. Invocar Lambda
6. Mostrar progreso de steps
7. Reportar resultado (success/error)

---

## 🔧 Configuración Necesaria

### 1. Deploy de la Lambda

```bash
cd lambda-apigateway-creator/

# Deploy con SAM
sam deploy --guided \
  --stack-name apigateway-creator-ci \
  --parameter-overrides Environment=ci \
  --capabilities CAPABILITY_IAM
```

### 2. Configurar Nombre de Lambda en Cliente

**Opción A: Variable de entorno**
```bash
export LAMBDA_FUNCTION_NAME="apigateway-resource-creator-ci"
```

**Opción B: Editar lambda_client.py**
```python
def get_lambda_function_name() -> str:
    return "apigateway-resource-creator-prod"  # Cambiar aquí
```

### 3. Permisos IAM del Usuario

El usuario que ejecuta el script necesita:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:apigateway-resource-creator-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "apigateway:GET"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 🚀 Uso del Script Refactorizado

### Workflow Completo

```bash
# 1. Ejecutar script
python3 apiGatewayCreator.py

# 2. Seleccionar fuente de configuración
#    → Cargar perfil existente
#    → Crear nueva configuración

# 3. El script hace READ operations localmente:
#    → Lista APIs disponibles (AWS CLI)
#    → Selecciona authorizers (AWS CLI)
#    → Selecciona Cognito pools (AWS CLI)

# 4. Obtiene headers dinámicos de Lambda:
#    → Lambda retorna opciones de headers
#    → Usuario selecciona/personaliza

# 5. Solicita configuración del endpoint:
#    → Path backend completo
#    → Métodos HTTP

# 6. Crea endpoint vía Lambda:
#    → Envía JSON payload a Lambda
#    → Lambda ejecuta creación en API Gateway
#    → Muestra progreso de steps en tiempo real
```

### Ejemplo de Salida

```
═══════════════════════════════════════════════════════════════════
  HEADERS PARA COGNITO_CUSTOMER
═══════════════════════════════════════════════════════════════════

📋 Headers disponibles para COGNITO_CUSTOMER:
   Para la app o la web

Headers configurados:
  1* Claim-Email
     → Email del usuario desde Cognito
     Default: context.authorizer.claims.email

  2* Claim-User-Id
     → ID del customer desde Cognito
     Default: context.authorizer.claims.custom:customer_id

  3* KNOWN-TOKEN-KEY
     → Token key desde stage variables
     Default: stageVariables.knownTokenKey

→ ¿Deseas agregar headers personalizados? (s/n): n

[SUCCESS] ✓ 3 headers seleccionados

═══════════════════════════════════════════════════════════════════
  CREANDO ENDPOINT VÍA LAMBDA
═══════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════
  RESUMEN DE CREACIÓN
═══════════════════════════════════════════════════════════════════

🌐 API Gateway:
  API ID: abc123xyz
  Stage: ci

📍 Endpoint:
  Path Backend: /discounts/v2/campaigns/{id}
  Path API GW: /v2/campaigns/{id}
  Métodos: GET, POST, PUT, DELETE

🔐 Autenticación:
  Método: AUTHORIZER
  Tipo: COGNITO_CUSTOMER
  Authorizer ID: auth456def

🔗 Integración:
  Backend Host: https://${stageVariables.urlDiscountsPrivate}
  VPC Link Variable: vpcLinkId
  Timeout: 29000ms

📋 Headers: 3 configurados

→ ¿Proceder con la creación? (s/n): s

📤 Enviando request a Lambda...

═══════════════════════════════════════════════════════════════════
  ✅ ENDPOINT CREADO EXITOSAMENTE
═══════════════════════════════════════════════════════════════════

[SUCCESS] Resource ID: res789xyz

📊 Pasos ejecutados:
  ✓ Parse Path
  ✓ Create Resources (created=3, skipped=0)
  ✓ Create Methods (count=4)
  ✓ Configure Integrations
  ✓ Create Cors
  ✓ Verify

[SUCCESS] Endpoint created successfully
```

---

## 🔍 Ventajas de la Nueva Arquitectura

### 1. **Seguridad Mejorada**
- ✅ No más `subprocess.run(shell=True)`
- ✅ Lambda usa boto3 SDK (sin command injection)
- ✅ Permisos IAM granulares por operación

### 2. **Configuración Dinámica**
- ✅ Headers obtenidos de Lambda (no hardcodeados)
- ✅ Fácil agregar nuevos headers sin cambiar cliente
- ✅ Validación centralizada en Lambda

### 3. **Mejor Manejo de Errores**
- ✅ Respuestas estructuradas con steps
- ✅ Errores específicos con códigos
- ✅ Rollback potencial en Lambda

### 4. **Escalabilidad**
- ✅ Lambda puede escalar automáticamente
- ✅ Timeouts configurables (hasta 15 min en Lambda)
- ✅ Logs centralizados en CloudWatch

### 5. **Mantenibilidad**
- ✅ Código más modular
- ✅ Tests más fáciles (mock Lambda)
- ✅ Separación clara: cliente vs servidor

---

## 🧪 Testing

### Test Local de Lambda
```bash
cd lambda-apigateway-creator/

# Test get_header_options
cat > test_headers.json << 'EOF'
{
  "body": "{\"operation\": \"get_header_options\", \"filter\": \"auth_headers\"}"
}
EOF

sam local invoke APIGatewayCreatorFunction --event test_headers.json
```

### Test Integración Completa
```bash
# 1. Deploy Lambda
sam deploy --guided

# 2. Configurar nombre de función
export LAMBDA_FUNCTION_NAME="apigateway-resource-creator-ci"

# 3. Ejecutar cliente
python3 apiGatewayCreator.py

# 4. Verificar en CloudWatch Logs
aws logs tail /aws/lambda/apigateway-resource-creator-ci --follow
```

---

## 📝 Migración desde Versión Anterior

### Cambios en apiGatewayCreator.py

**Antes**:
```python
# Creación directa con AWS CLI
success = create_endpoint_workflow(manager, base_config, endpoint_config)
```

**Ahora**:
```python
# Importar nuevo módulo
from endpoint_creator_lambda import create_endpoint_via_lambda

# Creación vía Lambda
success = create_endpoint_via_lambda(base_config, endpoint_config)
```

### Retrocompatibilidad

- ✅ Perfiles existentes siguen funcionando
- ✅ Configuraciones INI sin cambios
- ✅ Mismos comandos AWS CLI para READ operations
- ⚠️ Requiere Lambda deployed para WRITE operations

---

## 🐛 Troubleshooting

### Error: "Lambda invocation failed"
**Solución**:
```bash
# Verificar que la Lambda existe
aws lambda get-function --function-name apigateway-resource-creator-ci

# Verificar permisos
aws iam get-user

# Test directo
aws lambda invoke \
  --function-name apigateway-resource-creator-ci \
  --payload '{"operation":"get_header_options"}' \
  response.json
```

### Error: "No se pudieron obtener opciones de headers"
**Solución**:
- Lambda usa fallback a valores por defecto
- Verifica logs de Lambda en CloudWatch
- Asegura que header_options.py está en el deployment package

### Error: "RESOURCE_CREATION_FAILED"
**Solución**:
- Revisa logs de Lambda en CloudWatch
- Verifica permisos IAM de la Lambda
- Confirma que API ID es válido

---

## 📚 Próximos Pasos

- [ ] Agregar caché local de header options
- [ ] Implementar retry logic en lambda_client
- [ ] Agregar modo offline (usa solo configuraciones locales)
- [ ] Soporte para múltiples regiones AWS
- [ ] Dashboard web para visualizar endpoints creados

---

## 🔗 Referencias

- [Arquitectura Original](./CLAUDE.md)
- [Lambda README](./lambda-apigateway-creator/README.md)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Boto3 API Gateway Reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html)
