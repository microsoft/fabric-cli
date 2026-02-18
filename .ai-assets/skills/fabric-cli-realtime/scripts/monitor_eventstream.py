#!/usr/bin/env python3
"""
monitor_eventstream.py - Check eventstream health and throughput

This script monitors the health and performance of an eventstream in Microsoft Fabric,
checking status, throughput metrics, and error counts.

Usage:
    python monitor_eventstream.py <eventstream>
    python monitor_eventstream.py RealTime.Workspace/SensorStream.Eventstream

Exit codes:
    0 - Eventstream is healthy
    1 - Eventstream has issues or error occurred
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


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
    """Parse JSON output from fab CLI."""
    try:
        return json.loads(output.strip())
    except json.JSONDecodeError:
        return None


def parse_eventstream_path(path: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse workspace and eventstream name from path."""
    parts = path.split("/")
    if len(parts) != 2:
        return None, None
    
    workspace = parts[0]
    eventstream = parts[1]
    
    # Ensure workspace suffix
    if not workspace.endswith(".Workspace"):
        workspace = f"{workspace}.Workspace"
    
    # Ensure eventstream suffix
    if not eventstream.endswith(".Eventstream"):
        eventstream = f"{eventstream}.Eventstream"
    
    return workspace, eventstream


def check_path_exists(path: str) -> bool:
    """Check if path exists."""
    exit_code, _, _ = run_fab_command(["exists", path])
    return exit_code == 0


def get_item_details(path: str) -> Dict[str, Any]:
    """Get item details."""
    exit_code, stdout, stderr = run_fab_command(["get", path, "-f", "json"])
    
    if exit_code == 0:
        return parse_json_output(stdout) or {"error": "Failed to parse item details"}
    return {"error": stderr.strip() or "Failed to get item details"}


def get_item_id(path: str) -> Optional[str]:
    """Get item ID from path."""
    exit_code, stdout, stderr = run_fab_command(["get", path, "-q", "id", "-f", "json"])
    
    if exit_code == 0:
        result = parse_json_output(stdout)
        if isinstance(result, str):
            return result.strip('"')
        return result
    return None


def get_eventstream_status(workspace_id: str, eventstream_id: str) -> Dict[str, Any]:
    """Get eventstream status via API."""
    
    # Try to get eventstream details from the API
    api_path = f"/workspaces/{workspace_id}/eventstreams/{eventstream_id}"
    
    exit_code, stdout, stderr = run_fab_command([
        "api", "get", api_path,
        "-f", "json"
    ], timeout=30)
    
    if exit_code == 0:
        return parse_json_output(stdout) or {"error": "Failed to parse response"}
    return {"error": stderr}


def get_eventstream_metrics(workspace_id: str, eventstream_id: str) -> Dict[str, Any]:
    """Get eventstream metrics if available."""
    
    metrics = {
        "input_events": None,
        "output_events": None,
        "errors": None,
        "lag": None,
        "last_updated": None
    }
    
    # Try to get metrics from monitoring API
    # Note: This is a placeholder - actual API may differ
    api_path = f"/workspaces/{workspace_id}/eventstreams/{eventstream_id}/metrics"
    
    exit_code, stdout, stderr = run_fab_command([
        "api", "get", api_path,
        "-f", "json"
    ], timeout=30)
    
    if exit_code == 0:
        data = parse_json_output(stdout)
        if data:
            metrics["input_events"] = data.get("inputEventsTotal") or data.get("inputEvents")
            metrics["output_events"] = data.get("outputEventsTotal") or data.get("outputEvents")
            metrics["errors"] = data.get("errorCount") or data.get("errors")
            metrics["lag"] = data.get("lagMs") or data.get("lag")
            metrics["last_updated"] = datetime.now().isoformat()
    
    return metrics


def get_eventstream_sources_sinks(workspace_id: str, eventstream_id: str) -> Dict[str, Any]:
    """Get eventstream sources and sinks configuration."""
    
    result = {
        "sources": [],
        "sinks": []
    }
    
    # Try to get source/sink configuration
    api_path = f"/workspaces/{workspace_id}/eventstreams/{eventstream_id}/configuration"
    
    exit_code, stdout, stderr = run_fab_command([
        "api", "get", api_path,
        "-f", "json"
    ], timeout=30)
    
    if exit_code == 0:
        data = parse_json_output(stdout)
        if data:
            result["sources"] = data.get("sources", [])
            result["sinks"] = data.get("sinks", []) or data.get("destinations", [])
    
    return result


