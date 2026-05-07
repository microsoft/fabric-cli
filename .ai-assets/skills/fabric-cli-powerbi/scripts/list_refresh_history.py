#!/usr/bin/env python3
"""
list_refresh_history.py - Show refresh history and failure details

This script displays the refresh history for a semantic model, including
duration, status, and error details.

Usage:
    python list_refresh_history.py <model> [--last N]
    python list_refresh_history.py Production.Workspace/Sales.SemanticModel --last 10

Exit codes:
    0 - History retrieved successfully
    1 - Failed to retrieve history
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
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


def ensure_semantic_model_suffix(path: str) -> str:
    """Ensure path has .SemanticModel suffix if it's just a model path."""
    # If it already ends with a type suffix, return as is
    known_suffixes = [".SemanticModel", ".Dataset", ".Workspace"]
    for suffix in known_suffixes:
        if path.endswith(suffix):
            return path
    
    # If path contains a workspace but no model type, add SemanticModel
    if "/" in path and not path.split("/")[-1].count("."):
        return f"{path}.SemanticModel"
    
    return path


def check_path_exists(path: str) -> bool:
    """Check if path exists."""
    exit_code, _, _ = run_fab_command(["exists", path])
    return exit_code == 0


def get_refresh_history(model_path: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get refresh history for a semantic model."""
    # Use the jobs list command to get refresh history
    cmd = ["jobs", "list", model_path, "-t", "Refresh", "-l", str(limit), "-f", "json"]
    
    exit_code, stdout, stderr = run_fab_command(cmd)
    
    if exit_code == 0:
        try:
            result = json.loads(stdout.strip())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
    
    return []


def get_job_details(job_id: str, model_path: str) -> Dict[str, Any]:
    """Get detailed information about a specific job."""
    cmd = ["jobs", "get", model_path, "-j", job_id, "-f", "json"]
    
    exit_code, stdout, stderr = run_fab_command(cmd)
    
    if exit_code == 0:
        try:
            return json.loads(stdout.strip())
        except json.JSONDecodeError:
            pass
    
    return {}


def format_duration(start_time: str, end_time: str) -> str:
    """Format duration between two ISO timestamps."""
    try:
        start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        duration = end - start
        
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except:
        return "N/A"


def format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp for display."""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return timestamp


def analyze_failure_patterns(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze refresh history for failure patterns."""
    analysis = {
        "total_refreshes": len(history),
        "successful": 0,
        "failed": 0,
        "cancelled": 0,
        "in_progress": 0,
        "success_rate": 0.0,
        "avg_duration_seconds": 0,
        "common_errors": {},
        "recent_failures": []
    }
    
    durations = []
    
    for refresh in history:
        status = refresh.get("status", "").lower()
        
        if status in ["completed", "succeeded", "success"]:
            analysis["successful"] += 1
            
            # Calculate duration for successful refreshes
            start = refresh.get("startTime", refresh.get("startDateTime"))
            end = refresh.get("endTime", refresh.get("endDateTime"))
            if start and end:
                try:
                    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                    durations.append((end_dt - start_dt).total_seconds())
                except:
                    pass
                    
        elif status in ["failed", "error"]:
            analysis["failed"] += 1
            
            # Track error messages
            error_msg = refresh.get("error", refresh.get("errorMessage", "Unknown error"))
            if error_msg:
                analysis["common_errors"][error_msg] = analysis["common_errors"].get(error_msg, 0) + 1
            
            # Track recent failures
            if len(analysis["recent_failures"]) < 5:
                analysis["recent_failures"].append({
                    "time": refresh.get("startTime", refresh.get("startDateTime", "Unknown")),
                    "error": error_msg
                })
                
        elif status in ["cancelled", "canceled"]:
            analysis["cancelled"] += 1
            
        elif status in ["running", "in_progress", "inprogress"]:
            analysis["in_progress"] += 1
    
    # Calculate success rate
    completed = analysis["successful"] + analysis["failed"]
    if completed > 0:
        analysis["success_rate"] = round(analysis["successful"] / completed * 100, 1)
    
    # Calculate average duration
    if durations:
        analysis["avg_duration_seconds"] = round(sum(durations) / len(durations), 1)
    
    return analysis


def print_refresh_table(history: List[Dict[str, Any]]):
    """Print refresh history in a formatted table."""
    if not history:
        print("No refresh history found.")
        return
    
    # Table header
    print("\n{:<6} {:<22} {:<12} {:<12} {}".format(
        "#", "Started", "Duration", "Status", "Details"
    ))
    print("-" * 80)
    
    for i, refresh in enumerate(history, 1):
        # Extract fields
        start_time = refresh.get("startTime", refresh.get("startDateTime", "N/A"))
        end_time = refresh.get("endTime", refresh.get("endDateTime", ""))
        status = refresh.get("status", "Unknown")
        error = refresh.get("error", refresh.get("errorMessage", ""))
        
        # Format values
        start_formatted = format_timestamp(start_time)[:22] if start_time != "N/A" else "N/A"
        duration = format_duration(start_time, end_time) if end_time else "Running"
        
        # Status emoji
        status_display = status
        if status.lower() in ["completed", "succeeded", "success"]:
            status_display = "✓ Success"
        elif status.lower() in ["failed", "error"]:
            status_display = "✗ Failed"
        elif status.lower() in ["running", "in_progress"]:
            status_display = "⟳ Running"
        elif status.lower() in ["cancelled", "canceled"]:
            status_display = "⊘ Cancelled"
        
        # Details (truncate if too long)
        details = error[:30] + "..." if len(error) > 30 else error
        
        print("{:<6} {:<22} {:<12} {:<12} {}".format(
            i, start_formatted, duration, status_display, details
        ))


def list_refresh_history(
    model_path: str,
    limit: int = 10,
    show_details: bool = False
) -> Dict[str, Any]:
    """List refresh history for a semantic model."""
    
    model_path = ensure_semantic_model_suffix(model_path)
    
    report = {
        "model": model_path,
        "limit": limit,
        "history": [],
        "analysis": {}
    }
    
    # Verify model exists
    print(f"\nVerifying model: {model_path}")
    if not check_path_exists(model_path):
        print(f"Error: Model '{model_path}' does not exist or is not accessible")
        return report
    print("  Model found")
    
    # Get refresh history
    print(f"\nFetching refresh history (last {limit})...")
    history = get_refresh_history(model_path, limit)
    report["history"] = history
    
    if not history:
        print("  No refresh history found")
        return report
    
    print(f"  Found {len(history)} refresh record(s)")
    
    # Get additional details if requested
    if show_details:
        print("\nFetching detailed information...")
        for i, refresh in enumerate(history):
            job_id = refresh.get("id", refresh.get("jobId"))
            if job_id:
                details = get_job_details(job_id, model_path)
                if details:
                    history[i].update(details)
    
    # Print table
    print_refresh_table(history)
    
    # Analyze patterns
    print("\nAnalyzing refresh patterns...")
    analysis = analyze_failure_patterns(history)
    report["analysis"] = analysis
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Show refresh history and failure details for a semantic model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python list_refresh_history.py Production.Workspace/Sales.SemanticModel
    python list_refresh_history.py Production.Workspace/Sales.SemanticModel --last 20
    python list_refresh_history.py "My Workspace/Revenue Model" --last 5 --details

Output includes:
    - Refresh start time
    - Duration
    - Status (Success, Failed, Running, Cancelled)
    - Error details for failed refreshes
    - Success rate analysis
    - Common error patterns
        """
    )
    parser.add_argument(
        "model",
        help="Semantic model path (Workspace/Model.SemanticModel)"
    )
    parser.add_argument(
        "--last", "-n",
        type=int,
        default=10,
        help="Number of recent refreshes to show (default: 10)"
    )
    parser.add_argument(
        "--details", "-d",
        action="store_true",
        help="Fetch detailed information for each refresh"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    try:
        report = list_refresh_history(
            model_path=args.model,
            limit=args.last,
            show_details=args.details
        )
        
        # Print analysis summary
        if report["analysis"]:
            analysis = report["analysis"]
            print("\n" + "=" * 50)
            print("REFRESH ANALYSIS")
            print("=" * 50)
            print(f"Total Refreshes: {analysis['total_refreshes']}")
            print(f"  Successful: {analysis['successful']}")
            print(f"  Failed: {analysis['failed']}")
            print(f"  Cancelled: {analysis['cancelled']}")
            print(f"  In Progress: {analysis['in_progress']}")
            print(f"\nSuccess Rate: {analysis['success_rate']}%")
            
            if analysis['avg_duration_seconds'] > 0:
                avg_mins = analysis['avg_duration_seconds'] / 60
                print(f"Avg Duration: {avg_mins:.1f} minutes")
            
            if analysis['common_errors']:
                print("\nCommon Errors:")
                for error, count in sorted(analysis['common_errors'].items(), key=lambda x: -x[1])[:3]:
                    print(f"  [{count}x] {error[:60]}...")
            
            print("=" * 50)
        
        if args.json:
            print("\n" + json.dumps(report, indent=2, default=str))
        
        # Exit code: 0 if we got history, 1 if not
        sys.exit(0 if report['history'] else 1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
