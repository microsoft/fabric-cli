#!/usr/bin/env python3
"""
rebind_report.py - Rebind report to different semantic model

This script changes the semantic model connection for a Power BI report in
Microsoft Fabric.

Usage:
    python rebind_report.py <report> --model <new-model>
    python rebind_report.py Production.Workspace/SalesReport.Report --model Production.Workspace/NewSales.SemanticModel

Exit codes:
    0 - Report successfully rebound to new model
    1 - Rebind failed or error occurred
"""

import argparse
import json
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


def parse_item_path(path: str, item_type: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse workspace and item name from path."""
    parts = path.split("/")
    if len(parts) != 2:
        return None, None
    
    workspace = parts[0]
    item = parts[1]
    
    # Ensure workspace suffix
    if not workspace.endswith(".Workspace"):
        workspace = f"{workspace}.Workspace"
    
    # Ensure item suffix
    suffix = f".{item_type}"
    if not item.endswith(suffix):
        item = f"{item}{suffix}"
    
    return workspace, item


def check_path_exists(path: str) -> bool:
    """Check if path exists."""
    exit_code, _, _ = run_fab_command(["exists", path])
    return exit_code == 0


def get_item_details(path: str) -> Dict[str, Any]:
    """Get item details."""
    exit_code, stdout, stderr = run_fab_command(["get", path, "-f", "json"])
    
    if exit_code == 0:
        return parse_json_output(stdout) or {"error": "Failed to parse item details"}
    return {"error": stderr.strip() or "Failed to get item details"}


def get_item_id(path: str) -> Optional[str]:
    """Get item ID from path."""
    exit_code, stdout, stderr = run_fab_command(["get", path, "-q", "id", "-f", "json"])
    
    if exit_code == 0:
        result = parse_json_output(stdout)
        if isinstance(result, str):
            return result.strip('"')
        return result
    return None


def get_report_datasource(report_path: str) -> Dict[str, Any]:
    """Get the current datasource configuration for a report."""
    exit_code, stdout, stderr = run_fab_command(["get", report_path, "-f", "json"])
    
    if exit_code == 0:
        details = parse_json_output(stdout) or {}
        return {
            "current_model": details.get("semanticModelId") or details.get("datasetId"),
            "workspace_id": details.get("workspaceId"),
            "details": details
        }
    return {"error": stderr}


def rebind_report(workspace_id: str, report_id: str, new_model_id: str, 
                  new_model_workspace_id: Optional[str] = None) -> Dict[str, Any]:
    """Rebind report to a new semantic model using the API."""
    
    result = {
        "status": "unknown",
        "message": "",
        "report_id": report_id,
        "new_model_id": new_model_id
    }
    
    # Build the API request body
    request_body = {
        "datasetId": new_model_id
    }
    
    # If model is in different workspace, include workspace ID
    if new_model_workspace_id and new_model_workspace_id != workspace_id:
        request_body["datasetWorkspaceId"] = new_model_workspace_id
    
    # Use the API command to rebind
    # POST /groups/{workspaceId}/reports/{reportId}/Rebind
    api_path = f"/groups/{workspace_id}/reports/{report_id}/Rebind"
    
    exit_code, stdout, stderr = run_fab_command([
        "api", "post", api_path,
        "-b", json.dumps(request_body),
        "--api-version", "v1.0",
        "-f", "json"
    ], timeout=60)
    
    if exit_code == 0:
        result["status"] = "success"
        result["message"] = "Report successfully rebound to new semantic model"
    else:
        # Check for specific error conditions
        if "already bound" in stderr.lower() or "same dataset" in stderr.lower():
            result["status"] = "success"
            result["message"] = "Report is already bound to the specified model"
        else:
            result["status"] = "failed"
            result["message"] = stderr.strip() or "Failed to rebind report"
    
    return result


def verify_rebind(report_path: str, expected_model_id: str) -> bool:
    """Verify that rebind was successful."""
    time.sleep(2)  # Give it a moment to propagate
    
    datasource = get_report_datasource(report_path)
    current_model = datasource.get("current_model")
    
    return current_model == expected_model_id


def print_result(result: Dict[str, Any], output_format: str, output_file: Optional[str] = None):
    """Print rebind result."""
    if output_format == "json":
        output = json.dumps(result, indent=2)
    else:
        # Text format
        lines = []
        lines.append("=" * 60)
        lines.append("REPORT REBIND RESULT")
        lines.append("=" * 60)
        lines.append(f"Report: {result.get('report_path', 'Unknown')}")
        lines.append(f"Target Model: {result.get('model_path', 'Unknown')}")
        lines.append("")
        
        status = result.get("status", "unknown")
        if status == "success":
            lines.append("✓ REBIND SUCCESSFUL")
            lines.append(f"  {result.get('message', '')}")
        else:
            lines.append("✗ REBIND FAILED")
            lines.append(f"  {result.get('message', 'Unknown error')}")
        
        if result.get("verified"):
            lines.append("")
            lines.append("✓ Verification: Report is now connected to the new model")
        elif result.get("verified") is False:
            lines.append("")
            lines.append("⚠ Verification: Could not confirm rebind (may need time to propagate)")
        
        if result.get("previous_model"):
            lines.append("")
            lines.append(f"Previous Model ID: {result['previous_model']}")
        
        lines.append("")
        lines.append("=" * 60)
        output = "\n".join(lines)
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Result written to: {output_file}", file=sys.stderr)
    else:
        print(output)


def main():
    parser = argparse.ArgumentParser(
        description="Rebind report to different semantic model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python rebind_report.py Production.Workspace/SalesReport.Report --model Production.Workspace/NewSales.SemanticModel
    python rebind_report.py MyWorkspace/Report --model MyWorkspace/Model -f json
    python rebind_report.py Dev.Workspace/TestReport.Report --model Prod.Workspace/ProdModel.SemanticModel --verify
        """
    )
    
    parser.add_argument(
        "report",
        help="Report path (e.g., 'MyWorkspace.Workspace/MyReport.Report')"
    )
    
    parser.add_argument(
        "--model",
        required=True,
        help="New semantic model path (e.g., 'MyWorkspace.Workspace/MyModel.SemanticModel')"
    )
    
    parser.add_argument(
        "-f", "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: stdout)"
    )
    
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify rebind was successful after operation"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    args = parser.parse_args()
    
    # Parse report path
    report_workspace, report_name = parse_item_path(args.report, "Report")
    if not report_workspace or not report_name:
        print(f"Error: Invalid report path: {args.report}", file=sys.stderr)
        print("Expected format: Workspace.Workspace/Report.Report", file=sys.stderr)
        return 1
    
    report_path = f"{report_workspace}/{report_name}"
    
    # Parse model path
    model_workspace, model_name = parse_item_path(args.model, "SemanticModel")
    if not model_workspace or not model_name:
        print(f"Error: Invalid model path: {args.model}", file=sys.stderr)
        print("Expected format: Workspace.Workspace/Model.SemanticModel", file=sys.stderr)
        return 1
    
    model_path = f"{model_workspace}/{model_name}"
    
    if args.verbose:
        print(f"Report: {report_path}", file=sys.stderr)
        print(f"Target Model: {model_path}", file=sys.stderr)
    
    # Check report exists
    if not check_path_exists(report_path):
        print(f"Error: Report does not exist: {report_path}", file=sys.stderr)
        return 1
    
    # Check model exists
    if not check_path_exists(model_path):
        print(f"Error: Semantic model does not exist: {model_path}", file=sys.stderr)
        return 1
    
    # Get current datasource info
    if args.verbose:
        print("Getting current report configuration...", file=sys.stderr)
    
    current_datasource = get_report_datasource(report_path)
    if "error" in current_datasource:
        print(f"Warning: Could not get current datasource: {current_datasource['error']}", file=sys.stderr)
    
    # Get IDs
    if args.verbose:
        print("Getting item IDs...", file=sys.stderr)
    
    # Get report workspace ID and report ID
    report_workspace_id = get_item_id(report_workspace)
    report_id = get_item_id(report_path)
    
    if not report_workspace_id or not report_id:
        print("Error: Could not get report workspace or report ID", file=sys.stderr)
        return 1
    
    # Get model workspace ID and model ID
    model_workspace_id = get_item_id(model_workspace)
    model_id = get_item_id(model_path)
    
    if not model_workspace_id or not model_id:
        print("Error: Could not get model workspace or model ID", file=sys.stderr)
        return 1
    
    if args.verbose:
        print(f"Report Workspace ID: {report_workspace_id}", file=sys.stderr)
        print(f"Report ID: {report_id}", file=sys.stderr)
        print(f"Model Workspace ID: {model_workspace_id}", file=sys.stderr)
        print(f"Model ID: {model_id}", file=sys.stderr)
    
    result = {
        "report_path": report_path,
        "model_path": model_path,
        "report_id": report_id,
        "model_id": model_id,
        "previous_model": current_datasource.get("current_model"),
        "status": "unknown",
        "message": ""
    }
    
    # Dry run mode
    if args.dry_run:
        result["status"] = "dry_run"
        result["message"] = "Would rebind report to specified model (dry run, no changes made)"
        print_result(result, args.format, args.output)
        return 0
    
    # Perform rebind
    if args.verbose:
        print("Rebinding report to new model...", file=sys.stderr)
    
    rebind_result = rebind_report(
        report_workspace_id, 
        report_id, 
        model_id,
        model_workspace_id if model_workspace_id != report_workspace_id else None
    )
    
    result["status"] = rebind_result["status"]
    result["message"] = rebind_result["message"]
    
    # Verify if requested
    if args.verify and rebind_result["status"] == "success":
        if args.verbose:
            print("Verifying rebind...", file=sys.stderr)
        
        verified = verify_rebind(report_path, model_id)
        result["verified"] = verified
    
    # Output result
    print_result(result, args.format, args.output)
    
    # Return exit code
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
