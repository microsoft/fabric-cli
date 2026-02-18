#!/usr/bin/env python3
"""
validate_governance.py - Check workspace against governance rules

This script validates a Microsoft Fabric workspace against a set of governance rules
defined in a JSON configuration file.

Usage:
    python validate_governance.py <workspace> --rules <rules.json>
    python validate_governance.py Production.Workspace --rules company-rules.json

Exit codes:
    0 - All governance checks passed
    1 - Governance violations found or error occurred
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
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


def load_rules(rules_file: str) -> Dict[str, Any]:
    """Load governance rules from JSON file."""
    path = Path(rules_file)
    
    if not path.exists():
        raise FileNotFoundError(f"Rules file not found: {rules_file}")
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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


def get_item_labels(workspace: str) -> List[Dict[str, Any]]:
    """Get sensitivity labels for items in workspace."""
    exit_code, stdout, stderr = run_fab_command(["labels", "list", workspace, "-f", "json"])
    
    if exit_code == 0:
        result = parse_json_output(stdout)
        if isinstance(result, list):
            return result
        return []
    return []


class GovernanceValidator:
    """Validates workspace against governance rules."""
    
    def __init__(self, workspace: str, rules: Dict[str, Any], verbose: bool = False):
        self.workspace = ensure_workspace_suffix(workspace)
        self.rules = rules
        self.verbose = verbose
        self.violations: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.passed_checks: List[str] = []
        
        # Cached data
        self.workspace_details: Optional[Dict[str, Any]] = None
        self.permissions: Optional[List[Dict[str, Any]]] = None
        self.items: Optional[List[Dict[str, Any]]] = None
        self.labels: Optional[List[Dict[str, Any]]] = None
    
    def log(self, message: str):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(message, file=sys.stderr)
    
    def add_violation(self, rule: str, message: str, severity: str = "error", details: Any = None):
        """Add a governance violation."""
        self.violations.append({
            "rule": rule,
            "message": message,
            "severity": severity,
            "details": details
        })
    
    def add_warning(self, rule: str, message: str, details: Any = None):
        """Add a governance warning."""
        self.warnings.append({
            "rule": rule,
            "message": message,
            "details": details
        })
    
    def add_passed(self, rule: str):
        """Mark a rule as passed."""
        self.passed_checks.append(rule)
    
    def load_workspace_data(self) -> bool:
        """Load all workspace data needed for validation."""
        self.log(f"Loading workspace data for: {self.workspace}")
        
        # Get workspace details
        self.log("  Fetching workspace details...")
        self.workspace_details = get_workspace_details(self.workspace)
        if "error" in self.workspace_details:
            print(f"Error: Failed to get workspace details: {self.workspace_details['error']}", file=sys.stderr)
            return False
        
        # Get permissions
        self.log("  Fetching permissions...")
        self.permissions = get_workspace_permissions(self.workspace)
        
        # Get items
        self.log("  Fetching items...")
        self.items = get_workspace_items(self.workspace)
        
        # Get labels (optional - may not be available)
        self.log("  Fetching labels...")
        self.labels = get_item_labels(self.workspace)
        
        return True
    
    def validate_capacity_assignment(self):
        """Check if workspace has required capacity assignment."""
        rule_name = "capacity_assignment"
        rule_config = self.rules.get(rule_name, {})
        
        if not rule_config.get("enabled", False):
            return
        
        self.log(f"Checking rule: {rule_name}")
        
        capacity_id = self.workspace_details.get("capacityId")
        
        if rule_config.get("required", False) and not capacity_id:
            self.add_violation(
                rule_name,
                "Workspace must be assigned to a capacity",
                severity="error"
            )
            return
        
        allowed_capacities = rule_config.get("allowed_capacities", [])
        if allowed_capacities and capacity_id not in allowed_capacities:
            self.add_violation(
                rule_name,
                f"Workspace capacity '{capacity_id}' not in allowed list",
                severity="error",
                details={"current": capacity_id, "allowed": allowed_capacities}
            )
            return
        
        self.add_passed(rule_name)
    
    def validate_naming_conventions(self):
        """Check workspace and item naming conventions."""
        rule_name = "naming_conventions"
        rule_config = self.rules.get(rule_name, {})
        
        if not rule_config.get("enabled", False):
            return
        
        self.log(f"Checking rule: {rule_name}")
        
        violations_found = False
        
        # Check workspace name pattern
        workspace_pattern = rule_config.get("workspace_pattern")
        if workspace_pattern:
            workspace_name = self.workspace.replace(".Workspace", "")
            if not re.match(workspace_pattern, workspace_name):
                self.add_violation(
                    rule_name,
                    f"Workspace name '{workspace_name}' does not match pattern '{workspace_pattern}'",
                    severity="error"
                )
                violations_found = True
        
        # Check item name patterns
        item_patterns = rule_config.get("item_patterns", {})
        for item in self.items or []:
            item_type = item.get("type", "")
            item_name = item.get("name", "")
            
            # Check type-specific pattern
            pattern = item_patterns.get(item_type) or item_patterns.get("default")
            if pattern and not re.match(pattern, item_name):
                self.add_violation(
                    rule_name,
                    f"Item '{item_name}' ({item_type}) does not match naming pattern '{pattern}'",
                    severity="warning",
                    details={"item": item_name, "type": item_type, "pattern": pattern}
                )
                violations_found = True
        
        if not violations_found:
            self.add_passed(rule_name)
    
    def validate_sensitivity_labels(self):
        """Check that items have required sensitivity labels."""
        rule_name = "sensitivity_labels"
        rule_config = self.rules.get(rule_name, {})
        
        if not rule_config.get("enabled", False):
            return
        
        self.log(f"Checking rule: {rule_name}")
        
        required = rule_config.get("required", False)
        required_types = rule_config.get("required_item_types", [])
        allowed_labels = rule_config.get("allowed_labels", [])
        
        violations_found = False
        
        # Build a map of items with labels
        labeled_items = {}
        for label_info in self.labels or []:
            item_name = label_info.get("itemName", "")
            labeled_items[item_name] = label_info.get("label", "")
        
        for item in self.items or []:
            item_name = item.get("name", "")
            item_type = item.get("type", "")
            
            # Check if this type requires labels
            if required_types and item_type not in required_types:
                continue
            
            item_label = labeled_items.get(item_name)
            
            # Check if label is required
            if required and not item_label:
                self.add_violation(
                    rule_name,
                    f"Item '{item_name}' ({item_type}) is missing required sensitivity label",
                    severity="error",
                    details={"item": item_name, "type": item_type}
                )
                violations_found = True
            # Check if label is in allowed list
            elif item_label and allowed_labels and item_label not in allowed_labels:
                self.add_violation(
                    rule_name,
                    f"Item '{item_name}' has label '{item_label}' not in allowed list",
                    severity="warning",
                    details={"item": item_name, "label": item_label, "allowed": allowed_labels}
                )
                violations_found = True
        
        if not violations_found:
            self.add_passed(rule_name)
    
    def validate_allowed_item_types(self):
        """Check that workspace only contains allowed item types."""
        rule_name = "allowed_item_types"
        rule_config = self.rules.get(rule_name, {})
        
        if not rule_config.get("enabled", False):
            return
        
        self.log(f"Checking rule: {rule_name}")
        
        allowed_types = rule_config.get("types", [])
        blocked_types = rule_config.get("blocked_types", [])
        
        violations_found = False
        
        for item in self.items or []:
            item_type = item.get("type", "")
            item_name = item.get("name", "")
            
            # Check allowed list
            if allowed_types and item_type not in allowed_types:
                self.add_violation(
                    rule_name,
                    f"Item '{item_name}' has type '{item_type}' not in allowed types",
                    severity="error",
                    details={"item": item_name, "type": item_type, "allowed": allowed_types}
                )
                violations_found = True
            
            # Check blocked list
            if item_type in blocked_types:
                self.add_violation(
                    rule_name,
                    f"Item '{item_name}' has blocked type '{item_type}'",
                    severity="error",
                    details={"item": item_name, "type": item_type}
                )
                violations_found = True
        
        if not violations_found:
            self.add_passed(rule_name)
    
    def validate_required_permissions(self):
        """Check that required permissions are configured."""
        rule_name = "required_permissions"
        rule_config = self.rules.get(rule_name, {})
        
        if not rule_config.get("enabled", False):
            return
        
        self.log(f"Checking rule: {rule_name}")
        
        required_principals = rule_config.get("required_principals", [])
        max_admins = rule_config.get("max_admins")
        require_group_access = rule_config.get("require_group_access", False)
        
        violations_found = False
        
        # Build permission map
        current_permissions = {}
        admin_count = 0
        has_group_access = False
        
        for perm in self.permissions or []:
            principal = perm.get("principal", {})
            principal_id = principal.get("id", "")
            principal_type = principal.get("type", "")
            role = perm.get("role", "")
            
            current_permissions[principal_id] = role
            
            if role == "Admin":
                admin_count += 1
            
            if principal_type == "Group":
                has_group_access = True
        
        # Check required principals
        for required in required_principals:
            principal_id = required.get("principal_id")
            required_role = required.get("role")
            
            current_role = current_permissions.get(principal_id)
            if not current_role:
                self.add_violation(
                    rule_name,
                    f"Required principal '{principal_id}' is not assigned to workspace",
                    severity="error",
                    details=required
                )
                violations_found = True
            elif required_role and current_role != required_role:
                self.add_warning(
                    rule_name,
                    f"Principal '{principal_id}' has role '{current_role}' but '{required_role}' is required",
                    details={"principal": principal_id, "current": current_role, "required": required_role}
                )
        
        # Check max admins
        if max_admins is not None and admin_count > max_admins:
            self.add_violation(
                rule_name,
                f"Workspace has {admin_count} admins, maximum allowed is {max_admins}",
                severity="warning",
                details={"current": admin_count, "max": max_admins}
            )
            violations_found = True
        
        # Check group access requirement
        if require_group_access and not has_group_access:
            self.add_violation(
                rule_name,
                "Workspace must have at least one group with access (no direct user access only)",
                severity="warning"
            )
            violations_found = True
        
        if not violations_found:
            self.add_passed(rule_name)
    
    def validate_domain_membership(self):
        """Check workspace domain membership."""
        rule_name = "domain_membership"
        rule_config = self.rules.get(rule_name, {})
        
        if not rule_config.get("enabled", False):
            return
        
        self.log(f"Checking rule: {rule_name}")
        
        required = rule_config.get("required", False)
        allowed_domains = rule_config.get("allowed_domains", [])
        
        domain_id = self.workspace_details.get("domainId")
        
        if required and not domain_id:
            self.add_violation(
                rule_name,
                "Workspace must be assigned to a domain",
                severity="error"
            )
            return
        
        if allowed_domains and domain_id and domain_id not in allowed_domains:
            self.add_violation(
                rule_name,
                f"Workspace domain '{domain_id}' not in allowed list",
                severity="error",
                details={"current": domain_id, "allowed": allowed_domains}
            )
            return
        
        self.add_passed(rule_name)
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all governance validations."""
        if not self.load_workspace_data():
            return {
                "workspace": self.workspace,
                "status": "error",
                "message": "Failed to load workspace data"
            }
        
        # Run all validators
        self.validate_capacity_assignment()
        self.validate_naming_conventions()
        self.validate_sensitivity_labels()
        self.validate_allowed_item_types()
        self.validate_required_permissions()
        self.validate_domain_membership()
        
        # Determine overall status
        has_errors = any(v["severity"] == "error" for v in self.violations)
        status = "fail" if has_errors else ("pass_with_warnings" if self.violations else "pass")
        
        return {
            "workspace": self.workspace,
            "status": status,
            "rules_file": self.rules.get("_source", "unknown"),
            "summary": {
                "passed": len(self.passed_checks),
                "violations": len(self.violations),
                "warnings": len(self.warnings)
            },
            "passed_checks": self.passed_checks,
            "violations": self.violations,
            "warnings": self.warnings
        }


