#!/usr/bin/env python3
"""
kql_query.py - Execute KQL query and return results

This script executes Kusto Query Language (KQL) queries against a KQL database
and returns the results.

Usage:
    python kql_query.py <database> --query <kql-file>
    python kql_query.py RealTime.Workspace/SensorDB.KQLDatabase --query queries/anomalies.kql
    python kql_query.py RealTime.Workspace/SensorDB.KQLDatabase --inline "SensorData | take 10"

Exit codes:
    0 - Query executed successfully
    1 - Query execution failed
"""

import argparse
import csv
import json
import subprocess
import sys
from io import StringIO
from pathlib import Path
from typing import Dict, Any, List, Optional


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


def ensure_database_suffix(path: str) -> str:
    """Ensure path has .KQLDatabase suffix if needed."""
    known_suffixes = [".KQLDatabase", ".Workspace"]
    for suffix in known_suffixes:
        if path.endswith(suffix):
            return path
    
    # If path contains a workspace but no database type, add KQLDatabase
    if "/" in path and not path.split("/")[-1].count("."):
        return f"{path}.KQLDatabase"
    
    return path


def check_path_exists(path: str) -> bool:
    """Check if path exists."""
    exit_code, _, _ = run_fab_command(["exists", path])
    return exit_code == 0


