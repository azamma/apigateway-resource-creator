"""
Lambda Client for API Gateway Creator.

Handles communication with the Lambda function for write operations.
"""
import json
import subprocess
from typing import Dict, Any, Optional

from common import get_logger

logger = get_logger(__name__)


class LambdaClient:
    """Client for invoking Lambda function."""

    def __init__(self, function_name: str, region: str = "us-east-1"):
        """
        Initialize Lambda client.

        Args:
            function_name: Name of the Lambda function
            region: AWS region (default: us-east-1)
        """
        self.function_name = function_name
        self.region = region

    def invoke(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Invoke Lambda function with payload.

        Args:
            payload: JSON payload to send

        Returns:
            Response from Lambda or None if error
        """
        try:
            payload_json = json.dumps(payload)

            # Use AWS CLI to invoke Lambda
            command = [
                "aws", "lambda", "invoke",
                "--function-name", self.function_name,
                "--region", self.region,
                "--payload", payload_json,
                "--cli-binary-format", "raw-in-base64-out",
                "/tmp/lambda_response.json"
            ]

            logger.debug(f"Invoking Lambda: {self.function_name}")

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                logger.error(f"Lambda invocation failed: {result.stderr}")
                return None

            # Read response from temp file
            with open("/tmp/lambda_response.json", 'r') as f:
                response = json.load(f)

            # Parse body if it's a string
            if "body" in response and isinstance(response["body"], str):
                response["body"] = json.loads(response["body"])

            return response

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Lambda response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error invoking Lambda: {e}")
            return None

    def get_header_options(self, filter_type: str = "all") -> Optional[Dict[str, Any]]:
        """
        Get available header options from Lambda.

        Args:
            filter_type: Type of options to get (all, auth_headers, cors_headers, integration_config)

        Returns:
            Dictionary with available options or None
        """
        payload = {
            "operation": "get_header_options",
            "filter": filter_type
        }

        response = self.invoke(payload)

        if not response:
            return None

        body = response.get("body", {})

        if not body.get("success"):
            logger.error(f"Lambda returned error: {body.get('error')}")
            return None

        return body.get("options", {})

    def create_endpoint(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create API Gateway endpoint via Lambda.

        Args:
            config: Complete endpoint configuration

        Returns:
            Response with steps or None if error
        """
        payload = {
            "operation": "create_endpoint",
            **config
        }

        response = self.invoke(payload)

        if not response:
            return None

        body = response.get("body", {})

        return body


def get_lambda_function_name() -> str:
    """
    Get Lambda function name from environment or config.

    Returns:
        Lambda function name
    """
    import os

    # Check environment variable first
    function_name = os.environ.get("LAMBDA_FUNCTION_NAME")

    if function_name:
        return function_name

    # Default based on environment
    # You can make this configurable via a settings file
    return "apigateway-resource-creator-ci"


# Global instance
_lambda_client: Optional[LambdaClient] = None


def get_lambda_client() -> LambdaClient:
    """
    Get or create Lambda client instance.

    Returns:
        LambdaClient instance
    """
    global _lambda_client

    if _lambda_client is None:
        function_name = get_lambda_function_name()
        _lambda_client = LambdaClient(function_name)
        logger.debug(f"Lambda client initialized: {function_name}")

    return _lambda_client
