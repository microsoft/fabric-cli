#!/usr/bin/env python3
"""
optimize_tables.py - Run optimization on lakehouse tables

This script runs V-Order and/or Z-Order optimization on lakehouse tables
to improve query performance.

Usage:
    python optimize_tables.py <lakehouse> [--vorder] [--zorder COL]
    python optimize_tables.py DataPlatform.Workspace/Bronze.Lakehouse --vorder
    python optimize_tables.py DataPlatform.Workspace/Bronze.Lakehouse/Tables/sales --zorder customer_id,date

Exit codes:
    0 - Optimization completed successfully
    1 - Optimization failed or had errors
"""

import argparse
import json
import subprocess
import sys
from typing import Dict, Any, List, Optional


def run_fab_command(args: list[str], timeout: int = 600) -> tuple[int, str, str]:
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


def check_path_exists(path: str) -> bool:
    """Check if path exists."""
    exit_code, _, _ = run_fab_command(["exists", path])
    return exit_code == 0


def parse_lakehouse_path(path: str) -> Dict[str, Optional[str]]:
    """Parse lakehouse path into components."""
    result = {
        "workspace": None,
        "lakehouse": None,
        "table": None,
        "full_path": path
    }
    
    parts = path.split("/")
    
    for i, part in enumerate(parts):
        if part.endswith(".Workspace"):
            result["workspace"] = part
        elif part.endswith(".Lakehouse"):
            result["lakehouse"] = part
            if result["workspace"]:
                result["lakehouse_path"] = f"{result['workspace']}/{part}"
        elif part == "Tables" and i < len(parts) - 1:
            result["table"] = parts[i + 1]
    
    return result


def get_lakehouse_tables(lakehouse_path: str) -> List[Dict[str, Any]]:
    """Get all tables in a lakehouse."""
    tables_path = f"{lakehouse_path}/Tables"
    exit_code, stdout, stderr = run_fab_command(["ls", tables_path, "-l", "-f", "json"])
    
    if exit_code == 0:
        try:
            result = json.loads(stdout.strip())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
    
    return []


def optimize_table_vorder(table_path: str) -> Dict[str, Any]:
    """Run V-Order optimization on a table."""
    result = {
        "table": table_path,
        "optimization": "vorder",
        "status": "unknown",
        "message": ""
    }
    
    # Run OPTIMIZE command with VORDER
    cmd = ["tables", "optimize", table_path, "--vorder", "-f", "json"]
    
    exit_code, stdout, stderr = run_fab_command(cmd, timeout=1800)  # 30 min timeout for large tables
    
    if exit_code == 0:
        result["status"] = "success"
        result["message"] = "V-Order optimization completed"
        try:
            result["details"] = json.loads(stdout.strip())
        except json.JSONDecodeError:
            result["details"] = {"output": stdout.strip()}
    else:
        result["status"] = "failed"
        result["message"] = stderr.strip() or "V-Order optimization failed"
    
    return result


def optimize_table_zorder(table_path: str, columns: List[str]) -> Dict[str, Any]:
    """Run Z-Order optimization on a table."""
    result = {
        "table": table_path,
        "optimization": "zorder",
        "columns": columns,
        "status": "unknown",
        "message": ""
    }
    
    # Run OPTIMIZE command with ZORDER
    columns_str = ",".join(columns)
    cmd = ["tables", "optimize", table_path, "--zorder", columns_str, "-f", "json"]
    
    exit_code, stdout, stderr = run_fab_command(cmd, timeout=1800)  # 30 min timeout for large tables
    
    if exit_code == 0:
        result["status"] = "success"
        result["message"] = f"Z-Order optimization completed on columns: {columns_str}"
        try:
            result["details"] = json.loads(stdout.strip())
        except json.JSONDecodeError:
            result["details"] = {"output": stdout.strip()}
    else:
        result["status"] = "failed"
        result["message"] = stderr.strip() or "Z-Order optimization failed"
    
    return result


def get_table_stats(table_path: str) -> Dict[str, Any]:
    """Get table statistics."""
    exit_code, stdout, stderr = run_fab_command(["tables", "get", table_path, "-f", "json"])
    
    if exit_code == 0:
        try:
            return json.loads(stdout.strip())
        except json.JSONDecodeError:
            pass
    
    return {}


