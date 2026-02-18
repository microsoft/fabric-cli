#!/usr/bin/env python3
"""
diff_definitions.py - Compare item definitions between environments

This script compares Fabric item definitions between two sources (workspaces or
local exports) and outputs the differences.

Usage:
    python diff_definitions.py <item1> <item2>
    python diff_definitions.py Dev.Workspace/Model.SemanticModel Prod.Workspace/Model.SemanticModel
    python diff_definitions.py ./local-export/Model.SemanticModel Prod.Workspace/Model.SemanticModel

Exit codes:
    0 - Items are identical
    1 - Items are different or error occurred
"""

import argparse
import difflib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


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


def is_local_path(path: str) -> bool:
    """Check if path is a local filesystem path."""
    # Local paths start with . or / or drive letter
    return path.startswith((".", "/", "\\")) or (len(path) > 1 and path[1] == ":")


def get_item_type_from_path(path: str) -> Optional[str]:
    """Extract item type from path."""
    item_types = [
        "Workspace", "Lakehouse", "Warehouse", "SemanticModel", "Report",
        "Notebook", "SparkJobDefinition", "DataPipeline", "KQLDatabase",
        "KQLDashboard", "KQLQueryset", "Eventhouse", "Eventstream",
        "MirroredDatabase", "Reflex", "MountedDataFactory", "CopyJob"
    ]
    
    for item_type in item_types:
        if path.endswith(f".{item_type}"):
            return item_type
        if f".{item_type}/" in path or f".{item_type}\\" in path:
            return item_type
    
    return None


def export_item_definition(item_path: str, output_dir: str) -> Tuple[bool, str]:
    """Export item definition from Fabric to local directory."""
    exit_code, stdout, stderr = run_fab_command([
        "export", item_path, "-d", output_dir, "-f", "json"
    ])
    
    if exit_code == 0:
        return True, output_dir
    return False, stderr


def load_local_definition(local_path: str) -> Dict[str, Any]:
    """Load item definition from local path."""
    result = {
        "path": local_path,
        "files": {},
        "metadata": {}
    }
    
    path = Path(local_path)
    
    if not path.exists():
        return {"error": f"Path does not exist: {local_path}"}
    
    if path.is_file():
        # Single file comparison
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        result["files"][path.name] = content
        return result
    
    # Directory - load all relevant files
    for file_path in path.rglob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(path))
            
            # Skip certain files
            if any(skip in rel_path for skip in [".git", "__pycache__", ".DS_Store"]):
                continue
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                result["files"][rel_path] = content
            except UnicodeDecodeError:
                # Binary file - store hash or skip
                result["files"][rel_path] = f"<binary file: {file_path.stat().st_size} bytes>"
    
    # Load metadata if exists
    platform_file = path / ".platform"
    if platform_file.exists():
        try:
            with open(platform_file, "r", encoding="utf-8") as f:
                result["metadata"]["platform"] = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    
    return result


def get_definition(source: str, temp_dir: str) -> Tuple[Dict[str, Any], str]:
    """Get item definition from source (local path or Fabric path)."""
    if is_local_path(source):
        definition = load_local_definition(source)
        return definition, source
    else:
        # Export from Fabric to temp directory
        item_name = source.split("/")[-1] if "/" in source else source
        export_path = os.path.join(temp_dir, item_name.replace(".", "_"))
        
        success, result = export_item_definition(source, export_path)
        if success:
            definition = load_local_definition(export_path)
            return definition, export_path
        else:
            return {"error": result}, ""


def normalize_json_content(content: str) -> str:
    """Normalize JSON content for comparison (sort keys, consistent formatting)."""
    try:
        data = json.loads(content)
        # Remove volatile fields
        volatile_fields = ["lastModifiedTime", "modifiedDateTime", "createdDateTime", "id"]
        
        def remove_volatile(obj):
            if isinstance(obj, dict):
                return {k: remove_volatile(v) for k, v in obj.items() if k not in volatile_fields}
            elif isinstance(obj, list):
                return [remove_volatile(item) for item in obj]
            return obj
        
        cleaned = remove_volatile(data)
        return json.dumps(cleaned, indent=2, sort_keys=True)
    except json.JSONDecodeError:
        return content


