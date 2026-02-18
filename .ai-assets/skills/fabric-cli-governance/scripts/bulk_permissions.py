#!/usr/bin/env python3
"""
bulk_permissions.py - Apply permissions from CSV/JSON file

This script applies workspace permissions in bulk from a structured input file.
It supports CSV and JSON formats and provides dry-run capability.

Usage:
    python bulk_permissions.py <workspace> -i <perms.csv>
    python bulk_permissions.py Production.Workspace -i permissions.csv --dry-run

Input CSV format:
    principal,role,principalType
    user@company.com,Contributor,User
    DataTeam@company.com,Viewer,Group

Input JSON format:
    [
        {"principal": "user@company.com", "role": "Contributor", "principalType": "User"},
        {"principal": "DataTeam@company.com", "role": "Viewer", "principalType": "Group"}
    ]

Exit codes:
    0 - All permissions applied successfully
    1 - Some permissions failed to apply
"""

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List


# Valid roles for workspace permissions
VALID_ROLES = ["Admin", "Member", "Contributor", "Viewer"]

# Valid principal types
VALID_PRINCIPAL_TYPES = ["User", "Group", "ServicePrincipal"]


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


def ensure_workspace_suffix(workspace: str) -> str:
    """Ensure workspace name has .Workspace suffix."""
    if not workspace.endswith(".Workspace"):
        return f"{workspace}.Workspace"
    return workspace


def check_workspace_exists(workspace: str) -> bool:
    """Check if workspace exists."""
    exit_code, _, _ = run_fab_command(["exists", workspace])
    return exit_code == 0


def load_permissions_csv(file_path: str) -> List[Dict[str, str]]:
    """Load permissions from CSV file."""
    permissions = []
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names (handle case variations)
            normalized = {}
            for key, value in row.items():
                key_lower = key.lower().strip()
                if key_lower in ["principal", "principalid", "principal_id"]:
                    normalized["principal"] = value.strip()
                elif key_lower in ["role", "rolename", "role_name"]:
                    normalized["role"] = value.strip()
                elif key_lower in ["principaltype", "principal_type", "type"]:
                    normalized["principalType"] = value.strip()
            
            if normalized.get("principal") and normalized.get("role"):
                permissions.append(normalized)
    
    return permissions