def analyze_health(details: Dict[str, Any], metrics: Dict[str, Any], 
                   config: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze eventstream health based on collected data."""
    
    health = {
        "status": "unknown",
        "score": 0,
        "checks": [],
        "warnings": [],
        "recommendations": []
    }
    
    max_score = 0
    actual_score = 0
    
    # Check 1: Eventstream exists and has basic info
    max_score += 20
    if details and "error" not in details:
        actual_score += 20
        health["checks"].append({
            "name": "eventstream_accessible",
            "passed": True,
            "message": "Eventstream is accessible"
        })
    else:
        health["checks"].append({
            "name": "eventstream_accessible",
            "passed": False,
            "message": f"Could not access eventstream: {details.get('error', 'Unknown')}"
        })
    
    # Check 2: Has configured sources
    max_score += 20
    sources = config.get("sources", [])
    if sources:
        actual_score += 20
        health["checks"].append({
            "name": "has_sources",
            "passed": True,
            "message": f"Eventstream has {len(sources)} configured source(s)"
        })
    else:
        health["checks"].append({
            "name": "has_sources",
            "passed": False,
            "message": "No sources configured"
        })
        health["recommendations"].append("Configure at least one data source for the eventstream")
    
    # Check 3: Has configured sinks
    max_score += 20
    sinks = config.get("sinks", [])
    if sinks:
        actual_score += 20
        health["checks"].append({
            "name": "has_sinks",
            "passed": True,
            "message": f"Eventstream has {len(sinks)} configured sink(s)"
        })
    else:
        health["warnings"].append("No sinks/destinations configured")
        health["checks"].append({
            "name": "has_sinks",
            "passed": False,
            "message": "No sinks configured"
        })
        health["recommendations"].append("Configure at least one destination for the eventstream")
    
    # Check 4: Error rate
    max_score += 20
    error_count = metrics.get("errors")
    if error_count is not None:
        if error_count == 0:
            actual_score += 20
            health["checks"].append({
                "name": "no_errors",
                "passed": True,
                "message": "No errors detected"
            })
        else:
            # Partial score based on error severity
            health["checks"].append({
                "name": "no_errors",
                "passed": False,
                "message": f"Detected {error_count} error(s)"
            })
            health["warnings"].append(f"Eventstream has {error_count} errors")
            health["recommendations"].append("Review eventstream error logs to identify and fix issues")
    else:
        actual_score += 10  # Neutral if we can't check
        health["checks"].append({
            "name": "no_errors",
            "passed": True,
            "message": "Error metrics not available"
        })
    
    # Check 5: Throughput/Activity
    max_score += 20
    input_events = metrics.get("input_events")
    output_events = metrics.get("output_events")
    
    if input_events is not None:
        if input_events > 0:
            actual_score += 20
            health["checks"].append({
                "name": "has_throughput",
                "passed": True,
                "message": f"Processing events (input: {input_events}, output: {output_events or 'N/A'})"
            })
        else:
            health["checks"].append({
                "name": "has_throughput",
                "passed": False,
                "message": "No events being processed"
            })
            health["warnings"].append("Eventstream shows no event activity")
            health["recommendations"].append("Verify that sources are sending data")
    else:
        actual_score += 10  # Neutral if we can't check
        health["checks"].append({
            "name": "has_throughput",
            "passed": True,
            "message": "Throughput metrics not available"
        })
    
    # Calculate overall score
    health["score"] = int((actual_score / max_score) * 100) if max_score > 0 else 0
    
    # Determine status
    if health["score"] >= 80:
        health["status"] = "healthy"
    elif health["score"] >= 60:
        health["status"] = "warning"
    else:
        health["status"] = "unhealthy"
    
    return health


def print_monitoring_report(result: Dict[str, Any], output_format: str, 
                           output_file: Optional[str] = None):
    """Print monitoring report."""
    if output_format == "json":
        output = json.dumps(result, indent=2)
    else:
        # Text format
        lines = []
        lines.append("=" * 70)
        lines.append("EVENTSTREAM MONITORING REPORT")
        lines.append("=" * 70)
        lines.append(f"Eventstream: {result['eventstream']}")
        lines.append(f"Timestamp: {result.get('timestamp', 'Unknown')}")
        lines.append("")
        
        health = result.get("health", {})
        status = health.get("status", "unknown").upper()
        score = health.get("score", 0)
        
        status_icon = {
            "HEALTHY": "✓",
            "WARNING": "⚠",
            "UNHEALTHY": "✗",
            "UNKNOWN": "?"
        }.get(status, "?")
        
        lines.append(f"STATUS: {status_icon} {status} (Health Score: {score}%)")
        lines.append("")
        
        # Health checks
        lines.append("HEALTH CHECKS:")
        for check in health.get("checks", []):
            icon = "✓" if check["passed"] else "✗"
            lines.append(f"  {icon} {check['name']}: {check['message']}")
        lines.append("")
        
        # Metrics
        metrics = result.get("metrics", {})
        if any(v is not None for v in metrics.values()):
            lines.append("METRICS:")
            if metrics.get("input_events") is not None:
                lines.append(f"  Input Events: {metrics['input_events']}")
            if metrics.get("output_events") is not None:
                lines.append(f"  Output Events: {metrics['output_events']}")
            if metrics.get("errors") is not None:
                lines.append(f"  Errors: {metrics['errors']}")
            if metrics.get("lag") is not None:
                lines.append(f"  Lag: {metrics['lag']} ms")
            lines.append("")
        
        # Configuration
        config = result.get("configuration", {})
        sources = config.get("sources", [])
        sinks = config.get("sinks", [])
        
        lines.append("CONFIGURATION:")
        lines.append(f"  Sources: {len(sources)}")
        for src in sources[:5]:  # Show first 5
            name = src.get("name") or src.get("type", "Unknown")
            lines.append(f"    - {name}")
        if len(sources) > 5:
            lines.append(f"    ... and {len(sources) - 5} more")
        
        lines.append(f"  Sinks/Destinations: {len(sinks)}")
        for sink in sinks[:5]:  # Show first 5
            name = sink.get("name") or sink.get("type", "Unknown")
            lines.append(f"    - {name}")
        if len(sinks) > 5:
            lines.append(f"    ... and {len(sinks) - 5} more")
        lines.append("")
        
        # Warnings
        if health.get("warnings"):
            lines.append("WARNINGS:")
            for warning in health["warnings"]:
                lines.append(f"  ⚠ {warning}")
            lines.append("")
        
        # Recommendations
        if health.get("recommendations"):
            lines.append("RECOMMENDATIONS:")
            for rec in health["recommendations"]:
                lines.append(f"  → {rec}")
            lines.append("")
        
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
        description="Check eventstream health and throughput",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python monitor_eventstream.py RealTime.Workspace/SensorStream.Eventstream
    python monitor_eventstream.py MyWorkspace/MyEventstream -f json
    python monitor_eventstream.py Production.Workspace/TelemetryStream.Eventstream -o report.json
        """
    )
    
    parser.add_argument(
        "eventstream",
        help="Eventstream path (e.g., 'MyWorkspace.Workspace/MyEventstream.Eventstream')"
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
    
    # Parse eventstream path
    workspace, eventstream = parse_eventstream_path(args.eventstream)
    if not workspace or not eventstream:
        print(f"Error: Invalid eventstream path: {args.eventstream}", file=sys.stderr)
        print("Expected format: Workspace.Workspace/Eventstream.Eventstream", file=sys.stderr)
        return 1
    
    eventstream_path = f"{workspace}/{eventstream}"
    
    if args.verbose:
        print(f"Monitoring eventstream: {eventstream_path}", file=sys.stderr)
    
    # Check eventstream exists
    if not check_path_exists(eventstream_path):
        print(f"Error: Eventstream does not exist: {eventstream_path}", file=sys.stderr)
        return 1
    
    # Get IDs
    if args.verbose:
        print("Getting item IDs...", file=sys.stderr)
    
    workspace_id = get_item_id(workspace)
    eventstream_id = get_item_id(eventstream_path)
    
    if not workspace_id or not eventstream_id:
        print("Error: Could not get workspace or eventstream ID", file=sys.stderr)
        return 1
    
    # Get eventstream details
    if args.verbose:
        print("Getting eventstream details...", file=sys.stderr)
    
    details = get_item_details(eventstream_path)
    
    # Get status
    if args.verbose:
        print("Getting eventstream status...", file=sys.stderr)
    
    status = get_eventstream_status(workspace_id, eventstream_id)
    
    # Get metrics
    if args.verbose:
        print("Getting metrics...", file=sys.stderr)
    
    metrics = get_eventstream_metrics(workspace_id, eventstream_id)
    
    # Get configuration
    if args.verbose:
        print("Getting configuration...", file=sys.stderr)
    
    config = get_eventstream_sources_sinks(workspace_id, eventstream_id)
    
    # Analyze health
    if args.verbose:
        print("Analyzing health...", file=sys.stderr)
    
    health = analyze_health(details, metrics, config)
    
    # Build result
    result = {
        "eventstream": eventstream_path,
        "timestamp": datetime.now().isoformat(),
        "workspace_id": workspace_id,
        "eventstream_id": eventstream_id,
        "details": details if "error" not in details else None,
        "metrics": metrics,
        "configuration": config,
        "health": health
    }
    
    # Output report
    print_monitoring_report(result, args.format, args.output)
    
    # Return exit code based on health status
    if health["status"] == "unhealthy":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
