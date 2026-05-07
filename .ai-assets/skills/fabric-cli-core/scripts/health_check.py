#!/usr/bin/env python3
"""
health_check.py - Verify CLI installation, auth status, and connectivity

This script performs comprehensive health checks for the Fabric CLI environment:
- Verifies fab CLI is installed and accessible
- Checks authentication status
- Validates workspace connectivity
- Optionally verifies specific workspace access

Usage:
    python health_check.py [--workspace WS] [--json]

Exit codes:
    0 - All checks passed (healthy)
    1 - One or more checks failed (issues found)
"""

import argparse
import json
import subprocess
import sys
from typing import Dict, Any, Optional


def run_fab_command(args: list[str], timeout: int = 30) -> tuple[int, str, str]:
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


def check_cli_installed() -> Dict[str, Any]:
    """Check if fab CLI is installed and accessible."""
    check = {
        "check": "cli_installed",
        "description": "Verify fab CLI is installed and accessible",
        "status": "unknown",
        "details": {}
    }
    
    exit_code, stdout, stderr = run_fab_command(["--version"])
    
    if exit_code == 0:
        check["status"] = "pass"
        check["details"]["version"] = stdout.strip()
    elif exit_code == -1:
        check["status"] = "fail"
        check["details"]["error"] = "fab CLI not found in PATH. Please install the Fabric CLI."
    else:
        check["status"] = "fail"
        check["details"]["error"] = stderr or "Unable to determine CLI version"
    
    return check


def check_auth_status() -> Dict[str, Any]:
    """Check authentication status with Fabric."""
    check = {
        "check": "auth_status",
        "description": "Verify authentication to Microsoft Fabric",
        "status": "unknown",
        "details": {}
    }
    
    exit_code, stdout, stderr = run_fab_command(["auth", "status"])
    
    if exit_code == 0:
        check["status"] = "pass"
        # Parse auth status output
        lines = stdout.strip().split("\n")
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                check["details"][key.strip().lower().replace(" ", "_")] = value.strip()
    else:
        check["status"] = "fail"
        check["details"]["error"] = stderr.strip() or "Not authenticated. Run 'fab auth login' to authenticate."
    
    return check


def check_workspace_connectivity() -> Dict[str, Any]:
    """Check if we can list at least one workspace."""
    check = {
        "check": "workspace_connectivity",
        "description": "Verify ability to list workspaces",
        "status": "unknown",
        "details": {}
    }
    
    # Try to list workspaces (limit to 1 for quick check)
    exit_code, stdout, stderr = run_fab_command(["ls", "/", "-q", "[0].name"])
    
    if exit_code == 0 and stdout.strip():
        check["status"] = "pass"
        check["details"]["sample_workspace"] = stdout.strip().strip('"')
        check["details"]["message"] = "Successfully retrieved workspace list"
    elif exit_code == 0:
        check["status"] = "warn"
        check["details"]["message"] = "No workspaces found. You may not have access to any workspaces."
    else:
        check["status"] = "fail"
        check["details"]["error"] = stderr.strip() or "Unable to list workspaces"
    
    return check


def check_specific_workspace(workspace: str) -> Dict[str, Any]:
    """Check access to a specific workspace."""
    check = {
        "check": "specific_workspace",
        "description": f"Verify access to workspace: {workspace}",
        "status": "unknown",
        "details": {"workspace": workspace}
    }
    
    # Ensure workspace has .Workspace suffix
    if not workspace.endswith(".Workspace"):
        workspace = f"{workspace}.Workspace"
    
    exit_code, stdout, stderr = run_fab_command(["exists", workspace])
    
    if exit_code == 0:
        check["status"] = "pass"
        check["details"]["message"] = f"Workspace '{workspace}' is accessible"
    else:
        check["status"] = "fail"
        check["details"]["error"] = stderr.strip() or f"Unable to access workspace '{workspace}'"
    
    return check


def run_health_checks(workspace: Optional[str] = None) -> Dict[str, Any]:
    """Run all health checks and return results."""
    results = {
        "overall_status": "healthy",
        "checks": []
    }
    
    # Required checks
    cli_check = check_cli_installed()
    results["checks"].append(cli_check)
    
    # Only proceed with other checks if CLI is installed
    if cli_check["status"] == "pass":
        auth_check = check_auth_status()
        results["checks"].append(auth_check)
        
        # Only check connectivity if authenticated
        if auth_check["status"] == "pass":
            connectivity_check = check_workspace_connectivity()
            results["checks"].append(connectivity_check)
            
            # Check specific workspace if provided
            if workspace:
                workspace_check = check_specific_workspace(workspace)
                results["checks"].append(workspace_check)
    
    # Determine overall status
    statuses = [c["status"] for c in results["checks"]]
    if "fail" in statuses:
        results["overall_status"] = "unhealthy"
    elif "warn" in statuses:
        results["overall_status"] = "degraded"
    
    return results


def print_human_readable(results: Dict[str, Any]) -> None:
    """Print results in human-readable format."""
    status_symbols = {
        "pass": "✓",
        "fail": "✗",
        "warn": "⚠",
        "unknown": "?"
    }
    
    print("\n" + "=" * 60)
    print("FABRIC CLI HEALTH CHECK")
    print("=" * 60)
    
    for check in results["checks"]:
        symbol = status_symbols.get(check["status"], "?")
        status_color = {
            "pass": "",
            "fail": "",
            "warn": "",
            "unknown": ""
        }.get(check["status"], "")
        
        print(f"\n{symbol} {check['description']}")
        print(f"  Status: {check['status'].upper()}")
        
        for key, value in check["details"].items():
            print(f"  {key}: {value}")
    
    print("\n" + "-" * 60)
    overall = results["overall_status"].upper()
    print(f"OVERALL STATUS: {overall}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Verify Fabric CLI installation, authentication, and connectivity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python health_check.py
    python health_check.py --workspace Production
    python health_check.py --json
    python health_check.py --workspace Production.Workspace --json
        """
    )
    parser.add_argument(
        "--workspace", "-w",
        help="Specific workspace to verify access (optional)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    results = run_health_checks(workspace=args.workspace)
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_human_readable(results)
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_status"] == "healthy" else 1)


if __name__ == "__main__":
    main()
