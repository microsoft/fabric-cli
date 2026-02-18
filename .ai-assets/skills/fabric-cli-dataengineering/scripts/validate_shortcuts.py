#!/usr/bin/env python3
"""
validate_shortcuts.py - Verify all shortcuts are accessible

This script validates all shortcuts in a lakehouse, checking that targets exist
and are accessible.

Usage:
    python validate_shortcuts.py <lakehouse>
    python validate_shortcuts.py DataPlatform.Workspace/Silver.Lakehouse

Exit codes:
    0 - All shortcuts are valid and accessible
    1 - One or more shortcuts have issues
"""

import argparse
import json
import subprocess
import sys
from typing import Dict, Any, List, Optional


def run_fab_command(args: list[str], timeout: int = 120) -> tuple[int, str, str]:
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


def ensure_lakehouse_suffix(path: str) -> str:
    """Ensure path has .Lakehouse suffix if needed."""
    if "/" not in path:
        return path
    
    parts = path.split("/")
    for i, part in enumerate(parts):
        if "." in part:
            continue
        # Check if this looks like a lakehouse name
        if i > 0 and parts[i-1].endswith(".Workspace"):
            parts[i] = f"{part}.Lakehouse"
            break
    
    return "/".join(parts)


def check_path_exists(path: str) -> bool:
    """Check if path exists."""
    exit_code, _, _ = run_fab_command(["exists", path])
    return exit_code == 0


def parse_lakehouse_path(path: str) -> Dict[str, Optional[str]]:
    """Parse lakehouse path into components."""
    result = {
        "workspace": None,
        "lakehouse": None,
        "full_path": path
    }
    
    parts = path.split("/")
    
    for part in parts:
        if part.endswith(".Workspace"):
            result["workspace"] = part
        elif part.endswith(".Lakehouse"):
            result["lakehouse"] = part
            if result["workspace"]:
                result["lakehouse_path"] = f"{result['workspace']}/{part}"
    
    return result


def list_shortcuts(lakehouse_path: str) -> List[Dict[str, Any]]:
    """List all shortcuts in a lakehouse."""
    shortcuts = []
    
    # Check Tables folder
    tables_path = f"{lakehouse_path}/Tables"
    exit_code, stdout, stderr = run_fab_command(["ls", tables_path, "-l", "-f", "json"])
    
    if exit_code == 0:
        items = parse_json_output(stdout) or []
        for item in items:
            if item.get("type") == "Shortcut":
                item["location"] = "Tables"
                item["full_path"] = f"{tables_path}/{item.get('name', '')}"
                shortcuts.append(item)
    
    # Check Files folder
    files_path = f"{lakehouse_path}/Files"
    exit_code, stdout, stderr = run_fab_command(["ls", files_path, "-l", "-f", "json"])
    
    if exit_code == 0:
        items = parse_json_output(stdout) or []
        for item in items:
            if item.get("type") == "Shortcut":
                item["location"] = "Files"
                item["full_path"] = f"{files_path}/{item.get('name', '')}"
                shortcuts.append(item)
    
    # Also check for shortcuts using the shortcut-specific command
    exit_code, stdout, stderr = run_fab_command(["ln", "list", lakehouse_path, "-f", "json"])
    
    if exit_code == 0:
        ln_shortcuts = parse_json_output(stdout) or []
        # Merge with existing list, avoiding duplicates
        existing_names = {s.get("name") for s in shortcuts}
        for s in ln_shortcuts:
            if s.get("name") not in existing_names:
                shortcuts.append(s)
    
    return shortcuts


def get_shortcut_details(shortcut_path: str) -> Dict[str, Any]:
    """Get detailed information about a shortcut."""
    exit_code, stdout, stderr = run_fab_command(["get", shortcut_path, "-f", "json"])
    
    if exit_code == 0:
        return parse_json_output(stdout) or {}
    return {"error": stderr}