def create_sample_rules() -> Dict[str, Any]:
    """Create a sample governance rules file."""
    return {
        "_description": "Sample Fabric governance rules configuration",
        "_version": "1.0",
        "capacity_assignment": {
            "enabled": True,
            "required": True,
            "allowed_capacities": []
        },
        "naming_conventions": {
            "enabled": True,
            "workspace_pattern": "^[A-Z][a-zA-Z0-9_-]+$",
            "item_patterns": {
                "default": "^[A-Za-z][A-Za-z0-9_-]*$",
                "SemanticModel": "^[A-Z][a-zA-Z0-9_-]+$",
                "Report": "^[A-Z][a-zA-Z0-9_-]+Report$"
            }
        },
        "sensitivity_labels": {
            "enabled": True,
            "required": False,
            "required_item_types": ["SemanticModel", "Report"],
            "allowed_labels": []
        },
        "allowed_item_types": {
            "enabled": False,
            "types": [],
            "blocked_types": []
        },
        "required_permissions": {
            "enabled": True,
            "required_principals": [],
            "max_admins": 5,
            "require_group_access": False
        },
        "domain_membership": {
            "enabled": False,
            "required": False,
            "allowed_domains": []
        }
    }


def print_report(result: Dict[str, Any], output_format: str, output_file: Optional[str] = None):
    """Print validation report."""
    if output_format == "json":
        output = json.dumps(result, indent=2)
    else:
        # Text format
        lines = []
        lines.append("=" * 60)
        lines.append("GOVERNANCE VALIDATION REPORT")
        lines.append("=" * 60)
        lines.append(f"Workspace: {result['workspace']}")
        lines.append(f"Status: {result['status'].upper()}")
        lines.append("")
        
        summary = result.get("summary", {})
        lines.append(f"Passed: {summary.get('passed', 0)}")
        lines.append(f"Violations: {summary.get('violations', 0)}")
        lines.append(f"Warnings: {summary.get('warnings', 0)}")
        lines.append("")
        
        if result.get("passed_checks"):
            lines.append("PASSED CHECKS:")
            for check in result["passed_checks"]:
                lines.append(f"  ✓ {check}")
            lines.append("")
        
        if result.get("violations"):
            lines.append("VIOLATIONS:")
            for v in result["violations"]:
                severity_icon = "✗" if v["severity"] == "error" else "⚠"
                lines.append(f"  {severity_icon} [{v['rule']}] {v['message']}")
            lines.append("")
        
        if result.get("warnings"):
            lines.append("WARNINGS:")
            for w in result["warnings"]:
                lines.append(f"  ⚠ [{w['rule']}] {w['message']}")
            lines.append("")
        
        lines.append("=" * 60)
        output = "\n".join(lines)
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Report written to: {output_file}", file=sys.stderr)
    else:
        print(output)


