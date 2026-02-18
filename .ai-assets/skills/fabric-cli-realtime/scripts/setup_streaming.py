#!/usr/bin/env python3
"""
setup_streaming.py - Create complete streaming pipeline

This script creates a complete real-time analytics pipeline in Microsoft Fabric,
including Eventhouse, KQL Database, Eventstream, KQL Queryset, and optionally an Activator.

Usage:
    python setup_streaming.py <workspace> --name <pipeline>
    python setup_streaming.py RealTime.Workspace --name IoTTelemetry
    python setup_streaming.py RealTime.Workspace --name IoTTelemetry --with-alerts

Exit codes:
    0 - Streaming pipeline created successfully
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


def parse_json_output(output: str) -> Any:
    """Parse JSON output from fab CLI."""
    try:
        return json.loads(output.strip())
    except json.JSONDecodeError:
        return None


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


def get_item_id(item_path: str) -> Optional[str]:
    """Get the ID of an item."""
    exit_code, stdout, stderr = run_fab_command(["get", item_path, "-q", "id", "-f", "json"])
    if exit_code == 0:
        result = parse_json_output(stdout)
        if result:
            return result.strip('"') if isinstance(result, str) else result
    return None


def create_eventhouse(workspace: str, name: str) -> Dict[str, Any]:
    """Create an Eventhouse in the workspace."""
    item_path = f"{workspace}/{name}.Eventhouse"
    
    result = {
        "name": name,
        "type": "Eventhouse",
        "path": item_path,
        "status": "unknown",
        "id": None,
        "message": ""
    }
    
    # Check if already exists
    if check_item_exists(item_path):
        result["status"] = "exists"
        result["id"] = get_item_id(item_path)
        result["message"] = f"Eventhouse '{name}' already exists"
        return result
    
    # Create the eventhouse
    exit_code, stdout, stderr = run_fab_command(["create", item_path, "-f"])
    
    if exit_code == 0:
        result["status"] = "created"
        result["id"] = get_item_id(item_path)
        result["message"] = f"Eventhouse '{name}' created successfully"
    else:
        result["status"] = "failed"
        result["message"] = stderr.strip() or f"Failed to create eventhouse '{name}'"
    
    return result


def create_kql_database(workspace: str, name: str, eventhouse_id: str) -> Dict[str, Any]:
    """Create a KQL Database linked to an Eventhouse."""
    item_path = f"{workspace}/{name}.KQLDatabase"
    
    result = {
        "name": name,
        "type": "KQLDatabase",
        "path": item_path,
        "status": "unknown",
        "id": None,
        "message": ""
    }
    
    # Check if already exists
    if check_item_exists(item_path):
        result["status"] = "exists"
        result["id"] = get_item_id(item_path)
        result["message"] = f"KQL Database '{name}' already exists"
        return result
    
    # Create the KQL database with eventhouse linkage
    exit_code, stdout, stderr = run_fab_command([
        "create", item_path, "-f",
        "-P", f"dbtype=ReadWrite",
        "-P", f"eventhouseId={eventhouse_id}"
    ])
    
    if exit_code == 0:
        result["status"] = "created"
        result["id"] = get_item_id(item_path)
        result["message"] = f"KQL Database '{name}' created and linked to Eventhouse"
    else:
        result["status"] = "failed"
        result["message"] = stderr.strip() or f"Failed to create KQL Database '{name}'"
    
    return result


def create_eventstream(workspace: str, name: str) -> Dict[str, Any]:
    """Create an Eventstream in the workspace."""
    item_path = f"{workspace}/{name}.Eventstream"
    
    result = {
        "name": name,
        "type": "Eventstream",
        "path": item_path,
        "status": "unknown",
        "id": None,
        "message": ""
    }
    
    # Check if already exists
    if check_item_exists(item_path):
        result["status"] = "exists"
        result["id"] = get_item_id(item_path)
        result["message"] = f"Eventstream '{name}' already exists"
        return result
    
    # Create the eventstream
    exit_code, stdout, stderr = run_fab_command(["create", item_path, "-f"])
    
    if exit_code == 0:
        result["status"] = "created"
        result["id"] = get_item_id(item_path)
        result["message"] = f"Eventstream '{name}' created successfully"
    else:
        result["status"] = "failed"
        result["message"] = stderr.strip() or f"Failed to create eventstream '{name}'"
    
    return result


def create_kql_queryset(workspace: str, name: str) -> Dict[str, Any]:
    """Create a KQL Queryset in the workspace."""
    item_path = f"{workspace}/{name}.KQLQueryset"
    
    result = {
        "name": name,
        "type": "KQLQueryset",
        "path": item_path,
        "status": "unknown",
        "id": None,
        "message": ""
    }
    
    # Check if already exists
    if check_item_exists(item_path):
        result["status"] = "exists"
        result["id"] = get_item_id(item_path)
        result["message"] = f"KQL Queryset '{name}' already exists"
        return result
    
    # Create the KQL queryset
    exit_code, stdout, stderr = run_fab_command(["create", item_path, "-f"])
    
    if exit_code == 0:
        result["status"] = "created"
        result["id"] = get_item_id(item_path)
        result["message"] = f"KQL Queryset '{name}' created successfully"
    else:
        result["status"] = "failed"
        result["message"] = stderr.strip() or f"Failed to create KQL Queryset '{name}'"
    
    return result


def create_activator(workspace: str, name: str) -> Dict[str, Any]:
    """Create an Activator (Reflex) in the workspace."""
    item_path = f"{workspace}/{name}.Reflex"
    
    result = {
        "name": name,
        "type": "Reflex (Activator)",
        "path": item_path,
        "status": "unknown",
        "id": None,
        "message": ""
    }
    
    # Check if already exists
    if check_item_exists(item_path):
        result["status"] = "exists"
        result["id"] = get_item_id(item_path)
        result["message"] = f"Activator '{name}' already exists"
        return result
    
    # Create the activator (Reflex)
    exit_code, stdout, stderr = run_fab_command(["create", item_path, "-f"])
    
    if exit_code == 0:
        result["status"] = "created"
        result["id"] = get_item_id(item_path)
        result["message"] = f"Activator '{name}' created successfully"
    else:
        result["status"] = "failed"
        result["message"] = stderr.strip() or f"Failed to create Activator '{name}'"
    
    return result


def setup_streaming_pipeline(
    workspace: str,
    name: str,
    with_alerts: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Set up complete streaming pipeline."""
    
    workspace = ensure_workspace_suffix(workspace)
    
    # Define component names
    eventhouse_name = f"{name}_Eventhouse"
    database_name = f"{name}_DB"
    eventstream_name = f"{name}_Stream"
    queryset_name = f"{name}_Queries"
    activator_name = f"{name}_Alerts"
    
    report = {
        "workspace": workspace,
        "pipeline_name": name,
        "with_alerts": with_alerts,
        "dry_run": dry_run,
        "components": [],
        "summary": {
            "total_components": 0,
            "created": 0,
            "existed": 0,
            "failed": 0
        }
    }
    
    # Calculate total components
    total = 4  # Eventhouse, KQLDatabase, Eventstream, KQLQueryset
    if with_alerts:
        total += 1  # Activator
    report["summary"]["total_components"] = total
    
    if dry_run:
        print(f"\n[DRY RUN] The following components would be created:\n")
        print(f"Workspace: {workspace}")
        print(f"Pipeline Name: {name}")
        print(f"\nComponents:")
        print(f"  1. {eventhouse_name}.Eventhouse")
        print(f"  2. {database_name}.KQLDatabase (linked to Eventhouse)")
        print(f"  3. {eventstream_name}.Eventstream")
        print(f"  4. {queryset_name}.KQLQueryset")
        if with_alerts:
            print(f"  5. {activator_name}.Reflex (Activator)")
        return report
    
    # Check workspace exists
    print(f"\nSetting up streaming pipeline '{name}' in: {workspace}")
    if not check_workspace_exists(workspace):
        print(f"Error: Workspace '{workspace}' does not exist or is not accessible")
        sys.exit(1)
    
    # Create components in order
    print("\n1. Creating Eventhouse...")
    eventhouse_result = create_eventhouse(workspace, eventhouse_name)
    report["components"].append(eventhouse_result)
    
    if eventhouse_result["status"] == "created":
        report["summary"]["created"] += 1
        print(f"   ✓ {eventhouse_result['message']}")
    elif eventhouse_result["status"] == "exists":
        report["summary"]["existed"] += 1
        print(f"   • {eventhouse_result['message']}")
    else:
        report["summary"]["failed"] += 1
        print(f"   ✗ {eventhouse_result['message']}")
        return report  # Can't continue without eventhouse
    
    # Create KQL Database (needs eventhouse ID)
    print("\n2. Creating KQL Database...")
    eventhouse_id = eventhouse_result.get("id")
    if not eventhouse_id:
        print("   ✗ Cannot create KQL Database: Eventhouse ID not available")
        report["summary"]["failed"] += 1
        return report
    
    database_result = create_kql_database(workspace, database_name, eventhouse_id)
    report["components"].append(database_result)
    
    if database_result["status"] == "created":
        report["summary"]["created"] += 1
        print(f"   ✓ {database_result['message']}")
    elif database_result["status"] == "exists":
        report["summary"]["existed"] += 1
        print(f"   • {database_result['message']}")
    else:
        report["summary"]["failed"] += 1
        print(f"   ✗ {database_result['message']}")
    
    # Create Eventstream
    print("\n3. Creating Eventstream...")
    eventstream_result = create_eventstream(workspace, eventstream_name)
    report["components"].append(eventstream_result)
    
    if eventstream_result["status"] == "created":
        report["summary"]["created"] += 1
        print(f"   ✓ {eventstream_result['message']}")
    elif eventstream_result["status"] == "exists":
        report["summary"]["existed"] += 1
        print(f"   • {eventstream_result['message']}")
    else:
        report["summary"]["failed"] += 1
        print(f"   ✗ {eventstream_result['message']}")
    
    # Create KQL Queryset
    print("\n4. Creating KQL Queryset...")
    queryset_result = create_kql_queryset(workspace, queryset_name)
    report["components"].append(queryset_result)
    
    if queryset_result["status"] == "created":
        report["summary"]["created"] += 1
        print(f"   ✓ {queryset_result['message']}")
    elif queryset_result["status"] == "exists":
        report["summary"]["existed"] += 1
        print(f"   • {queryset_result['message']}")
    else:
        report["summary"]["failed"] += 1
        print(f"   ✗ {queryset_result['message']}")
    
    # Create Activator if requested
    if with_alerts:
        print("\n5. Creating Activator...")
        activator_result = create_activator(workspace, activator_name)
        report["components"].append(activator_result)
        
        if activator_result["status"] == "created":
            report["summary"]["created"] += 1
            print(f"   ✓ {activator_result['message']}")
        elif activator_result["status"] == "exists":
            report["summary"]["existed"] += 1
            print(f"   • {activator_result['message']}")
        else:
            report["summary"]["failed"] += 1
            print(f"   ✗ {activator_result['message']}")
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Create complete streaming pipeline (Eventhouse, KQL Database, Eventstream, etc.)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python setup_streaming.py RealTime.Workspace --name IoTTelemetry
    python setup_streaming.py RealTime.Workspace --name SensorData --with-alerts
    python setup_streaming.py "My Workspace" --name Analytics --dry-run

