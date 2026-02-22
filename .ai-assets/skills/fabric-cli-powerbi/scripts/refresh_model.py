#!/usr/bin/env python3
"""
refresh_model.py - Trigger and monitor semantic model refresh

This script triggers a semantic model refresh in Microsoft Fabric and optionally
waits for completion with configurable timeout.

Usage:
    python refresh_model.py <model> [--wait] [--timeout 300]
    python refresh_model.py Production.Workspace/Sales.SemanticModel --wait --timeout 600

Exit codes:
    0 - Refresh completed successfully (or triggered successfully without --wait)
    1 - Refresh failed or error occurred
"""

import argparse
import json
import re
import subprocess
import sys
import time
from typing import Dict, Any, Optional, Tuple


def run_fab_command(args: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """Execute a fab CLI command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            ["fab"] + args,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", "fab CLI not found in PATH"
    except subprocess.TimeoutExpired:
        return -2, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return -3, "", str(e)


def parse_json_output(output: str) -> Any:
    """Parse JSON output from fab CLI."""
    try:
        return json.loads(output.strip())
    except json.JSONDecodeError:
        return None


def parse_model_path(model_path: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse workspace and model name from path."""
    # Handle format: Workspace.Workspace/Model.SemanticModel or Workspace/Model.SemanticModel
    parts = model_path.split("/")
    if len(parts) != 2:
        return None, None
    
    workspace = parts[0]
    model = parts[1]
    
    # Ensure suffixes
    if not workspace.endswith(".Workspace"):
        workspace = f"{workspace}.Workspace"
    if not model.endswith(".SemanticModel"):
        model = f"{model}.SemanticModel"
    
    return workspace, model


def get_ids_from_path(workspace: str, model: str) -> Tuple[Optional[str], Optional[str]]:
    """Get workspace ID and model ID from names."""
    # Get workspace ID
    exit_code, stdout, stderr = run_fab_command(["get", workspace, "-q", "id", "-f", "json"])
    if exit_code != 0:
        print(f"Error: Failed to get workspace ID: {stderr}", file=sys.stderr)
        return None, None
    
    workspace_id = parse_json_output(stdout)
    if not workspace_id:
        print(f"Error: Could not parse workspace ID", file=sys.stderr)
        return None, None
    
    # Get model ID
    model_path = f"{workspace}/{model}"
    exit_code, stdout, stderr = run_fab_command(["get", model_path, "-q", "id", "-f", "json"])
    if exit_code != 0:
        print(f"Error: Failed to get model ID: {stderr}", file=sys.stderr)
        return None, None
    
    model_id = parse_json_output(stdout)
    if not model_id:
        print(f"Error: Could not parse model ID", file=sys.stderr)
        return None, None
    
    return workspace_id.strip('"'), model_id.strip('"')


def trigger_refresh(workspace_id: str, model_id: str, retry_count: int = 1) -> Dict[str, Any]:
    """Trigger semantic model refresh via Power BI API."""
    result = {
        "status": "unknown",
        "refresh_id": None,
        "polling_endpoint": None,
        "message": ""
    }
    
    # Build request body
    request_body = json.dumps({"retryCount": str(retry_count)})
    
    # Trigger refresh using fab api command
    api_path = f"groups/{workspace_id}/datasets/{model_id}/refreshes"
    exit_code, stdout, stderr = run_fab_command([
        "api", "-A", "powerbi", "-X", "post", api_path,
        "--show_headers", "-i", request_body
    ])
    
    if exit_code != 0:
        result["status"] = "failed"
        result["message"] = stderr.strip() or "Failed to trigger refresh"
        return result
    
    # Parse response
    response = parse_json_output(stdout)
    if not response:
        result["status"] = "failed"
        result["message"] = "Failed to parse API response"
        return result
    
    status_code = response.get("status_code")
    if status_code != 202:
        result["status"] = "failed"
        result["message"] = f"Unexpected status code: {status_code}"
        return result
    
    # Extract polling endpoint from Location header
    headers = response.get("headers", {})
    location = headers.get("Location", "")
    
    if location:
        # Extract the API path from the full URL
        match = re.search(r'https?://[^/]+/v1\.0/myorg/(.+)', location)
        if match:
            result["polling_endpoint"] = match.group(1).strip()
    
    # Fallback to RequestId header
    if not result["polling_endpoint"]:
        request_id = headers.get("RequestId")
        if request_id:
            result["polling_endpoint"] = f"groups/{workspace_id}/datasets/{model_id}/refreshes/{request_id}"
            result["refresh_id"] = request_id
    
    result["status"] = "triggered"
    result["message"] = "Refresh triggered successfully"
    
    return result


def poll_refresh_status(polling_endpoint: str, timeout: int = 300, poll_interval: int = 10) -> Dict[str, Any]:
    """Poll refresh status until completion or timeout."""
    result = {
        "status": "unknown",
        "final_status": None,
        "duration_seconds": 0,
        "message": ""
    }
    
    start_time = time.time()
    
    print(f"\nPolling refresh status (timeout: {timeout}s)...")
    
    while True:
        elapsed = time.time() - start_time
        
        if elapsed > timeout:
            result["status"] = "timeout"
            result["duration_seconds"] = int(elapsed)
            result["message"] = f"Refresh timed out after {timeout} seconds"
            return result
        
        # Get refresh status
        exit_code, stdout, stderr = run_fab_command([
            "api", "-A", "powerbi", polling_endpoint, "--show_headers"
        ])
        
        if exit_code != 0:
            result["status"] = "error"
            result["message"] = stderr.strip() or "Failed to get refresh status"
            return result
        
        response = parse_json_output(stdout)
        if not response:
            result["status"] = "error"
            result["message"] = "Failed to parse status response"
            return result
        
        status_code = response.get("status_code")
        if status_code not in [200, 202]:
            result["status"] = "error"
            result["message"] = f"Unexpected status code: {status_code}"
            return result
        
        # Parse the status text
        status_text = response.get("text", {})
        if isinstance(status_text, str):
            status_text = parse_json_output(status_text) or {}
        
        refresh_status = status_text.get("extendedStatus") or status_text.get("status", "Unknown")
        
        print(f"  Status: {refresh_status} (elapsed: {int(elapsed)}s)")
        
        # Check for completion states
        if refresh_status == "Completed":
            result["status"] = "completed"
            result["final_status"] = refresh_status
            result["duration_seconds"] = int(time.time() - start_time)
            result["message"] = "Refresh completed successfully"
            return result
        
        if refresh_status in ["Failed", "Cancelled", "Disabled", "TimedOut"]:
            result["status"] = "failed"
            result["final_status"] = refresh_status
            result["duration_seconds"] = int(time.time() - start_time)
            result["message"] = f"Refresh ended with status: {refresh_status}"
            
            # Try to get error details
            if "error" in status_text:
                result["error_details"] = status_text["error"]
            
            return result
        
        # Still in progress, wait and poll again
        time.sleep(poll_interval)


def refresh_model(
    model_path: str,
    wait: bool = False,
    timeout: int = 300,
    retry_count: int = 1
) -> Dict[str, Any]:
    """Main function to refresh a semantic model."""
    
    result = {
        "model_path": model_path,
        "wait": wait,
        "timeout": timeout,
        "trigger_result": None,
        "poll_result": None,
        "overall_status": "unknown"
    }
    
    # Parse model path
    workspace, model = parse_model_path(model_path)
    if not workspace or not model:
        result["overall_status"] = "error"
        result["message"] = f"Invalid model path: {model_path}. Expected format: Workspace/Model.SemanticModel"
        return result
    
    print(f"\nModel: {workspace}/{model}")
    
    # Get IDs
    print("Resolving workspace and model IDs...")
    workspace_id, model_id = get_ids_from_path(workspace, model)
    if not workspace_id or not model_id:
        result["overall_status"] = "error"
        result["message"] = "Failed to resolve workspace or model ID"
        return result
    
    result["workspace_id"] = workspace_id
    result["model_id"] = model_id
    
    # Trigger refresh
    print("Triggering refresh...")
    trigger_result = trigger_refresh(workspace_id, model_id, retry_count)
    result["trigger_result"] = trigger_result
    
    if trigger_result["status"] != "triggered":
        result["overall_status"] = "failed"
        result["message"] = trigger_result["message"]
        return result
    
    print(f"✓ {trigger_result['message']}")
    
    if not wait:
        result["overall_status"] = "triggered"
        result["message"] = "Refresh triggered. Use --wait to monitor completion."
        return result
    
    # Poll for completion
    if not trigger_result.get("polling_endpoint"):
        result["overall_status"] = "warning"
        result["message"] = "Refresh triggered but no polling endpoint available"
        return result
    
    poll_result = poll_refresh_status(
        trigger_result["polling_endpoint"],
        timeout=timeout
    )
    result["poll_result"] = poll_result
    
    if poll_result["status"] == "completed":
        result["overall_status"] = "completed"
        result["message"] = f"Refresh completed in {poll_result['duration_seconds']} seconds"
    else:
        result["overall_status"] = "failed"
        result["message"] = poll_result["message"]
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Trigger and monitor semantic model refresh",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python refresh_model.py Production.Workspace/Sales.SemanticModel
    python refresh_model.py Production/Sales.SemanticModel --wait
    python refresh_model.py Dev.Workspace/Model.SemanticModel --wait --timeout 600
    python refresh_model.py "My Workspace/My Model.SemanticModel" --wait --json

Note:
    Without --wait, the script triggers the refresh and exits immediately.
    With --wait, the script polls until completion or timeout.
        """
    )
    parser.add_argument(
        "model",
        help="Semantic model path (format: Workspace/Model.SemanticModel)"
    )
    parser.add_argument(
        "--wait", "-w",
        action="store_true",
        help="Wait for refresh to complete"
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=300,
        help="Timeout in seconds when waiting (default: 300)"
    )
    parser.add_argument(
        "--retry-count", "-r",
        type=int,
        default=1,
        help="Number of retries for the refresh operation (default: 1)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    try:
        result = refresh_model(
            model_path=args.model,
            wait=args.wait,
            timeout=args.timeout,
            retry_count=args.retry_count
        )
        
        # Print summary
        print("\n" + "=" * 50)
        print("REFRESH RESULT")
        print("=" * 50)
        print(f"Model: {result['model_path']}")
        print(f"Status: {result['overall_status'].upper()}")
        print(f"Message: {result.get('message', 'N/A')}")
        
        if result.get("poll_result"):
            print(f"Duration: {result['poll_result'].get('duration_seconds', 'N/A')} seconds")
        
        print("=" * 50)
        
        if args.json:
            print("\n" + json.dumps(result, indent=2))
        
        # Exit code based on status
        success_statuses = ["completed", "triggered"]
        sys.exit(0 if result["overall_status"] in success_statuses else 1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