def load_permissions_json(file_path: str) -> List[Dict[str, str]]:
    """Load permissions from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "permissions" in data:
        return data["permissions"]
    else:
        raise ValueError("JSON must be an array or object with 'permissions' array")


def load_permissions(file_path: str) -> List[Dict[str, str]]:
    """Load permissions from file (auto-detect format)."""
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    suffix = path.suffix.lower()
    
    if suffix == ".csv":
        return load_permissions_csv(file_path)
    elif suffix == ".json":
        return load_permissions_json(file_path)
    else:
        # Try JSON first, then CSV
        try:
            return load_permissions_json(file_path)
        except (json.JSONDecodeError, ValueError):
            return load_permissions_csv(file_path)


def validate_permission(perm: Dict[str, str], index: int) -> List[str]:
    """Validate a permission entry. Returns list of errors."""
    errors = []
    
    if not perm.get("principal"):
        errors.append(f"Row {index + 1}: Missing 'principal' field")
    
    if not perm.get("role"):
        errors.append(f"Row {index + 1}: Missing 'role' field")
    elif perm["role"] not in VALID_ROLES:
        errors.append(f"Row {index + 1}: Invalid role '{perm['role']}'. Valid roles: {', '.join(VALID_ROLES)}")
    
    principal_type = perm.get("principalType", "User")
    if principal_type not in VALID_PRINCIPAL_TYPES:
        errors.append(f"Row {index + 1}: Invalid principalType '{principal_type}'. Valid types: {', '.join(VALID_PRINCIPAL_TYPES)}")
    
    return errors


def get_current_permissions(workspace: str) -> List[Dict[str, Any]]:
    """Get current workspace permissions."""
    exit_code, stdout, stderr = run_fab_command(["acl", "get", workspace, "-f", "json"])
    
    if exit_code == 0:
        try:
            result = json.loads(stdout.strip())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
    
    return []


def apply_permission(workspace: str, principal: str, role: str, principal_type: str = "User") -> Dict[str, Any]:
    """Apply a single permission to the workspace."""
    result = {
        "principal": principal,
        "role": role,
        "principalType": principal_type,
        "status": "unknown",
        "message": ""
    }
    
    # Build the acl set command
    cmd = ["acl", "set", workspace, "-p", principal, "-r", role, "-t", principal_type, "-f"]
    
    exit_code, stdout, stderr = run_fab_command(cmd)
    
    if exit_code == 0:
        result["status"] = "success"
        result["message"] = f"Permission set: {principal} -> {role}"
    else:
        result["status"] = "failed"
        result["message"] = stderr.strip() or "Failed to set permission"
    
    return result


def bulk_apply_permissions(
    workspace: str,
    permissions: List[Dict[str, str]],
    dry_run: bool = False,
    skip_validation: bool = False
) -> Dict[str, Any]:
    """Apply permissions in bulk to the workspace."""
    
    workspace = ensure_workspace_suffix(workspace)
    
    report = {
        "workspace": workspace,
        "dry_run": dry_run,
        "total_permissions": len(permissions),
        "validation_errors": [],
        "results": [],
        "summary": {
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
    }
    
    # Validate all permissions first
    if not skip_validation:
        print("Validating permissions...")
        for i, perm in enumerate(permissions):
            errors = validate_permission(perm, i)
            report["validation_errors"].extend(errors)
        
        if report["validation_errors"]:
            print(f"  Found {len(report['validation_errors'])} validation error(s)")
            for error in report["validation_errors"]:
                print(f"    - {error}")
            return report
        
        print(f"  All {len(permissions)} permission(s) validated successfully")
    
    # Check workspace exists
    print(f"\nVerifying workspace: {workspace}")
    if not check_workspace_exists(workspace):
        print(f"Error: Workspace '{workspace}' does not exist or is not accessible")
        report["validation_errors"].append(f"Workspace not found: {workspace}")
        return report
    print("  Workspace found")
    
    # Get current permissions for comparison
    current_perms = get_current_permissions(workspace)
    current_lookup = {p.get("principal", {}).get("id", ""): p.get("role") for p in current_perms}
    
    if dry_run:
        print(f"\n[DRY RUN] Would apply the following permissions:")
        for perm in permissions:
            principal = perm["principal"]
            role = perm["role"]
            principal_type = perm.get("principalType", "User")
            print(f"  {principal} ({principal_type}) -> {role}")
        return report
    
    # Apply each permission
    print(f"\nApplying {len(permissions)} permission(s)...")
    for perm in permissions:
        principal = perm["principal"]
        role = perm["role"]
        principal_type = perm.get("principalType", "User")
        
        print(f"\n  Setting permission: {principal} -> {role}")
        result = apply_permission(workspace, principal, role, principal_type)
        report["results"].append(result)
        
        if result["status"] == "success":
            report["summary"]["success"] += 1
            print(f"    ✓ {result['message']}")
        else:
            report["summary"]["failed"] += 1
            print(f"    ✗ {result['message']}")
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Apply permissions from CSV/JSON file to a workspace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python bulk_permissions.py Production.Workspace -i permissions.csv
    python bulk_permissions.py Production.Workspace -i permissions.json --dry-run
    python bulk_permissions.py "My Workspace" -i perms.csv

Input CSV format:
    principal,role,principalType
    user@company.com,Contributor,User
    DataTeam@company.com,Viewer,Group
    12345678-1234-1234-1234-123456789abc,Admin,ServicePrincipal

Input JSON format:
    [
        {"principal": "user@company.com", "role": "Contributor", "principalType": "User"},
        {"principal": "DataTeam@company.com", "role": "Viewer", "principalType": "Group"}
    ]

Valid Roles:
    Admin, Member, Contributor, Viewer

Valid Principal Types:
    User, Group, ServicePrincipal
        """
    )
    parser.add_argument(
        "workspace",
        help="Workspace name or path to apply permissions to"
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input file path (CSV or JSON)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip validation of permission entries"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    try:
        # Load permissions from file
        print(f"Loading permissions from: {args.input}")
        permissions = load_permissions(args.input)
        print(f"  Loaded {len(permissions)} permission(s)")
        
        if not permissions:
            print("No permissions found in input file")
            sys.exit(1)
        
        # Apply permissions
        report = bulk_apply_permissions(
            workspace=args.workspace,
            permissions=permissions,
            dry_run=args.dry_run,
            skip_validation=args.skip_validation
        )
        
        # Print summary
        print("\n" + "=" * 50)
        print("BULK PERMISSIONS SUMMARY")
        print("=" * 50)
        print(f"Workspace: {report['workspace']}")
        print(f"Dry Run: {report['dry_run']}")
        print(f"Total Permissions: {report['total_permissions']}")
        
        if report["validation_errors"]:
            print(f"Validation Errors: {len(report['validation_errors'])}")
        else:
            print(f"\nResults:")
            print(f"  Success: {report['summary']['success']}")
            print(f"  Failed: {report['summary']['failed']}")
            print(f"  Skipped: {report['summary']['skipped']}")
        
        print("=" * 50)
        
        if args.json:
            print("\n" + json.dumps(report, indent=2))
        
        # Exit code based on failures
        has_errors = len(report["validation_errors"]) > 0 or report["summary"]["failed"] > 0
        sys.exit(1 if has_errors else 0)
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