Created Components:
    1. Eventhouse - Storage for real-time data
    2. KQL Database - Query engine linked to Eventhouse
    3. Eventstream - Data ingestion pipeline
    4. KQL Queryset - Saved queries for analysis
    5. Activator (optional) - Alert rules and triggers

Next Steps After Creation:
    1. Configure Eventstream sources (Event Hub, Kafka, etc.)
    2. Add Eventstream destinations (KQL Database)
    3. Create tables in KQL Database
    4. Add queries to KQL Queryset
    5. Configure alert rules in Activator
        """
    )
    parser.add_argument(
        "workspace",
        help="Workspace name or path where streaming pipeline will be created"
    )
    parser.add_argument(
        "--name", "-n",
        required=True,
        help="Base name for the streaming pipeline components"
    )
    parser.add_argument(
        "--with-alerts",
        action="store_true",
        help="Also create an Activator for alert rules"
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
        report = setup_streaming_pipeline(
            workspace=args.workspace,
            name=args.name,
            with_alerts=args.with_alerts,
            dry_run=args.dry_run
        )
        
        if args.dry_run:
            sys.exit(0)
        
        # Print summary
        print("\n" + "=" * 50)
        print("STREAMING PIPELINE SETUP COMPLETE")
        print("=" * 50)
        print(f"Workspace: {report['workspace']}")
        print(f"Pipeline Name: {report['pipeline_name']}")
        print(f"\nSummary:")
        print(f"  Total Components: {report['summary']['total_components']}")
        print(f"  Created: {report['summary']['created']}")
        print(f"  Already Existed: {report['summary']['existed']}")
        print(f"  Failed: {report['summary']['failed']}")
        
        print("\nComponents:")
        for comp in report["components"]:
            status_icon = "✓" if comp["status"] in ["created", "exists"] else "✗"
            print(f"  {status_icon} {comp['path']}")
        
        print("=" * 50)
        
        if args.json:
            print("\n" + json.dumps(report, indent=2))
        
        sys.exit(0 if report['summary']['failed'] == 0 else 1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