def compare_definitions(def1: Dict[str, Any], def2: Dict[str, Any], 
                       ignore_metadata: bool = False) -> Dict[str, Any]:
    """Compare two item definitions."""
    result = {
        "identical": True,
        "differences": [],
        "only_in_source1": [],
        "only_in_source2": [],
        "modified_files": []
    }
    
    if "error" in def1:
        return {"error": f"Source 1 error: {def1['error']}"}
    if "error" in def2:
        return {"error": f"Source 2 error: {def2['error']}"}
    
    files1 = def1.get("files", {})
    files2 = def2.get("files", {})
    
    all_files = set(files1.keys()) | set(files2.keys())
    
    for file_name in sorted(all_files):
        # Skip metadata files if requested
        if ignore_metadata and file_name in [".platform", "item.metadata.json"]:
            continue
        
        content1 = files1.get(file_name)
        content2 = files2.get(file_name)
        
        if content1 is None:
            result["only_in_source2"].append(file_name)
            result["identical"] = False
        elif content2 is None:
            result["only_in_source1"].append(file_name)
            result["identical"] = False
        else:
            # Normalize JSON files for comparison
            if file_name.endswith(".json"):
                content1_normalized = normalize_json_content(content1)
                content2_normalized = normalize_json_content(content2)
            else:
                content1_normalized = content1
                content2_normalized = content2
            
            if content1_normalized != content2_normalized:
                result["identical"] = False
                result["modified_files"].append(file_name)
                
                # Generate diff
                diff = list(difflib.unified_diff(
                    content1_normalized.splitlines(keepends=True),
                    content2_normalized.splitlines(keepends=True),
                    fromfile=f"source1/{file_name}",
                    tofile=f"source2/{file_name}",
                    lineterm=""
                ))
                
                result["differences"].append({
                    "file": file_name,
                    "diff": "".join(diff)
                })
    
    return result


def print_comparison_report(result: Dict[str, Any], source1: str, source2: str,
                           output_format: str, output_file: Optional[str] = None):
    """Print comparison report."""
    if output_format == "json":
        report = {
            "source1": source1,
            "source2": source2,
            **result
        }
        output = json.dumps(report, indent=2)
    else:
        # Text format
        lines = []
        lines.append("=" * 70)
        lines.append("ITEM DEFINITION COMPARISON")
        lines.append("=" * 70)
        lines.append(f"Source 1: {source1}")
        lines.append(f"Source 2: {source2}")
        lines.append("")
        
        if "error" in result:
            lines.append(f"ERROR: {result['error']}")
        else:
            if result["identical"]:
                lines.append("RESULT: Items are IDENTICAL")
            else:
                lines.append("RESULT: Items are DIFFERENT")
                lines.append("")
                
                if result["only_in_source1"]:
                    lines.append("Files only in source 1:")
                    for f in result["only_in_source1"]:
                        lines.append(f"  - {f}")
                    lines.append("")
                
                if result["only_in_source2"]:
                    lines.append("Files only in source 2:")
                    for f in result["only_in_source2"]:
                        lines.append(f"  + {f}")
                    lines.append("")
                
                if result["modified_files"]:
                    lines.append("Modified files:")
                    for f in result["modified_files"]:
                        lines.append(f"  ~ {f}")
                    lines.append("")
                
                if result["differences"]:
                    lines.append("-" * 70)
                    lines.append("DETAILED DIFFERENCES:")
                    lines.append("-" * 70)
                    for diff_info in result["differences"]:
                        lines.append(f"\n{diff_info['file']}:")
                        lines.append(diff_info["diff"])
        
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
        description="Compare item definitions between environments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Compare items between workspaces
    python diff_definitions.py Dev.Workspace/Model.SemanticModel Prod.Workspace/Model.SemanticModel
    
    # Compare local export to workspace
    python diff_definitions.py ./exports/Model.SemanticModel Production.Workspace/Model.SemanticModel
    
    # Compare two local exports
    python diff_definitions.py ./dev-export/Model.SemanticModel ./prod-export/Model.SemanticModel
    
    # Output as JSON
    python diff_definitions.py Dev.Workspace/Model Prod.Workspace/Model -f json -o diff.json
        """
    )
    
    parser.add_argument(
        "source1",
        help="First item path (workspace path or local directory)"
    )
    
    parser.add_argument(
        "source2",
        help="Second item path (workspace path or local directory)"
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
        "--ignore-metadata",
        action="store_true",
        help="Ignore metadata files (.platform, item.metadata.json) in comparison"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Create temp directory for exports
    with tempfile.TemporaryDirectory() as temp_dir:
        if args.verbose:
            print(f"Using temp directory: {temp_dir}", file=sys.stderr)
        
        # Get definitions
        if args.verbose:
            print(f"Loading source 1: {args.source1}", file=sys.stderr)
        def1, path1 = get_definition(args.source1, os.path.join(temp_dir, "source1"))
        
        if args.verbose:
            print(f"Loading source 2: {args.source2}", file=sys.stderr)
        def2, path2 = get_definition(args.source2, os.path.join(temp_dir, "source2"))
        
        # Compare
        if args.verbose:
            print("Comparing definitions...", file=sys.stderr)
        comparison = compare_definitions(def1, def2, ignore_metadata=args.ignore_metadata)
        
        # Output report
        print_comparison_report(comparison, args.source1, args.source2, args.format, args.output)
        
        # Return exit code
        if "error" in comparison:
            return 1
        return 0 if comparison.get("identical", False) else 1


if __name__ == "__main__":
    sys.exit(main())
