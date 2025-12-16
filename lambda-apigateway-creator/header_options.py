"""
Header options provider.

Returns available header configurations for different auth types.
"""


def get_auth_headers_options():
    """
    Get available authentication header options.

    Returns:
        Dict with auth types and their headers
    """
    return {
        "COGNITO_ADMIN": {
            "description": "Para el admin",
            "headers": {
                "Claim-Email": {
                    "default": "context.authorizer.claims.email",
                    "description": "Email del usuario desde Cognito",
                    "required": True
                },
                "Claim-User-Id": {
                    "default": "context.authorizer.claims.custom:admin_id",
                    "description": "ID del admin desde Cognito",
                    "required": True
                },
                "CognitoPool": {
                    "default": "'admin'",
                    "description": "Nombre del pool de Cognito",
                    "required": True
                },
                "KNOWN-TOKEN-KEY": {
                    "default": "stageVariables.knownTokenKey",
                    "description": "Token key desde stage variables",
                    "required": True
                },
                "X-Amzn-Request-Id": {
                    "default": "context.requestId",
                    "description": "ID de la request de AWS",
                    "required": False
                }
            }
        },
        "COGNITO_CUSTOMER": {
            "description": "Para la app o la web",
            "headers": {
                "Claim-Email": {
                    "default": "context.authorizer.claims.email",
                    "description": "Email del usuario desde Cognito",
                    "required": True
                },
                "Claim-User-Id": {
                    "default": "context.authorizer.claims.custom:customer_id",
                    "description": "ID del customer desde Cognito",
                    "required": True
                },
                "CognitoPool": {
                    "default": "'customer'",
                    "description": "Nombre del pool de Cognito",
                    "required": True
                },
                "KNOWN-TOKEN-KEY": {
                    "default": "stageVariables.knownTokenKey",
                    "description": "Token key desde stage variables",
                    "required": True
                },
                "X-Amzn-Request-Id": {
                    "default": "context.requestId",
                    "description": "ID de la request de AWS",
                    "required": False
                }
            }
        },
        "NO_AUTH": {
            "description": "Sin autorización (APIs públicas)",
            "headers": {
                "KNOWN-TOKEN-KEY": {
                    "default": "stageVariables.knownTokenKey",
                    "description": "Token key desde stage variables",
                    "required": False
                },
                "X-Amzn-Request-Id": {
                    "default": "context.requestId",
                    "description": "ID de la request de AWS",
                    "required": False
                }
            }
        },
        "API_KEY": {
            "description": "Autenticación con API Key",
            "headers": {
                "X-Amzn-Request-Id": {
                    "default": "context.requestId",
                    "description": "ID de la request de AWS",
                    "required": False
                }
            }
        }
    }


def get_cors_headers_options():
    """
    Get available CORS header configurations.

    Returns:
        Dict with CORS configurations
    """
    return {
        "DEFAULT": {
            "description": "CORS configuration por defecto",
            "headers": {
                "Access-Control-Allow-Headers": {
                    "default": "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token,X-Api-Version'",
                    "description": "Headers permitidos en CORS"
                },
                "Access-Control-Allow-Methods": {
                    "default": "'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT'",
                    "description": "Métodos HTTP permitidos"
                },
                "Access-Control-Allow-Origin": {
                    "default": "'*'",
                    "description": "Orígenes permitidos (* = todos)"
                }
            }
        },
        "RESTRICTED": {
            "description": "CORS restringido a dominio específico",
            "headers": {
                "Access-Control-Allow-Headers": {
                    "default": "'Content-Type,Authorization'",
                    "description": "Headers permitidos (limitado)"
                },
                "Access-Control-Allow-Methods": {
                    "default": "'GET,POST,OPTIONS'",
                    "description": "Métodos HTTP permitidos (limitado)"
                },
                "Access-Control-Allow-Origin": {
                    "default": "'https://example.com'",
                    "description": "Origen específico permitido"
                }
            }
        }
    }


def get_integration_config_options():
    """
    Get available integration configuration options.

    Returns:
        Dict with integration options
    """
    return {
        "timeout_ms": {
            "default": 29000,
            "min": 50,
            "max": 29000,
            "description": "Timeout de integración en milisegundos"
        },
        "passthrough_behavior": {
            "default": "WHEN_NO_MATCH",
            "options": ["WHEN_NO_MATCH", "WHEN_NO_TEMPLATES", "NEVER"],
            "description": "Comportamiento de passthrough"
        },
        "integration_type": {
            "default": "HTTP_PROXY",
            "options": ["HTTP_PROXY", "HTTP", "AWS_PROXY", "AWS", "MOCK"],
            "description": "Tipo de integración"
        },
        "connection_type": {
            "default": "VPC_LINK",
            "options": ["VPC_LINK", "INTERNET"],
            "description": "Tipo de conexión"
        }
    }


def get_all_options():
    """
    Get all available configuration options.

    Returns:
        Dict with all options
    """
    return {
        "auth_headers": get_auth_headers_options(),
        "cors_headers": get_cors_headers_options(),
        "integration_config": get_integration_config_options()
    }
