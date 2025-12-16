# Lambda: API Gateway Resource Creator

Lambda function que recibe payloads JSON para crear recursos en AWS API Gateway.

## 📋 Descripción

Esta Lambda reemplaza las operaciones de escritura del script `apiGatewayCreator.py`, permitiendo centralizar la creación de recursos en AWS API Gateway a través de un endpoint serverless.

## 🏗️ Arquitectura

```
Client Terminal (read-only) ──────────┐
                                      │
                                      ▼
                              AWS API Gateway
                                      ▲
                                      │
Client Terminal (json) ───► Lambda ──┘
                           (crea recursos)
```

## 📦 Estructura del Proyecto

```
lambda-apigateway-creator/
├── index.py                      # Handler principal
├── api_gateway_operations.py     # Operaciones boto3
├── path_parser.py                # Parser de paths
├── validators.py                 # Validadores de input
├── response_builder.py           # Constructor de respuestas
├── template.yml                  # SAM template
├── buildspec.yml                 # CI/CD config
└── requirements.txt              # Dependencias
```

## 🚀 Deployment

### Prerequisitos

- AWS CLI v2 configurado
- AWS SAM CLI instalado
- Python 3.12
- Permisos IAM para Lambda y API Gateway

### Deploy Manual

```bash
# 1. Instalar dependencias
pip install -r requirements.txt -t .

# 2. Validar template
sam validate --template template.yml

# 3. Build
sam build --template template.yml

# 4. Deploy
sam deploy --guided \
  --stack-name apigateway-creator-ci \
  --parameter-overrides Environment=ci \
  --capabilities CAPABILITY_IAM

# O deploy sin confirmación:
sam deploy \
  --stack-name apigateway-creator-ci \
  --template-file .aws-sam/build/template.yaml \
  --parameter-overrides Environment=ci \
  --capabilities CAPABILITY_IAM \
  --no-confirm-changeset
```

### Deploy con CodeBuild/CodePipeline

El archivo `buildspec.yml` está configurado para CI/CD automático.

**Variables de entorno requeridas:**
- `DEPLOYMENT_BUCKET`: Bucket S3 para artifacts

## 📥 Payload de Entrada

```json
{
  "operation": "create_endpoint",
  "config": {
    "api_id": "abc123xyz",
    "api_name": "discounts-api-ci",
    "stage": "ci"
  },
  "authentication": {
    "method": "AUTHORIZER",
    "authorizer_id": "auth456def",
    "auth_type": "COGNITO_CUSTOMER",
    "cognito_pool": "customer-pool-ci"
  },
  "endpoint": {
    "full_backend_path": "/discounts/v2/campaigns/{id}",
    "api_gateway_path": "/v2/campaigns/{id}",
    "http_methods": ["GET", "POST", "PUT", "DELETE"]
  },
  "integration": {
    "connection_type": "VPC_LINK",
    "connection_variable": "vpcLinkId",
    "backend_host": "https://${stageVariables.urlDiscountsPrivate}",
    "timeout_ms": 29000,
    "passthrough_behavior": "WHEN_NO_MATCH",
    "integration_type": "HTTP_PROXY"
  },
  "headers": {
    "auth_headers": {
      "Claim-Email": "context.authorizer.claims.email",
      "Claim-User-Id": "context.authorizer.claims.custom:customer_id",
      "KNOWN-TOKEN-KEY": "stageVariables.knownTokenKey"
    },
    "custom_headers": {}
  },
  "cors": {
    "enabled": true,
    "type": "DEFAULT",
    "headers": {
      "Access-Control-Allow-Headers": "'Content-Type,Authorization'",
      "Access-Control-Allow-Methods": "'GET,POST,PUT,DELETE,OPTIONS'",
      "Access-Control-Allow-Origin": "'*'"
    }
  }
}
```

## 📤 Respuesta de Salida

### Éxito

```json
{
  "success": true,
  "resource_id": "res789xyz",
  "steps": [
    {"name": "parse_path", "status": "ok"},
    {"name": "create_resources", "status": "ok", "created": 3, "skipped": 0},
    {"name": "create_methods", "status": "ok", "count": 4},
    {"name": "configure_integrations", "status": "ok"},
    {"name": "create_cors", "status": "ok"},
    {"name": "verify", "status": "ok"}
  ],
  "message": "Endpoint created successfully"
}
```

### Error

```json
{
  "success": false,
  "error": "Failed to create resource /v2/campaigns",
  "error_code": "RESOURCE_CREATION_FAILED",
  "failed_step": "create_resources",
  "steps": [
    {"name": "parse_path", "status": "ok"},
    {"name": "create_resources", "status": "failed"}
  ]
}
```

## 🧪 Testing Local

```bash
# Crear evento de prueba
cat > event.json << 'EOF'
{
  "body": "{\"operation\": \"create_endpoint\", ...}"
}
EOF

# Invocar localmente
sam local invoke APIGatewayCreatorFunction --event event.json
```

## 🔐 Permisos IAM Requeridos

La Lambda necesita permisos para:
- ✅ API Gateway (GetResources, CreateResource, PutMethod, PutIntegration, etc.)
- ✅ CloudWatch Logs (CreateLogGroup, CreateLogStream, PutLogEvents)

Ver `template.yml` para la política completa.

## 📊 CloudWatch Logs

Los logs se organizan en:
```
/aws/lambda/apigateway-resource-creator-{environment}
```

Formato de logs:
```
[TIMESTAMP] Start handler
Event body: {...}
Parsed payload for operation: create_endpoint

[STEP 1] Parsing path...
  ✓ Path parsed: 3 segments

[STEP 2] Creating resource hierarchy...
  Resource /v2 already exists: res001
  Created resource /v2/campaigns: res002
  ...
```

## 🐛 Troubleshooting

### Error: "Missing 'config.api_id'"
- Verifica que el payload JSON incluya `config.api_id`

### Error: "RESOURCE_CREATION_FAILED"
- Verifica permisos IAM de la Lambda
- Confirma que el API ID existe en API Gateway

### Error: "INTEGRATION_FAILED"
- Verifica que la stage variable existe
- Confirma que el VPC Link ID es válido

## 📚 Referencias

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [Boto3 API Gateway Reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html)

## 🔄 Próximos Pasos

- [ ] Agregar tests unitarios
- [ ] Implementar retry logic para operaciones AWS
- [ ] Agregar soporte para actualización de recursos existentes
- [ ] Implementar rollback automático en caso de fallo
