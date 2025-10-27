"""
Data models for API Gateway Resource Creator.

Utiliza dataclasses (PEP 557) para definir estructuras de datos
tipadas, inmutables y bien documentadas.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .constants import AuthType


@dataclass(frozen=True)
class APIConfig:
    """
    Configuration for API Gateway and authorization.

    Atributos:
        api_id: REST API ID en AWS.
        authorizer_id: Cognito authorizer ID en API Gateway.
        connection_variable: Nombre de la variable de stage para VPC Link.
        cognito_pool: Nombre del Cognito User Pool.
        backend_host: URL del backend (puede contener stage variables).
        auth_type: Tipo de autorización (ADMIN, CUSTOMER, NO_AUTH).
        cors_type: Tipo de CORS configuration.
    """

    api_id: str
    authorizer_id: str
    connection_variable: str
    cognito_pool: str
    backend_host: str
    auth_type: AuthType
    cors_type: str = "DEFAULT"

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if not self.api_id:
            raise ValueError("api_id cannot be empty")
        if not self.authorizer_id:
            raise ValueError("authorizer_id cannot be empty")
        if not self.connection_variable:
            raise ValueError("connection_variable cannot be empty")
        if not self.cognito_pool:
            raise ValueError("cognito_pool cannot be empty")
        if not self.backend_host:
            raise ValueError("backend_host cannot be empty")


@dataclass
class EndpointConfig:
    """
    Configuration for creating an endpoint.

    Atributos:
        http_methods: Lista de métodos HTTP a crear.
        full_backend_path: Path completo del backend (ej: /service/v1/users/{id}).
        custom_headers: Headers personalizados adicionales (opcional).
    """

    http_methods: List[str]
    full_backend_path: str
    custom_headers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate endpoint configuration."""
        if not self.http_methods:
            raise ValueError("At least one HTTP method must be specified")
        if not self.full_backend_path:
            raise ValueError("full_backend_path cannot be empty")

    @property
    def api_gateway_path(self) -> str:
        """
        Derive API Gateway path by removing first segment.

        Returns:
            Path for API Gateway resource (without service name).

        Example:
            full_backend_path="/discounts/v1/items" -> "/v1/items"
        """
        parts = self.full_backend_path.strip("/").split("/")
        if len(parts) > 1:
            return "/" + "/".join(parts[1:])
        return self.full_backend_path


@dataclass(frozen=True)
class MethodSpec:
    """
    Specification for an HTTP method.

    Atributos:
        method: HTTP method name (GET, POST, PUT, DELETE, PATCH).
        timeout_ms: Integration timeout in milliseconds.
        passthrough_behavior: Passthrough behavior (WHEN_NO_MATCH).
        integration_type: Integration type (HTTP_PROXY).
        connection_type: Connection type (VPC_LINK).
        response_status_code: Success response status code.
    """

    method: str
    timeout_ms: int = 29000
    passthrough_behavior: str = "WHEN_NO_MATCH"
    integration_type: str = "HTTP_PROXY"
    connection_type: str = "VPC_LINK"
    response_status_code: str = "200"

    def __post_init__(self) -> None:
        """Validate method specification."""
        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"}
        if self.method not in valid_methods:
            raise ValueError(f"Invalid method: {self.method}")
        if self.timeout_ms <= 0:
            raise ValueError("timeout_ms must be positive")


@dataclass(frozen=True)
class AWSResource:
    """
    Representation of an AWS API Gateway resource.

    Atributos:
        id: Resource ID en API Gateway.
        path: Full path of the resource.
        parent_id: Parent resource ID.
    """

    id: str
    path: str
    parent_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate resource data."""
        if not self.id:
            raise ValueError("Resource id cannot be empty")
        if not self.path:
            raise ValueError("Resource path cannot be empty")


@dataclass(frozen=True)
class ValidationResult:
    """
    Result of a validation operation.

    Atributos:
        is_valid: Whether validation passed.
        message: Validation message or error description.
        details: Additional validation details.
    """

    is_valid: bool
    message: str
    details: Dict[str, bool] = field(default_factory=dict)

    @classmethod
    def success(cls, message: str = "Validation passed") -> "ValidationResult":
        """
        Create a successful validation result.

        Args:
            message: Success message.

        Returns:
            Successful ValidationResult.
        """
        return cls(is_valid=True, message=message)

    @classmethod
    def failure(cls, message: str, details: Optional[Dict[str, bool]] = None) -> "ValidationResult":
        """
        Create a failed validation result.

        Args:
            message: Failure message.
            details: Optional validation details.

        Returns:
            Failed ValidationResult.
        """
        return cls(
            is_valid=False,
            message=message,
            details=details or {},
        )


@dataclass(frozen=True)
class HeaderSpec:
    """
    Specification for an HTTP header.

    Atributos:
        name: Header name.
        value: Header value (may contain context variables).
        required: Whether header is mandatory.
    """

    name: str
    value: str
    required: bool = False

    def __post_init__(self) -> None:
        """Validate header specification."""
        if not self.name:
            raise ValueError("Header name cannot be empty")
        if not self.value:
            raise ValueError("Header value cannot be empty")

    def to_aws_integration_header(self) -> tuple[str, str]:
        """
        Convert to AWS integration request header format.

        Returns:
            Tuple of (integration.request.header.NAME, value).
        """
        aws_name = f"integration.request.header.{self.name}"
        return (aws_name, self.value)