def main():
    parser = argparse.ArgumentParser(
        description="Validate workspace against governance rules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python validate_governance.py Production.Workspace --rules company-rules.json
    python validate_governance.py MyWorkspace --rules rules.json -f json
    python validate_governance.py Production.Workspace --rules rules.json -o report.json
    python validate_governance.py --create-sample-rules > sample-rules.json
        """
    )
    
    parser.add_argument(
        "workspace",
        nargs="?",
        help="Workspace name or path (e.g., 'MyWorkspace' or 'MyWorkspace.Workspace')"
    )
    
    parser.add_argument(
        "--rules",
        required=False,
        help="Path to governance rules JSON file"
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
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--create-sample-rules",
        action="store_true",
        help="Output a sample governance rules file"
    )
    
    args = parser.parse_args()
    
    # Handle sample rules generation
    if args.create_sample_rules:
        print(json.dumps(create_sample_rules(), indent=2))
        return 0
    
    # Validate required arguments
    if not args.workspace:
        parser.error("workspace is required unless --create-sample-rules is specified")
    
    if not args.rules:
        parser.error("--rules is required")
    
    # Load rules
    try:
        rules = load_rules(args.rules)
        rules["_source"] = args.rules
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in rules file: {e}", file=sys.stderr)
        return 1
    
    # Run validation
    validator = GovernanceValidator(args.workspace, rules, verbose=args.verbose)
    result = validator.validate_all()
    
    # Output report
    print_report(result, args.format, args.output)
    
    # Return exit code based on status
    if result["status"] == "error":
        return 1
    elif result["status"] == "fail":
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
