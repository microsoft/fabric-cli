#!/usr/bin/env python3
"""
deploy.py - Deploy items from local folder to workspace

This script deploys Fabric items from a local filesystem (typically an export directory)
to a target workspace. It supports creating new items and updating existing ones.

Usage:
    python deploy.py <source> <target-ws> [--dry-run]
    python deploy.py ./fabric-items/ Production.Workspace
    python deploy.py ./fabric-items/ Production.Workspace --dry-run

Exit codes:
    0 - Deployment completed successfully
    1 - Deployment failed or had errors
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


# Supported item types that can be imported
IMPORTABLE_ITEM_TYPES = [
    "Notebook", "SparkJobDefinition", "DataPipeline",
    "Report", "SemanticModel",
    "KQLDatabase", "KQLDashboard", "KQLQueryset",
    "Eventhouse", "Eventstream", "MirroredDatabase",
    "Reflex", "MountedDataFactory", "CopyJob", "VariableLibrary"
]


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


def ensure_workspace_suffix(workspace: str) -> str:
    """Ensure workspace name has .Workspace suffix."""
    if not workspace.endswith(".Workspace"):
        return f"{workspace}.Workspace"
    return workspace


def check_workspace_exists(workspace: str) -> bool:
    """Check if workspace exists."""
    exit_code, _, _ = run_fab_command(["exists", workspace])
    return exit_code == 0


def check_item_exists(item_path: str) -> bool:
    """Check if an item exists."""
    exit_code, _, _ = run_fab_command(["exists", item_path])
    return exit_code == 0


def discover_items(source_dir: str) -> List[Dict[str, Any]]:
    """Discover Fabric items in the source directory."""
    items = []
    source_path = Path(source_dir)
    
    if not source_path.exists():
        return items
    
    # Look for item directories with type suffixes
    for entry in source_path.iterdir():
        if entry.is_dir():
            # Check if directory name ends with a known item type
            name = entry.name
            for item_type in IMPORTABLE_ITEM_TYPES:
                if name.endswith(f".{item_type}"):
                    item_name = name[:-len(f".{item_type}")]
                    items.append({
                        "name": item_name,
                        "type": item_type,
                        "full_name": name,
                        "source_path": str(entry),
                        "has_definition": (entry / ".platform").exists() or any(entry.glob("*.json"))
                    })
                    break
    
    return items


def import_item(source_path: str, target_path: str, force: bool = True) -> Dict[str, Any]:
    """Import an item from local source to target workspace."""
    result = {
        "source": source_path,
        "target": target_path,
        "status": "unknown",
        "message": ""
    }
    
    # Build import command
    cmd = ["import", target_path, "-i", source_path]
    if force:
        cmd.append("-f")
    
    exit_code, stdout, stderr = run_fab_command(cmd)
    
    if exit_code == 0:
        result["status"] = "success"
        result["message"] = "Item imported successfully"
    else:
        result["status"] = "failed"
        result["message"] = stderr.strip() or "Import failed"
    
    return result


def create_item(workspace: str, item_name: str, item_type: str) -> Dict[str, Any]:
    """Create a new item in the workspace."""
    item_path = f"{workspace}/{item_name}.{item_type}"
    
    result = {
        "path": item_path,
        "status": "unknown",
        "message": ""
    }
    
    exit_code, stdout, stderr = run_fab_command(["create", item_path, "-f"])
    
    if exit_code == 0:
        result["status"] = "created"
        result["message"] = f"Item '{item_name}.{item_type}' created"
    else:
        result["status"] = "failed"
        result["message"] = stderr.strip() or f"Failed to create item"
    
    return result


def deploy_items(
    source_dir: str,
    target_workspace: str,
    dry_run: bool = False,
    ignore_errors: bool = False
) -> Dict[str, Any]:
    """Deploy items from source directory to target workspace."""
    
    target_workspace = ensure_workspace_suffix(target_workspace)
    
    report = {
        "source_directory": source_dir,
        "target_workspace": target_workspace,
        "dry_run": dry_run,
        "items_discovered": [],
        "deployment_results": [],
        "summary": {
            "total_items": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0
        }
    }
    
    # Discover items in source directory
    print(f"\nDiscovering items in: {source_dir}")
    items = discover_items(source_dir)
    report["items_discovered"] = items
    report["summary"]["total_items"] = len(items)
    
    if not items:
        print("No deployable items found in source directory.")
        print(f"\nExpected format: <item_name>.<ItemType>/ directories")
        print(f"Supported types: {', '.join(IMPORTABLE_ITEM_TYPES)}")
        return report
    
    print(f"Found {len(items)} item(s) to deploy:")
    for item in items:
        print(f"  - {item['full_name']}")
    
    if dry_run:
        print(f"\n[DRY RUN] Would deploy to: {target_workspace}")
        for item in items:
            item_path = f"{target_workspace}/{item['full_name']}"
            exists = check_item_exists(item_path)
            action = "UPDATE" if exists else "CREATE"
            print(f"  [{action}] {item['full_name']}")
        return report
    
    # Check workspace exists
    print(f"\nVerifying workspace: {target_workspace}")
    if not check_workspace_exists(target_workspace):
        print(f"Error: Workspace '{target_workspace}' does not exist or is not accessible")
        sys.exit(1)
    
    # Deploy each item
    print(f"\nDeploying items...")
    for item in items:
        item_name = item["name"]
        item_type = item["type"]
        full_name = item["full_name"]
        source_path = item["source_path"]
        target_path = f"{target_workspace}/{full_name}"
        
        print(f"\n  Deploying {full_name}...")
        
        deployment_result = {
            "item": full_name,
            "source": source_path,
            "target": target_path,
            "action": "unknown",
            "status": "unknown",
            "message": ""
        }
        
        # Check if item exists
        exists = check_item_exists(target_path)
        
        if exists:
            # Update existing item via import
            deployment_result["action"] = "update"
            print(f"    Item exists, updating...")
            result = import_item(source_path, target_path)
            deployment_result["status"] = result["status"]
            deployment_result["message"] = result["message"]
            
            if result["status"] == "success":
                report["summary"]["updated"] += 1
                print(f"    ✓ Updated successfully")
            else:
                report["summary"]["failed"] += 1
                print(f"    ✗ Update failed: {result['message']}")
                if not ignore_errors:
                    report["deployment_results"].append(deployment_result)
                    return report
        else:
            # Create new item and import definition
            deployment_result["action"] = "create"
            print(f"    Creating new item...")
            
            # First create the item
            create_result = create_item(target_workspace, item_name, item_type)
            
            if create_result["status"] == "created":
                # Then import the definition
                print(f"    Importing definition...")
                import_result = import_item(source_path, target_path)
                
                if import_result["status"] == "success":
                    deployment_result["status"] = "success"
                    deployment_result["message"] = "Created and imported successfully"
                    report["summary"]["created"] += 1
                    print(f"    ✓ Created and imported successfully")
                else:
                    deployment_result["status"] = "partial"
                    deployment_result["message"] = f"Created but import failed: {import_result['message']}"
                    report["summary"]["created"] += 1
                    print(f"    ⚠ Created but import failed: {import_result['message']}")
            else:
                deployment_result["status"] = "failed"
                deployment_result["message"] = create_result["message"]
                report["summary"]["failed"] += 1
                print(f"    ✗ Creation failed: {create_result['message']}")
                
                if not ignore_errors:
                    report["deployment_results"].append(deployment_result)
                    return report
        
        report["deployment_results"].append(deployment_result)
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Fabric items from local folder to workspace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python deploy.py ./fabric-items/ Production.Workspace
    python deploy.py ./exports/ Dev.Workspace --dry-run
    python deploy.py ./fabric-items/ "My Workspace" --ignore-errors

Source Directory Structure:
    The source directory should contain item folders with type suffixes:
    
    ./fabric-items/
    ├── MyNotebook.Notebook/
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
    KQLDatabase, KQLDashboard, KQLQueryset, Eventhouse, Eventstream,
    MirroredDatabase, Reflex, MountedDataFactory, CopyJob, VariableLibrary
        """
    )
    parser.add_argument(
        "source",
        help="Source directory containing item exports"
    )
    parser.add_argument(
        "target",
        help="Target workspace name or path"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview deployment without making changes"
    )
    parser.add_argument(
        "--ignore-errors",
        action="store_true",
        help="Continue deployment even if individual items fail"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    # Validate source directory
    if not os.path.isdir(args.source):
        print(f"Error: Source directory '{args.source}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    try:
        report = deploy_items(
            source_dir=args.source,
            target_workspace=args.target,
            dry_run=args.dry_run,
            ignore_errors=args.ignore_errors
        )
        
        # Print summary
        print("\n" + "=" * 50)
        print("DEPLOYMENT SUMMARY")
        print("=" * 50)
        print(f"Source: {report['source_directory']}")
        print(f"Target: {report['target_workspace']}")
        print(f"Dry Run: {report['dry_run']}")
        print(f"\nResults:")
        print(f"  Total Items: {report['summary']['total_items']}")
        print(f"  Created: {report['summary']['created']}")
        print(f"  Updated: {report['summary']['updated']}")
        print(f"  Skipped: {report['summary']['skipped']}")
        print(f"  Failed: {report['summary']['failed']}")
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
