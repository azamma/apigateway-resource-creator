"""
Lambda Handler for API Gateway Resource Creator.

Receives JSON payload from client terminal and creates resources in AWS API Gateway.
"""
import json
import traceback
from datetime import datetime

import api_gateway_operations
import header_options
import response_builder
import validators
from path_parser import PathParser


def handler(event, context):
    """
    Main Lambda handler for creating API Gateway resources.

    Args:
        event: Lambda event containing the JSON payload
        context: Lambda context object

    Returns:
        Response with status and execution steps
    """
    print("=" * 70)
    print(f"[{datetime.now().isoformat()}] Start handler")
    print(f"Event body: {event.get('body', 'NO BODY')}")

    try:
        # Parse and validate request
        payload = _parse_request(event)
        print(f"Parsed payload for operation: {payload.get('operation')}")

        # Validate payload structure
        validation_result = validators.validate_payload(payload)
        if not validation_result["valid"]:
            print(f"Validation failed: {validation_result['error']}")
            return response_builder.error_response(
                validation_result["error"],
                "INVALID_PAYLOAD"
            )

        # Execute operation
        operation = payload.get("operation", "create_endpoint")

        if operation == "create_endpoint":
            result = _create_endpoint(payload)
        elif operation == "get_header_options":
            result = _get_header_options(payload)
        else:
            return response_builder.error_response(
                f"Unknown operation: {operation}",
                "UNKNOWN_OPERATION"
            )

        print(f"[{datetime.now().isoformat()}] End handler - Success")
        return result

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"ERROR: {str(e)}")
        print(f"Traceback:\n{error_trace}")

        return response_builder.error_response(
            str(e),
            "INTERNAL_ERROR"
        )


def _parse_request(event):
    """
    Parse the Lambda event and extract JSON payload.

    Args:
        event: Lambda event

    Returns:
        Parsed JSON payload
    """
    body = event.get('body', '{}')

    if isinstance(body, str):
        return json.loads(body)

    return body


def _create_endpoint(payload):
    """
    Create API Gateway endpoint with all configurations.

    Args:
        payload: Validated JSON payload

    Returns:
        Response with execution steps
    """
    steps = []

    try:
        # Step 1: Parse path
        print("\n[STEP 1] Parsing path...")
        parser = PathParser(payload["endpoint"]["api_gateway_path"])
        segments = parser.get_segments()

        steps.append({
            "name": "parse_path",
            "status": "ok"
        })
        print(f"  ✓ Path parsed: {len(segments)} segments")

        # Step 2: Create resource hierarchy
        print("\n[STEP 2] Creating resource hierarchy...")
        api_id = payload["config"]["api_id"]

        resource_result = api_gateway_operations.create_resource_hierarchy(
            api_id,
            segments,
            payload["endpoint"]["api_gateway_path"]
        )

        if not resource_result["success"]:
            steps.append({
                "name": "create_resources",
                "status": "failed"
            })
            return response_builder.error_response(
                resource_result["error"],
                "RESOURCE_CREATION_FAILED",
                steps
            )

        final_resource_id = resource_result["resource_id"]
        created_count = resource_result.get("created", 0)
        skipped_count = resource_result.get("skipped", 0)

        steps.append({
            "name": "create_resources",
            "status": "ok",
            "created": created_count,
            "skipped": skipped_count
        })
        print(f"  ✓ Resources created: {created_count}, skipped: {skipped_count}")

        # Step 3: Create HTTP methods
        print("\n[STEP 3] Creating HTTP methods...")
        http_methods = payload["endpoint"]["http_methods"]

        methods_result = api_gateway_operations.create_http_methods(
            api_id,
            final_resource_id,
            http_methods,
            payload
        )

        if not methods_result["success"]:
            steps.append({
                "name": "create_methods",
                "status": "failed"
            })
            return response_builder.error_response(
                methods_result["error"],
                "METHOD_CREATION_FAILED",
                steps
            )

        steps.append({
            "name": "create_methods",
            "status": "ok",
            "count": len(http_methods)
        })
        print(f"  ✓ Methods created: {len(http_methods)}")

        # Step 4: Configure integrations
        print("\n[STEP 4] Configuring integrations...")
        integration_result = api_gateway_operations.configure_integrations(
            api_id,
            final_resource_id,
            http_methods,
            payload
        )

        if not integration_result["success"]:
            steps.append({
                "name": "configure_integrations",
                "status": "failed"
            })
            return response_builder.error_response(
                integration_result["error"],
                "INTEGRATION_FAILED",
                steps
            )

        steps.append({
            "name": "configure_integrations",
            "status": "ok"
        })
        print(f"  ✓ Integrations configured")

        # Step 5: Create CORS (OPTIONS method)
        print("\n[STEP 5] Creating CORS configuration...")
        cors_result = api_gateway_operations.create_cors_method(
            api_id,
            final_resource_id,
            payload.get("cors", {})
        )

        if not cors_result["success"]:
            steps.append({
                "name": "create_cors",
                "status": "failed"
            })
            # CORS failure is not critical, continue
            print(f"  ⚠ CORS creation failed (non-critical): {cors_result.get('error')}")
        else:
            steps.append({
                "name": "create_cors",
                "status": "ok"
            })
            print(f"  ✓ CORS configured")

        # Step 6: Verify integrations
        print("\n[STEP 6] Verifying integrations...")
        verify_result = api_gateway_operations.verify_integrations(
            api_id,
            final_resource_id,
            http_methods + ["OPTIONS"]
        )

        if not verify_result["success"]:
            steps.append({
                "name": "verify",
                "status": "failed"
            })
            return response_builder.error_response(
                "Integration verification failed",
                "VERIFICATION_FAILED",
                steps
            )

        steps.append({
            "name": "verify",
            "status": "ok"
        })
        print(f"  ✓ All integrations verified")

        # Success response
        warnings = []
        if skipped_count > 0:
            warnings.append(f"{skipped_count} resources already existed")

        return response_builder.success_response(
            final_resource_id,
            steps,
            warnings
        )

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"ERROR in _create_endpoint: {str(e)}")
        print(f"Traceback:\n{error_trace}")

        steps.append({
            "name": "error",
            "status": "failed"
        })

        return response_builder.error_response(
            str(e),
            "ENDPOINT_CREATION_ERROR",
            steps
        )


def _get_header_options(payload):
    """
    Get available header and configuration options.

    Args:
        payload: Validated JSON payload

    Returns:
        Response with available options
    """
    print("\n[GET HEADER OPTIONS] Processing request...")

    try:
        filter_param = payload.get("filter", "all")

        if filter_param == "auth_headers":
            options = {"auth_headers": header_options.get_auth_headers_options()}
        elif filter_param == "cors_headers":
            options = {"cors_headers": header_options.get_cors_headers_options()}
        elif filter_param == "integration_config":
            options = {"integration_config": header_options.get_integration_config_options()}
        else:
            options = header_options.get_all_options()

        print(f"  ✓ Returned {len(options)} option categories")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "options": options
            }),
            "headers": {
                "Content-Type": "application/json"
            }
        }

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"ERROR in _get_header_options: {str(e)}")
        print(f"Traceback:\n{error_trace}")

        return response_builder.error_response(
            str(e),
            "HEADER_OPTIONS_ERROR"
        )