def optimize_tables(
    path: str,
    vorder: bool = False,
    zorder_columns: Optional[List[str]] = None,
    table_filter: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Optimize tables in a lakehouse."""
    
    report = {
        "path": path,
        "vorder": vorder,
        "zorder_columns": zorder_columns,
        "dry_run": dry_run,
        "tables_found": [],
        "optimization_results": [],
        "summary": {
            "total_tables": 0,
            "optimized": 0,
            "failed": 0,
            "skipped": 0
        }
    }
    
    # Parse the path
    parsed = parse_lakehouse_path(path)
    
    # Verify path exists
    print(f"\nVerifying path: {path}")
    if not check_path_exists(path):
        print(f"Error: Path '{path}' does not exist or is not accessible")
        return report
    print("  Path found")
    
    # Determine if we're optimizing a single table or all tables in a lakehouse
    tables_to_optimize = []
    
    if parsed.get("table"):
        # Single table specified
        tables_to_optimize = [{
            "name": parsed["table"],
            "path": path
        }]
        print(f"\nTarget: Single table '{parsed['table']}'")
    else:
        # Get all tables in lakehouse
        print("\nFetching lakehouse tables...")
        
        lakehouse_path = path
        tables = get_lakehouse_tables(lakehouse_path)
        
        for table in tables:
            table_name = table.get("displayName", table.get("name", "Unknown"))
            table_path = f"{lakehouse_path}/Tables/{table_name}"
            
            if table_filter and table_filter.lower() not in table_name.lower():
                continue
            
            tables_to_optimize.append({
                "name": table_name,
                "path": table_path,
                "metadata": table
            })
        
        print(f"  Found {len(tables_to_optimize)} table(s)")
    
    report["tables_found"] = [t["name"] for t in tables_to_optimize]
    report["summary"]["total_tables"] = len(tables_to_optimize)
    
    if not tables_to_optimize:
        print("No tables found to optimize")
        return report
    
    # Validate optimization options
    if not vorder and not zorder_columns:
        print("\nError: Must specify --vorder and/or --zorder columns")
        print("  Use --vorder for V-Order optimization")
        print("  Use --zorder col1,col2 for Z-Order optimization")
        return report
    
    if dry_run:
        print(f"\n[DRY RUN] Would optimize the following tables:")
        for table in tables_to_optimize:
            print(f"  - {table['name']}")
            if vorder:
                print(f"      V-Order: Yes")
            if zorder_columns:
                print(f"      Z-Order columns: {', '.join(zorder_columns)}")
        return report
    
    # Optimize each table
    print("\nOptimizing tables...")
    for table in tables_to_optimize:
        table_name = table["name"]
        table_path = table["path"]
        
        print(f"\n  Optimizing: {table_name}")
        
        table_result = {
            "table": table_name,
            "path": table_path,
            "optimizations": []
        }
        
        # V-Order optimization
        if vorder:
            print(f"    Running V-Order...")
            vorder_result = optimize_table_vorder(table_path)
            table_result["optimizations"].append(vorder_result)
            
            if vorder_result["status"] == "success":
                print(f"      ✓ V-Order completed")
            else:
                print(f"      ✗ V-Order failed: {vorder_result['message']}")
        
        # Z-Order optimization
        if zorder_columns:
            print(f"    Running Z-Order on: {', '.join(zorder_columns)}")
            zorder_result = optimize_table_zorder(table_path, zorder_columns)
            table_result["optimizations"].append(zorder_result)
            
            if zorder_result["status"] == "success":
                print(f"      ✓ Z-Order completed")
            else:
                print(f"      ✗ Z-Order failed: {zorder_result['message']}")
        
        # Determine overall status for this table
        all_success = all(opt["status"] == "success" for opt in table_result["optimizations"])
        any_success = any(opt["status"] == "success" for opt in table_result["optimizations"])
        
        if all_success:
            table_result["overall_status"] = "success"
            report["summary"]["optimized"] += 1
        elif any_success:
            table_result["overall_status"] = "partial"
            report["summary"]["optimized"] += 1
        else:
            table_result["overall_status"] = "failed"
            report["summary"]["failed"] += 1
        
        report["optimization_results"].append(table_result)
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Run optimization on lakehouse tables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # V-Order all tables in a lakehouse
    python optimize_tables.py DataPlatform.Workspace/Bronze.Lakehouse --vorder

    # Z-Order a specific table
    python optimize_tables.py DataPlatform.Workspace/Bronze.Lakehouse/Tables/sales --zorder customer_id,date

    # Both V-Order and Z-Order
    python optimize_tables.py DataPlatform.Workspace/Silver.Lakehouse --vorder --zorder date,region

    # Preview what would be optimized
    python optimize_tables.py DataPlatform.Workspace/Gold.Lakehouse --vorder --dry-run

    # Filter tables by name pattern
    python optimize_tables.py DataPlatform.Workspace/Bronze.Lakehouse --vorder --filter sales

Optimization Types:
    V-Order (--vorder):
        Optimizes data layout for read performance.
        Applies write-time sorting for faster queries.
        Recommended for tables with frequent analytical queries.

    Z-Order (--zorder col1,col2):
        Colocates related information in the same files.
        Improves filtering on specified columns.
        Best for columns commonly used in WHERE clauses.
        """
    )
    parser.add_argument(
        "path",
        help="Lakehouse or table path to optimize"
    )
    parser.add_argument(
        "--vorder",
        action="store_true",
        help="Apply V-Order optimization"
    )
    parser.add_argument(
        "--zorder",
        help="Comma-separated list of columns for Z-Order optimization"
    )
    parser.add_argument(
        "--filter",
        help="Filter tables by name pattern (case-insensitive)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview optimization without executing"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    # Parse Z-Order columns
    zorder_columns = None
    if args.zorder:
        zorder_columns = [col.strip() for col in args.zorder.split(",") if col.strip()]
    
    # Validate that at least one optimization is specified
    if not args.vorder and not zorder_columns:
        parser.error("Must specify --vorder and/or --zorder columns")
    
    try:
        report = optimize_tables(
            path=args.path,
            vorder=args.vorder,
            zorder_columns=zorder_columns,
            table_filter=args.filter,
            dry_run=args.dry_run
        )
        
        # Print summary
        print("\n" + "=" * 50)
        print("OPTIMIZATION SUMMARY")
        print("=" * 50)
        print(f"Path: {report['path']}")
        print(f"V-Order: {report['vorder']}")
        print(f"Z-Order Columns: {', '.join(report['zorder_columns']) if report['zorder_columns'] else 'None'}")
        print(f"Dry Run: {report['dry_run']}")
        print(f"\nResults:")
        print(f"  Total Tables: {report['summary']['total_tables']}")
        print(f"  Optimized: {report['summary']['optimized']}")
        print(f"  Failed: {report['summary']['failed']}")
        print(f"  Skipped: {report['summary']['skipped']}")
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
