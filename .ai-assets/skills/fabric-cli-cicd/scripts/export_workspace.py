#!/usr/bin/env python3
"""
export_workspace.py - Export all workspace items for version control

This script exports all items from a Microsoft Fabric workspace to a local directory
in a format suitable for Git version control.

Usage:
    python export_workspace.py <workspace> -o <dir>
    python export_workspace.py Dev.Workspace -o ./fabric-exports/

Exit codes:
    0 - Export completed successfully
    1 - Export failed or had errors
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


# Item types that support export
EXPORTABLE_ITEM_TYPES = [
    "Notebook", "SparkJobDefinition", "DataPipeline",
    "Report", "SemanticModel", "PaginatedReport",
    "KQLDatabase", "KQLDashboard", "KQLQueryset",
    "Eventhouse", "Eventstream", "MirroredDatabase",
    "Reflex", "MountedDataFactory", "CopyJob", "VariableLibrary",
    "Environment", "MLModel", "MLExperiment"
]


def run_fab_command(args: list[str], timeout: int = 300) -> tuple[int, str, str]:
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


def get_workspace_items(workspace: str) -> List[Dict[str, Any]]:
    """Get all items in the workspace."""
    exit_code, stdout, stderr = run_fab_command(["ls", workspace, "-l", "-f", "json"])
    
    if exit_code == 0:
        try:
            result = json.loads(stdout.strip())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
    
    return []


def get_workspace_details(workspace: str) -> Dict[str, Any]:
    """Get workspace metadata."""
    exit_code, stdout, stderr = run_fab_command(["get", workspace, "-f", "json"])
    
    if exit_code == 0:
        try:
            return json.loads(stdout.strip())
        except json.JSONDecodeError:
            pass
    
    return {}


def export_item(item_path: str, output_dir: str) -> Dict[str, Any]:
    """Export a single item to the output directory."""
    result = {
        "item": item_path,
        "output_dir": output_dir,
        "status": "unknown",
        "message": ""
    }
    
    # Build export command
    cmd = ["export", item_path, "-o", output_dir, "-f"]
    
    exit_code, stdout, stderr = run_fab_command(cmd)
    
    if exit_code == 0:
        result["status"] = "success"
        result["message"] = "Exported successfully"
    else:
        # Check if export is not supported for this item type
        if "not supported" in stderr.lower() or "cannot export" in stderr.lower():
            result["status"] = "skipped"
            result["message"] = "Export not supported for this item type"
        else:
            result["status"] = "failed"
            result["message"] = stderr.strip() or "Export failed"
    
    return result


def generate_manifest(
    workspace: str,
    workspace_details: Dict[str, Any],
    items: List[Dict[str, Any]],
    export_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate manifest.json with workspace metadata."""
    
    successful_exports = [r for r in export_results if r["status"] == "success"]
    
    manifest = {
        "manifest_version": "1.0.0",
        "export_metadata": {
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "source_workspace": workspace,
            "workspace_id": workspace_details.get("id"),
            "capacity_id": workspace_details.get("capacityId"),
            "total_items": len(items),
            "exported_items": len(successful_exports)
        },
        "workspace_info": {
            "name": workspace_details.get("displayName", workspace.replace(".Workspace", "")),
            "id": workspace_details.get("id"),
            "description": workspace_details.get("description", ""),
            "type": workspace_details.get("type")
        },
        "items": []
    }
    
    for result in export_results:
        if result["status"] == "success":
            manifest["items"].append({
                "path": result["item"],
                "name": result.get("name", ""),
                "type": result.get("type", ""),
                "status": "exported"
            })
    
    return manifest


