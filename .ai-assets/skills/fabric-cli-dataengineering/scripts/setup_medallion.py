#!/usr/bin/env python3
"""
setup_medallion.py - Create medallion architecture (bronze/silver/gold)

This script creates a standard medallion architecture in a Microsoft Fabric workspace,
including Bronze, Silver, and Gold lakehouses with standard folder structures.

Usage:
    python setup_medallion.py <workspace> [--prefix NAME]
    python setup_medallion.py DataPlatform.Workspace
    python setup_medallion.py DataPlatform.Workspace --prefix Sales

Exit codes:
    0 - Medallion architecture created successfully
    1 - Error during creation
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


def create_lakehouse(workspace: str, name: str, enable_schemas: bool = False) -> Dict[str, Any]:
    """Create a lakehouse in the workspace."""
    lakehouse_path = f"{workspace}/{name}.Lakehouse"
    
    result = {
        "name": name,
        "path": lakehouse_path,
        "status": "unknown",
        "message": ""
    }
    
    # Check if already exists
    if check_item_exists(lakehouse_path):
        result["status"] = "exists"
        result["message"] = f"Lakehouse '{name}' already exists"
        return result
    
    # Create the lakehouse
    cmd = ["create", lakehouse_path, "-f"]
    if enable_schemas:
        cmd.extend(["-P", "enableSchemas=true"])
    
    exit_code, stdout, stderr = run_fab_command(cmd)
    
    if exit_code == 0:
        result["status"] = "created"
        result["message"] = f"Lakehouse '{name}' created successfully"
    else:
        result["status"] = "failed"
        result["message"] = stderr.strip() or f"Failed to create lakehouse '{name}'"
    
    return result


def create_folder(lakehouse_path: str, folder_path: str) -> Dict[str, Any]:
    """Create a folder in a lakehouse."""
    full_path = f"{lakehouse_path}/{folder_path}"
    
    result = {
        "path": full_path,
        "status": "unknown",
        "message": ""
    }
    
    exit_code, stdout, stderr = run_fab_command(["mkdir", full_path, "-f"])
    
    if exit_code == 0:
        result["status"] = "created"
        result["message"] = f"Folder '{folder_path}' created"
    elif "already exists" in stderr.lower():
        result["status"] = "exists"
        result["message"] = f"Folder '{folder_path}' already exists"
    else:
        result["status"] = "failed"
        result["message"] = stderr.strip() or f"Failed to create folder '{folder_path}'"
    
    return result


def create_shortcut(source_lakehouse: str, target_lakehouse: str, shortcut_name: str, target_folder: str) -> Dict[str, Any]:
    """Create a shortcut between lakehouses."""
    shortcut_path = f"{source_lakehouse}/Files/{shortcut_name}.Shortcut"
    target_path = f"{target_lakehouse}/Files/{target_folder}"
    
    result = {
        "shortcut": shortcut_path,
        "target": target_path,
        "status": "unknown",
        "message": ""
    }
    
    # Check if shortcut already exists
    if check_item_exists(shortcut_path):
        result["status"] = "exists"
        result["message"] = f"Shortcut '{shortcut_name}' already exists"
        return result
    
    exit_code, stdout, stderr = run_fab_command([
        "ln", shortcut_path, 
        "--type", "oneLake",
        "--target", target_path,
        "-f"
    ])
    
    if exit_code == 0:
        result["status"] = "created"
        result["message"] = f"Shortcut '{shortcut_name}' created"
    else:
        result["status"] = "failed"
        result["message"] = stderr.strip() or f"Failed to create shortcut '{shortcut_name}'"
    
    return result


def setup_medallion_architecture(
    workspace: str, 
    prefix: Optional[str] = None,
    enable_schemas: bool = False,
    create_shortcuts: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Set up complete medallion architecture."""
    
    workspace = ensure_workspace_suffix(workspace)
    
    # Define lakehouse names
    bronze_name = f"{prefix}_Bronze" if prefix else "Bronze"
    silver_name = f"{prefix}_Silver" if prefix else "Silver"
    gold_name = f"{prefix}_Gold" if prefix else "Gold"
    
    # Standard folder structure for each layer
    bronze_folders = ["Files/raw", "Files/landing", "Files/archive"]
    silver_folders = ["Files/cleansed", "Files/enriched", "Files/validated"]
    gold_folders = ["Files/curated", "Files/aggregated", "Files/published"]
    
    report = {
        "workspace": workspace,
        "prefix": prefix,
        "dry_run": dry_run,
        "lakehouses": [],
        "folders": [],
        "shortcuts": [],
        "summary": {
            "lakehouses_created": 0,
            "lakehouses_existed": 0,
            "folders_created": 0,
            "shortcuts_created": 0,
            "errors": 0
        }
    }
    
    if dry_run:
        print("\n[DRY RUN] The following resources would be created:\n")
        print(f"Workspace: {workspace}")
        print(f"\nLakehouses:")
        print(f"  - {bronze_name}.Lakehouse")
        print(f"  - {silver_name}.Lakehouse")
        print(f"  - {gold_name}.Lakehouse")
        print(f"\nFolders in each lakehouse:")
        for folder in bronze_folders:
            print(f"  - Bronze: {folder}")
        for folder in silver_folders:
            print(f"  - Silver: {folder}")
        for folder in gold_folders:
            print(f"  - Gold: {folder}")
        if create_shortcuts:
            print(f"\nShortcuts:")
            print(f"  - Silver -> Bronze (bronze_source)")
            print(f"  - Gold -> Silver (silver_source)")
        return report
    
    # Check workspace exists
    print(f"\nSetting up medallion architecture in: {workspace}")
    if not check_workspace_exists(workspace):
        print(f"Error: Workspace '{workspace}' does not exist or is not accessible")
        sys.exit(1)
    
    # Create lakehouses
    print("\n1. Creating Lakehouses...")
    lakehouses = [
        (bronze_name, bronze_folders),
        (silver_name, silver_folders),
        (gold_name, gold_folders)
    ]
    
    for lh_name, folders in lakehouses:
        print(f"   Creating {lh_name}.Lakehouse...")
        result = create_lakehouse(workspace, lh_name, enable_schemas)
        report["lakehouses"].append(result)
        
        if result["status"] == "created":
            report["summary"]["lakehouses_created"] += 1
            print(f"   ✓ {result['message']}")
        elif result["status"] == "exists":
            report["summary"]["lakehouses_existed"] += 1
            print(f"   • {result['message']}")
        else:
            report["summary"]["errors"] += 1
            print(f"   ✗ {result['message']}")
    
    # Create folder structures
    print("\n2. Creating folder structures...")
    for lh_name, folders in lakehouses:
        lakehouse_path = f"{workspace}/{lh_name}.Lakehouse"
        print(f"   {lh_name}:")
        for folder in folders:
            result = create_folder(lakehouse_path, folder)
            report["folders"].append(result)
            
            if result["status"] == "created":
                report["summary"]["folders_created"] += 1
                print(f"     ✓ {folder}")
            elif result["status"] == "exists":
                print(f"     • {folder} (exists)")
            else:
                report["summary"]["errors"] += 1
                print(f"     ✗ {folder}: {result['message']}")
    
    # Create shortcuts between layers (optional)
    if create_shortcuts:
        print("\n3. Creating shortcuts between layers...")
        
        # Silver -> Bronze shortcut
        silver_path = f"{workspace}/{silver_name}.Lakehouse"
        bronze_path = f"{workspace}/{bronze_name}.Lakehouse"
        gold_path = f"{workspace}/{gold_name}.Lakehouse"
        
        result = create_shortcut(silver_path, bronze_path, "bronze_source", "cleansed")
        report["shortcuts"].append(result)
        if result["status"] == "created":
            report["summary"]["shortcuts_created"] += 1
            print(f"   ✓ Silver -> Bronze shortcut created")
        else:
            print(f"   • {result['message']}")
        
        # Gold -> Silver shortcut
        result = create_shortcut(gold_path, silver_path, "silver_source", "enriched")
        report["shortcuts"].append(result)
        if result["status"] == "created":
            report["summary"]["shortcuts_created"] += 1
            print(f"   ✓ Gold -> Silver shortcut created")
        else:
            print(f"   • {result['message']}")
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Create medallion architecture (Bronze/Silver/Gold lakehouses)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python setup_medallion.py DataPlatform.Workspace
    python setup_medallion.py DataPlatform.Workspace --prefix Sales
    python setup_medallion.py "My Workspace" --prefix Analytics --with-shortcuts
    python setup_medallion.py Dev.Workspace --dry-run