def load_query_from_file(file_path: str) -> str:
    """Load KQL query from a file."""
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Query file not found: {file_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def execute_kql_query(
    database_path: str,
    query: str,
    timeout: int = 300,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Execute a KQL query against a database."""
    
    result = {
        "database": database_path,
        "query": query,
        "status": "unknown",
        "message": "",
        "rows": [],
        "columns": [],
        "row_count": 0,
        "execution_time_ms": None
    }
    
    # Apply limit if specified and not already in query
    if limit and "| take" not in query.lower() and "| limit" not in query.lower():
        query = f"{query} | take {limit}"
        result["query"] = query
    
    # Build the query command
    cmd = ["tables", "query", database_path, "-q", query, "-f", "json"]
    
    exit_code, stdout, stderr = run_fab_command(cmd, timeout=timeout)
    
    if exit_code == 0:
        result["status"] = "success"
        result["message"] = "Query executed successfully"
        
        # Parse the JSON results
        try:
            query_result = json.loads(stdout.strip())
            
            # Handle different result formats
            if isinstance(query_result, list):
                result["rows"] = query_result
                result["row_count"] = len(query_result)
                if query_result:
                    result["columns"] = list(query_result[0].keys())
            elif isinstance(query_result, dict):
                if "rows" in query_result:
                    result["rows"] = query_result["rows"]
                    result["row_count"] = len(query_result["rows"])
                if "columns" in query_result:
                    result["columns"] = query_result["columns"]
                if "statistics" in query_result:
                    stats = query_result["statistics"]
                    if "executionTime" in stats:
                        result["execution_time_ms"] = stats["executionTime"]
                        
        except json.JSONDecodeError:
            # Output might be in table format
            result["raw_output"] = stdout.strip()
            result["message"] = "Query executed but output is not JSON"
    else:
        result["status"] = "failed"
        result["message"] = stderr.strip() or "Query execution failed"
    
    return result


def format_table_output(rows: List[Dict[str, Any]], columns: List[str], max_width: int = 120):
    """Format results as a readable table."""
    if not rows:
        print("No results returned.")
        return
    
    if not columns:
        columns = list(rows[0].keys())
    
    # Calculate column widths
    widths = {}
    for col in columns:
        col_values = [str(row.get(col, ""))[:50] for row in rows]
        widths[col] = max(len(col), max(len(v) for v in col_values) if col_values else 0)
    
    # Adjust widths if total is too wide
    total_width = sum(widths.values()) + len(columns) * 3
    if total_width > max_width:
        scale = max_width / total_width
        widths = {k: max(5, int(v * scale)) for k, v in widths.items()}
    
    # Print header
    header = " | ".join(col[:widths[col]].ljust(widths[col]) for col in columns)
    print(header)
    print("-" * len(header))
    
    # Print rows
    for row in rows:
        row_str = " | ".join(
            str(row.get(col, ""))[:widths[col]].ljust(widths[col]) 
            for col in columns
        )
        print(row_str)


def format_csv_output(rows: List[Dict[str, Any]], columns: List[str]):
    """Format results as CSV."""
    if not rows:
        return
    
    if not columns:
        columns = list(rows[0].keys())
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
    print(output.getvalue())


def execute_query(
    database: str,
    query: Optional[str] = None,
    query_file: Optional[str] = None,
    inline: Optional[str] = None,
    timeout: int = 300,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Execute KQL query from file or inline."""
    
    database = ensure_database_suffix(database)
    
    report = {
        "database": database,
        "query_source": None,
        "query": None,
        "result": {}
    }
    
    # Verify database exists
    print(f"\nVerifying database: {database}")
    if not check_path_exists(database):
        print(f"Error: Database '{database}' does not exist or is not accessible")
        return report
    print("  Database found")
    
    # Determine query source
    if query_file:
        print(f"\nLoading query from file: {query_file}")
        try:
            kql_query = load_query_from_file(query_file)
            report["query_source"] = f"file:{query_file}"
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return report
    elif inline:
        kql_query = inline
        report["query_source"] = "inline"
    elif query:
        kql_query = query
        report["query_source"] = "argument"
    else:
        print("Error: Must provide --query, --file, or --inline")
        return report
    
    report["query"] = kql_query
    
    # Display query
    print("\nExecuting query:")
    query_lines = kql_query.split("\n")
    for line in query_lines[:5]:
        print(f"  {line}")
    if len(query_lines) > 5:
        print(f"  ... ({len(query_lines) - 5} more lines)")
    
    if limit:
        print(f"\nRow limit: {limit}")
    
    # Execute query
    print("\nRunning query...")
    result = execute_kql_query(database, kql_query, timeout=timeout, limit=limit)
    report["result"] = result
    
    if result["status"] == "success":
        print(f"  ✓ Query completed: {result['row_count']} row(s) returned")
        if result.get("execution_time_ms"):
            print(f"  Execution time: {result['execution_time_ms']}ms")
    else:
        print(f"  ✗ Query failed: {result['message']}")
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Execute KQL query and return results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Query from file
    python kql_query.py RealTime.Workspace/SensorDB.KQLDatabase --file queries/anomalies.kql

    # Inline query
    python kql_query.py RealTime.Workspace/SensorDB.KQLDatabase --inline "SensorData | take 10"

    # Query with row limit
    python kql_query.py RealTime.Workspace/SensorDB.KQLDatabase --inline "Logs | where Level == 'Error'" --limit 100

    # Output as CSV
    python kql_query.py RealTime.Workspace/SensorDB.KQLDatabase --file query.kql --format csv

KQL Query Examples:
    # Simple table scan
    SensorData | take 100

    # Filter and project
    Logs 
    | where Timestamp > ago(1h)
    | where Level == "Error"
    | project Timestamp, Message

    # Aggregation
    Metrics
    | summarize avg(Value), max(Value) by bin(Timestamp, 1h), DeviceId

    # Time series
    SensorData
    | where Timestamp > ago(24h)
    | summarize avg(Temperature) by bin(Timestamp, 1h)
    | render timechart
        """
    )
    parser.add_argument(
        "database",
        help="KQL database path (Workspace/Database.KQLDatabase)"
    )
    
    # Query source (mutually exclusive)
    query_group = parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument(
        "--file", "-f",
        dest="query_file",
        help="Path to KQL query file"
    )
    query_group.add_argument(
        "--inline", "-i",
        help="Inline KQL query string"
    )
    query_group.add_argument(
        "--query", "-q",
        help="KQL query string"
    )
    
    parser.add_argument(
        "--limit", "-l",
        type=int,
        help="Maximum number of rows to return"
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=300,
        help="Query timeout in seconds (default: 300)"
    )
    parser.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)"
    )
    
    args = parser.parse_args()
    
    try:
        report = execute_query(
            database=args.database,
            query=args.query,
            query_file=args.query_file,
            inline=args.inline,
            timeout=args.timeout,
            limit=args.limit
        )
        
        result = report.get("result", {})
        
        # Print results in requested format
        if result.get("status") == "success" and result.get("rows"):
            print("\n" + "=" * 50)
            print("QUERY RESULTS")
            print("=" * 50)
            
            if args.format == "json":
                print(json.dumps(result["rows"], indent=2, default=str))
            elif args.format == "csv":
                format_csv_output(result["rows"], result.get("columns", []))
            else:  # table
                format_table_output(result["rows"], result.get("columns", []))
            
            print("=" * 50)
            print(f"Rows: {result['row_count']}")
        
        # Exit code based on query status
        sys.exit(0 if result.get("status") == "success" else 1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
