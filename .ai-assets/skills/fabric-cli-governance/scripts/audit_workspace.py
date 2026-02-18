#!/usr/bin/env python3
"""
audit_workspace.py - Generate comprehensive workspace audit report

This script generates a comprehensive audit report for a Microsoft Fabric workspace,
including permissions, item inventory, capacity assignment, and more.

Usage:
    python audit_workspace.py <workspace> -o <report.json>
    python audit_workspace.py Production.Workspace -o audit_report.json

Exit codes:
    0 - Audit completed successfully
    1 - Error during audit
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional


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
    """Parse JSON output from fab CLI, handling potential formatting issues."""
    try:
        return json.loads(output.strip())
    except json.JSONDecodeError:
        return None


def ensure_workspace_suffix(workspace: str) -> str:
    """Ensure workspace name has .Workspace suffix."""
    if not workspace.endswith(".Workspace"):
        return f"{workspace}.Workspace"
    return workspace


def get_workspace_details(workspace: str) -> Dict[str, Any]:
    """Get workspace metadata."""
    exit_code, stdout, stderr = run_fab_command(["get", workspace, "-f", "json"])
    
    if exit_code == 0:
        return parse_json_output(stdout) or {"error": "Failed to parse workspace details"}
    return {"error": stderr.strip() or "Failed to get workspace details"}


def get_workspace_permissions(workspace: str) -> List[Dict[str, Any]]:
    """Get all workspace permissions."""
    exit_code, stdout, stderr = run_fab_command(["acl", "get", workspace, "-f", "json"])
    
    if exit_code == 0:
        result = parse_json_output(stdout)
        if isinstance(result, list):
            return result
        return []
    return []


def get_workspace_items(workspace: str) -> List[Dict[str, Any]]:
    """Get all items in the workspace."""
    exit_code, stdout, stderr = run_fab_command(["ls", workspace, "-l", "-f", "json"])
    
    if exit_code == 0:
        result = parse_json_output(stdout)
        if isinstance(result, list):
            return result
        return []
    return []


def get_item_type_summary(items: List[Dict[str, Any]]) -> Dict[str, int]:
    """Summarize items by type."""
    type_counts = {}
    for item in items:
        item_type = item.get("type", "Unknown")
        type_counts[item_type] = type_counts.get(item_type, 0) + 1
    return type_counts


def get_capacity_info(workspace_details: Dict[str, Any]) -> Dict[str, Any]:
    """Extract capacity information from workspace details."""
    capacity_info = {
        "capacity_id": workspace_details.get("capacityId"),
        "capacity_assigned": workspace_details.get("capacityId") is not None
    }
    return capacity_info


def check_item_labels(workspace: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Check sensitivity labels on items."""
    labeled_items = []
    unlabeled_items = []
    
    for item in items:
        item_name = item.get("name", "Unknown")
        item_type = item.get("type", "Unknown")
        item_path = f"{workspace}/{item_name}.{item_type}"
        
        # Try to get label info (this may not be available for all items)
        exit_code, stdout, stderr = run_fab_command(["get", item_path, "-q", "sensitivityLabel", "-f", "json"])
        
        if exit_code == 0 and stdout.strip() and stdout.strip() != "null":
            labeled_items.append({
                "name": item_name,
                "type": item_type,
                "label": parse_json_output(stdout)
            })
        else:
            unlabeled_items.append({
                "name": item_name,
                "type": item_type
            })
    
    return {
        "total_items": len(items),
        "labeled_count": len(labeled_items),
        "unlabeled_count": len(unlabeled_items),
        "labeled_items": labeled_items,
        "unlabeled_items": unlabeled_items
    }


def generate_audit_report(workspace: str, check_labels: bool = False) -> Dict[str, Any]:
    """Generate comprehensive audit report for workspace."""
    workspace = ensure_workspace_suffix(workspace)
    
    report = {
        "audit_metadata": {
            "workspace": workspace,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "audit_version": "1.0.0"
        },
        "workspace_details": {},
        "permissions": {
            "summary": {},
            "details": []
        },
        "items": {
            "summary": {},
            "by_type": {},
            "details": []
        },
        "capacity": {},
        "labels": {},
        "issues": []
    }
    
    print(f"Auditing workspace: {workspace}")
    
    # Get workspace details
    print("  Fetching workspace details...")
    workspace_details = get_workspace_details(workspace)
    if "error" in workspace_details:
        report["issues"].append({
            "severity": "high",
            "message": f"Failed to get workspace details: {workspace_details['error']}"
        })
        report["workspace_details"] = {"error": workspace_details["error"]}
    else:
        report["workspace_details"] = workspace_details
        report["capacity"] = get_capacity_info(workspace_details)
    
    # Get permissions
    print("  Fetching permissions...")
    permissions = get_workspace_permissions(workspace)
    report["permissions"]["details"] = permissions
    report["permissions"]["summary"] = {
        "total_principals": len(permissions),
        "by_role": {}
    }
    
    for perm in permissions:
        role = perm.get("role", "Unknown")
        report["permissions"]["summary"]["by_role"][role] = \
            report["permissions"]["summary"]["by_role"].get(role, 0) + 1
    
    # Get items
    print("  Fetching items...")
    items = get_workspace_items(workspace)
    report["items"]["details"] = items
    report["items"]["summary"]["total_items"] = len(items)
    report["items"]["by_type"] = get_item_type_summary(items)
    
    # Check labels (optional - can be slow)
    if check_labels:
        print("  Checking sensitivity labels...")
        report["labels"] = check_item_labels(workspace, items)
    else:
        report["labels"] = {"note": "Label check skipped. Use --check-labels to include."}
    
    # Check for potential issues
    if not report["capacity"].get("capacity_assigned"):
        report["issues"].append({
            "severity": "medium",
            "message": "Workspace is not assigned to a capacity"
        })
    
    if report["permissions"]["summary"]["total_principals"] == 0:
        report["issues"].append({
            "severity": "high",
            "message": "No permissions found for workspace"
        })
    
    print(f"  Audit complete. Found {len(report['issues'])} issue(s).")
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Generate comprehensive workspace audit report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python audit_workspace.py Production.Workspace -o audit_report.json
    python audit_workspace.py Dev.Workspace -o audit.json --check-labels
    python audit_workspace.py "My Workspace" -o report.json
        """
    )
    parser.add_argument(
        "workspace",
        help="Workspace name or path to audit"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output file path for the audit report (JSON)"
    )
    parser.add_argument(
        "--check-labels",
        action="store_true",
        help="Include sensitivity label check (can be slow for large workspaces)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print report to stdout in addition to file"
    )
    
    args = parser.parse_args()
    
    try:
        report = generate_audit_report(args.workspace, check_labels=args.check_labels)
        
        # Write to file
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nAudit report saved to: {args.output}")
        
        if args.json:
            print("\n" + json.dumps(report, indent=2))
        
        # Print summary
        print("\n" + "=" * 50)
        print("AUDIT SUMMARY")
        print("=" * 50)
        print(f"Workspace: {report['audit_metadata']['workspace']}")
        print(f"Total Items: {report['items']['summary'].get('total_items', 0)}")
        print(f"Total Principals: {report['permissions']['summary'].get('total_principals', 0)}")
        print(f"Capacity Assigned: {report['capacity'].get('capacity_assigned', 'Unknown')}")
        print(f"Issues Found: {len(report['issues'])}")
        
        if report["issues"]:
            print("\nIssues:")
            for issue in report["issues"]:
                print(f"  [{issue['severity'].upper()}] {issue['message']}")
        
        print("=" * 50)
        
        sys.exit(0 if len(report["issues"]) == 0 else 1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