Medallion Architecture:
    Bronze: Raw data ingestion layer
    Silver: Cleansed and validated data
    Gold: Curated business-ready data
        """
    )
    parser.add_argument(
        "workspace",
        help="Workspace name or path where medallion architecture will be created"
    )
    parser.add_argument(
        "--prefix", "-p",
        help="Prefix for lakehouse names (e.g., 'Sales' creates Sales_Bronze, Sales_Silver, Sales_Gold)"
    )
    parser.add_argument(
        "--enable-schemas",
        action="store_true",
        help="Enable schema support for lakehouses"
    )
    parser.add_argument(
        "--with-shortcuts",
        action="store_true",
        help="Create shortcuts between layers (Silver->Bronze, Gold->Silver)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be created without making changes"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    try:
        report = setup_medallion_architecture(
            workspace=args.workspace,
            prefix=args.prefix,
            enable_schemas=args.enable_schemas,
            create_shortcuts=args.with_shortcuts,
            dry_run=args.dry_run
        )
        
        if args.dry_run:
            sys.exit(0)
        
        # Print summary
        print("\n" + "=" * 50)
        print("MEDALLION ARCHITECTURE SETUP COMPLETE")
        print("=" * 50)
        print(f"Workspace: {report['workspace']}")
        if report['prefix']:
            print(f"Prefix: {report['prefix']}")
        print(f"\nSummary:")
        print(f"  Lakehouses created: {report['summary']['lakehouses_created']}")
        print(f"  Lakehouses existed: {report['summary']['lakehouses_existed']}")
        print(f"  Folders created: {report['summary']['folders_created']}")
        if args.with_shortcuts:
            print(f"  Shortcuts created: {report['summary']['shortcuts_created']}")
        print(f"  Errors: {report['summary']['errors']}")
        print("=" * 50)
        
        if args.json:
            print("\n" + json.dumps(report, indent=2))
        
        sys.exit(0 if report['summary']['errors'] == 0 else 1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
