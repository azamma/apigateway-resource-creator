"""
Response builder for Lambda responses.

Constructs standardized JSON responses.
"""
import json


def success_response(resource_id, steps, warnings=None):
    """
    Build a success response.

    Args:
        resource_id: Created resource ID
        steps: List of execution steps
        warnings: Optional list of warning messages

    Returns:
        Lambda response dict
    """
    body = {
        "success": True,
        "resource_id": resource_id,
        "steps": steps,
        "message": "Endpoint created successfully"
    }

    if warnings:
        body["warnings"] = warnings

    return {
        "statusCode": 200,
        "body": json.dumps(body),
        "headers": {
            "Content-Type": "application/json"
        }
    }


def error_response(error_message, error_code, steps=None):
    """
    Build an error response.

    Args:
        error_message: Error description
        error_code: Error code
        steps: Optional list of completed steps

    Returns:
        Lambda response dict
    """
    body = {
        "success": False,
        "error": error_message,
        "error_code": error_code
    }

    if steps:
        body["steps"] = steps
        body["failed_step"] = steps[-1]["name"] if steps else None

    return {
        "statusCode": 400,
        "body": json.dumps(body),
        "headers": {
            "Content-Type": "application/json"
        }
    }
