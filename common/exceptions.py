"""
Custom exception classes for the API Gateway Resource Creator.

Define excepciones específicas del dominio para un manejo de errores
más granular y un flujo de control más explícito.
"""


class APIGatewayException(Exception):
    """Base exception for all API Gateway Resource Creator exceptions."""

    pass


class AWSException(APIGatewayException):
    """Raised when AWS CLI execution fails."""

    def __init__(
        self,
        message: str,
        command: str = "",
        returncode: int = 0,
        stderr: str = "",
    ) -> None:
        """
        Initialize AWS exception.

        Args:
            message: Error description.
            command: The AWS CLI command that failed.
            returncode: The command return code.
            stderr: Standard error output from the command.
        """
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        full_message = (
            f"{message}\n"
            f"Command: {command}\n"
            f"Return Code: {returncode}\n"
            f"Error: {stderr}"
            if command
            else message
        )
        super().__init__(full_message)


class ConfigurationException(APIGatewayException):
    """Raised when configuration is invalid or missing."""

    pass


class ProfileException(ConfigurationException):
    """Raised when profile loading/saving fails."""

    pass


class ValidationException(APIGatewayException):
    """Raised when validation fails."""

    pass


class ResourceNotFoundException(APIGatewayException):
    """Raised when a required resource is not found."""

    pass


class UserCancelledException(APIGatewayException):
    """Raised when user cancels an operation."""

    pass


class InputValidationException(ValidationException):
    """Raised when user input validation fails."""

    pass


class PathParsingException(ValidationException):
    """Raised when path parsing fails."""

    pass


class ResourceCreationException(AWSException):
    """Raised when resource creation fails."""

    pass


class MethodCreationException(AWSException):
    """Raised when method creation fails."""

    pass


class IntegrationException(AWSException):
    """Raised when integration configuration fails."""

    pass


class AuthorizerException(ValidationException):
    """Raised when authorizer configuration fails."""

    pass


class HeaderException(ValidationException):
    """Raised when header configuration fails."""

    pass