def export_workspace(
    workspace: str,
    output_dir: str,
    include_unsupported: bool = False
) -> Dict[str, Any]:
    """Export all workspace items to the output directory."""
    
    workspace = ensure_workspace_suffix(workspace)
    
    report = {
        "workspace": workspace,
        "output_directory": output_dir,
        "items_found": [],
        "export_results": [],
        "summary": {
            "total_items": 0,
            "exported": 0,
            "skipped": 0,
            "failed": 0,
            "not_supported": 0
        }
    }
    
    # Verify workspace exists
    print(f"\nVerifying workspace: {workspace}")
    if not check_workspace_exists(workspace):
        print(f"Error: Workspace '{workspace}' does not exist or is not accessible")
        return report
    print("  Workspace found")
    
    # Get workspace details
    print("\nFetching workspace details...")
    workspace_details = get_workspace_details(workspace)
    
    # Get all items
    print("Fetching workspace items...")
    items = get_workspace_items(workspace)
    report["items_found"] = items
    report["summary"]["total_items"] = len(items)
    
    if not items:
        print("No items found in workspace")
        return report
    
    print(f"  Found {len(items)} item(s)")
    
    # Group items by type for display
    items_by_type = {}
    for item in items:
        item_type = item.get("type", "Unknown")
        if item_type not in items_by_type:
            items_by_type[item_type] = []
        items_by_type[item_type].append(item)
    
    print("\n  Items by type:")
    for item_type, type_items in sorted(items_by_type.items()):
        print(f"    {item_type}: {len(type_items)}")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"\nExporting to: {output_dir}")
    
    # Export each item
    print("\nExporting items...")
    for item in items:
        item_name = item.get("displayName", item.get("name", "Unknown"))
        item_type = item.get("type", "Unknown")
        item_id = item.get("id", "")
        full_name = f"{item_name}.{item_type}"
        item_path = f"{workspace}/{full_name}"
        
        export_result = {
            "item": item_path,
            "name": item_name,
            "type": item_type,
            "id": item_id,
            "status": "unknown",
            "message": ""
        }
        
        # Check if item type is exportable
        if item_type not in EXPORTABLE_ITEM_TYPES and not include_unsupported:
            export_result["status"] = "not_supported"
            export_result["message"] = f"Item type '{item_type}' export not supported"
            report["export_results"].append(export_result)
            report["summary"]["not_supported"] += 1
            print(f"  [{item_type}] {item_name}: skipped (not supported)")
            continue
        
        print(f"  [{item_type}] {item_name}...")
        
        result = export_item(item_path, output_dir)
        export_result["status"] = result["status"]
        export_result["message"] = result["message"]
        report["export_results"].append(export_result)
        
        if result["status"] == "success":
            report["summary"]["exported"] += 1
            print(f"    ✓ Exported")
        elif result["status"] == "skipped":
            report["summary"]["skipped"] += 1
            print(f"    - Skipped: {result['message']}")
        else:
            report["summary"]["failed"] += 1
            print(f"    ✗ Failed: {result['message']}")
    
    # Generate manifest
    print("\nGenerating manifest.json...")
    manifest = generate_manifest(workspace, workspace_details, items, report["export_results"])
    manifest_path = output_path / "manifest.json"
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"  Manifest saved: {manifest_path}")
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Export all workspace items for version control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python export_workspace.py Dev.Workspace -o ./fabric-exports/
    python export_workspace.py Production.Workspace -o ./exports/prod/
    python export_workspace.py "My Workspace" -o ./my-workspace-export/

Output Structure:
    <output-dir>/
    ├── manifest.json           # Export metadata and item list
    ├── MyNotebook.Notebook/    # Exported item folders
    │   ├── .platform
    │   └── notebook-content.json
    ├── SalesReport.Report/
    │   ├── .platform
    │   └── definition.pbir
    └── DataModel.SemanticModel/
        ├── .platform
        └── model.bim

Supported Item Types:
    Notebook, SparkJobDefinition, DataPipeline, Report, SemanticModel,
    PaginatedReport, KQLDatabase, KQLDashboard, KQLQueryset, Eventhouse,
    Eventstream, MirroredDatabase, Reflex, MountedDataFactory, CopyJob,
    VariableLibrary, Environment, MLModel, MLExperiment
        """
    )
    parser.add_argument(
        "workspace",
        help="Workspace name or path to export"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output directory for exported items"
    )
    parser.add_argument(
        "--include-unsupported",
        action="store_true",
        help="Attempt to export items even if type is not officially supported"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    try:
        report = export_workspace(
            workspace=args.workspace,
            output_dir=args.output,
            include_unsupported=args.include_unsupported
        )
        
        # Print summary
        print("\n" + "=" * 50)
        print("EXPORT SUMMARY")
        print("=" * 50)
        print(f"Workspace: {report['workspace']}")
        print(f"Output Directory: {report['output_directory']}")
        print(f"\nResults:")
        print(f"  Total Items: {report['summary']['total_items']}")
        print(f"  Exported: {report['summary']['exported']}")
        print(f"  Skipped: {report['summary']['skipped']}")
        print(f"  Failed: {report['summary']['failed']}")
        print(f"  Not Supported: {report['summary']['not_supported']}")
        print("=" * 50)
        
        if args.json:
            print("\n" + json.dumps(report, indent=2))
        
        # Exit code based on failures
        sys.exit(0 if report['summary']['failed'] == 0 else 1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