def validate_shortcut(shortcut: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """Validate a single shortcut."""
    result = {
        "name": shortcut.get("name", "Unknown"),
        "location": shortcut.get("location", "Unknown"),
        "path": shortcut.get("full_path", ""),
        "status": "unknown",
        "target": None,
        "target_type": None,
        "checks": []
    }
    
    # Get shortcut target information
    shortcut_path = shortcut.get("full_path", "")
    if shortcut_path:
        details = get_shortcut_details(shortcut_path)
        
        if "error" in details:
            result["status"] = "error"
            result["checks"].append({
                "check": "get_details",
                "passed": False,
                "message": f"Failed to get shortcut details: {details['error']}"
            })
            return result
        
        # Extract target information
        target = details.get("target") or details.get("targetPath")
        target_type = details.get("targetType") or details.get("type", "")
        
        result["target"] = target
        result["target_type"] = target_type
        
        # Check 1: Target path is defined
        if target:
            result["checks"].append({
                "check": "target_defined",
                "passed": True,
                "message": f"Target is defined: {target}"
            })
        else:
            result["status"] = "invalid"
            result["checks"].append({
                "check": "target_defined",
                "passed": False,
                "message": "No target path defined for shortcut"
            })
            return result
        
        # Check 2: Target exists (for internal shortcuts)
        if target_type in ["OneLake", "Internal", "Lakehouse", "Warehouse"]:
            if verbose:
                print(f"  Checking if target exists: {target}", file=sys.stderr)
            
            target_exists = check_path_exists(target)
            if target_exists:
                result["checks"].append({
                    "check": "target_exists",
                    "passed": True,
                    "message": f"Target exists: {target}"
                })
            else:
                result["status"] = "broken"
                result["checks"].append({
                    "check": "target_exists",
                    "passed": False,
                    "message": f"Target does not exist: {target}"
                })
                return result
        
        # Check 3: Try to list contents (verify access)
        if verbose:
            print(f"  Checking shortcut accessibility...", file=sys.stderr)
        
        exit_code, stdout, stderr = run_fab_command(["ls", shortcut_path, "-f", "json"], timeout=30)
        
        if exit_code == 0:
            result["checks"].append({
                "check": "accessible",
                "passed": True,
                "message": "Shortcut content is accessible"
            })
        else:
            # Could be permission issue or broken shortcut
            result["status"] = "inaccessible"
            result["checks"].append({
                "check": "accessible",
                "passed": False,
                "message": f"Cannot access shortcut content: {stderr.strip()}"
            })
            return result
        
        # All checks passed
        result["status"] = "valid"
    
    return result


def print_validation_report(results: Dict[str, Any], output_format: str, 
                           output_file: Optional[str] = None):
    """Print validation report."""
    if output_format == "json":
        output = json.dumps(results, indent=2)
    else:
        # Text format
        lines = []
        lines.append("=" * 70)
        lines.append("SHORTCUT VALIDATION REPORT")
        lines.append("=" * 70)
        lines.append(f"Lakehouse: {results['lakehouse']}")
        lines.append("")
        
        summary = results.get("summary", {})
        lines.append(f"Total shortcuts: {summary.get('total', 0)}")
        lines.append(f"Valid: {summary.get('valid', 0)}")
        lines.append(f"Broken: {summary.get('broken', 0)}")
        lines.append(f"Inaccessible: {summary.get('inaccessible', 0)}")
        lines.append(f"Invalid: {summary.get('invalid', 0)}")
        lines.append(f"Errors: {summary.get('errors', 0)}")
        lines.append("")
        
        # Group by status
        shortcuts = results.get("shortcuts", [])
        
        valid_shortcuts = [s for s in shortcuts if s["status"] == "valid"]
        problem_shortcuts = [s for s in shortcuts if s["status"] != "valid"]
        
        if valid_shortcuts:
            lines.append("VALID SHORTCUTS:")
            for s in valid_shortcuts:
                target_info = f" -> {s['target']}" if s.get('target') else ""
                lines.append(f"  ✓ {s['name']} ({s['location']}){target_info}")
            lines.append("")
        
        if problem_shortcuts:
            lines.append("PROBLEM SHORTCUTS:")
            for s in problem_shortcuts:
                status_icon = {
                    "broken": "✗",
                    "inaccessible": "⚠",
                    "invalid": "?",
                    "error": "!"
                }.get(s["status"], "?")
                
                lines.append(f"  {status_icon} {s['name']} ({s['location']}) - {s['status'].upper()}")
                
                # Show failed checks
                for check in s.get("checks", []):
                    if not check["passed"]:
                        lines.append(f"      └─ {check['message']}")
            lines.append("")
        
        if not shortcuts:
            lines.append("No shortcuts found in this lakehouse.")
            lines.append("")
        
        # Overall status
        lines.append("-" * 70)
        if summary.get("broken", 0) > 0 or summary.get("invalid", 0) > 0:
            lines.append("STATUS: FAILED - Some shortcuts have issues that need attention")
        elif summary.get("inaccessible", 0) > 0:
            lines.append("STATUS: WARNING - Some shortcuts may have access issues")
        elif summary.get("total", 0) == 0:
            lines.append("STATUS: OK - No shortcuts to validate")
        else:
            lines.append("STATUS: PASSED - All shortcuts are valid and accessible")
        lines.append("=" * 70)
        
        output = "\n".join(lines)
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Report written to: {output_file}", file=sys.stderr)
    else:
        print(output)


def main():
    parser = argparse.ArgumentParser(
        description="Verify all shortcuts in a lakehouse are accessible",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python validate_shortcuts.py DataPlatform.Workspace/Silver.Lakehouse
    python validate_shortcuts.py MyWorkspace.Workspace/Bronze.Lakehouse -f json
    python validate_shortcuts.py Production.Workspace/Gold.Lakehouse -o report.json
        """
    )
    
    parser.add_argument(
        "lakehouse",
        help="Lakehouse path (e.g., 'MyWorkspace.Workspace/MyLakehouse.Lakehouse')"
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
    
    args = parser.parse_args()
    
    # Parse and validate lakehouse path
    lakehouse_path = ensure_lakehouse_suffix(args.lakehouse)
    path_info = parse_lakehouse_path(lakehouse_path)
    
    if not path_info.get("lakehouse_path"):
        print(f"Error: Invalid lakehouse path: {args.lakehouse}", file=sys.stderr)
        print("Expected format: Workspace.Workspace/Lakehouse.Lakehouse", file=sys.stderr)
        return 1
    
    lakehouse_full_path = path_info["lakehouse_path"]
    
    if args.verbose:
        print(f"Validating shortcuts in: {lakehouse_full_path}", file=sys.stderr)
    
    # Check lakehouse exists
    if not check_path_exists(lakehouse_full_path):
        print(f"Error: Lakehouse does not exist: {lakehouse_full_path}", file=sys.stderr)
        return 1
    
    # List all shortcuts
    if args.verbose:
        print("Discovering shortcuts...", file=sys.stderr)
    
    shortcuts = list_shortcuts(lakehouse_full_path)
    
    if args.verbose:
        print(f"Found {len(shortcuts)} shortcuts", file=sys.stderr)
    
    # Validate each shortcut
    validation_results = []
    for shortcut in shortcuts:
        if args.verbose:
            print(f"Validating: {shortcut.get('name', 'Unknown')}", file=sys.stderr)
        
        result = validate_shortcut(shortcut, verbose=args.verbose)
        validation_results.append(result)
    
    # Build summary
    summary = {
        "total": len(validation_results),
        "valid": sum(1 for r in validation_results if r["status"] == "valid"),
        "broken": sum(1 for r in validation_results if r["status"] == "broken"),
        "inaccessible": sum(1 for r in validation_results if r["status"] == "inaccessible"),
        "invalid": sum(1 for r in validation_results if r["status"] == "invalid"),
        "errors": sum(1 for r in validation_results if r["status"] == "error")
    }
    
    # Build report
    report = {
        "lakehouse": lakehouse_full_path,
        "summary": summary,
        "shortcuts": validation_results
    }
    
    # Output report
    print_validation_report(report, args.format, args.output)
    
    # Return exit code
    if summary["broken"] > 0 or summary["invalid"] > 0 or summary["errors"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
