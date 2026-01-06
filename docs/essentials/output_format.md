# Output Format

The Fabric CLI provides flexible output formatting options to support both human-readable and machine-parseable results. This document covers the output format feature, its configuration, usage patterns, and implementation guidelines.

## Overview

The output format feature allows users to control how command results are displayed. The CLI supports two primary output formats:
- **Text Format** (default): Human-readable, formatted output optimized for terminal viewing
- **JSON Format**: Structured, machine-parseable output suitable for scripting and automation

## Supported Output Formats

### Text Format (`text`)
The default format that provides human-readable output with:
- Clean, formatted display
- Headers for tabular data when using `-l` or `-q` flags
- Color-coded status indicators
- Progress indicators and informational messages
- Unix-style listings for directory-like commands

### JSON Format (`json`)
Structured output format that provides:
- Consistent JSON schema across all commands
- Machine-parseable results
- Standardized error reporting
- Timestamp and command metadata
- Support for hidden data with `--all` flag

## Configuration

### Command-Line Flag
Override the output format for any command using the global `--output_format` flag:

```bash
# Use JSON format for a single command
fab ls --output_format json

# Use text format explicitly
fab auth status --output_format text
```

**Available Values:**
- `json` - JSON structured output
- `text` - Human-readable text output (default)

### Configuration File
Set the default output format using the [`fab config set`](../commands/config/index.md) command:

```bash
# Set JSON as default format
fab config set output_format json

# Set text as default format (default)
fab config set output_format text

# View current setting
fab config get output_format
```

The configuration is stored in the user's Fabric CLI configuration file and applies to all subsequent commands unless overridden by the `--output_format` flag.

## JSON Output Schema

### Success Response Structure
```json
{
    "timestamp": "2026-01-06T08:00:00.000Z",
    "status": "Success",
    "command": "command_name",
    "result": {
        "data": [
            {
                "id": "example-id",
                "name": "example-name",
                "type": "example-type"
            }
        ],
        "hidden_data": [
            ".capacities",
            ".gateways"
        ],
        "message": "Operation completed successfully"
    }
}
```

### Error Response Structure
```json
{
    "timestamp": "2026-01-06T08:00:00.000Z",
    "status": "Failure",
    "command": "command_name",
    "result": {
        "message": "Unable to find workspace: workspace1",
        "error_code": "ERROR_WORKSPACE_NOT_FOUND"
    }
}
```

### JSON Schema Fields

#### Root Level
- **`timestamp`** (string): ISO 8601 UTC timestamp when the command completed
- **`status`** (string): Either `"Success"` or `"Failure"`
- **`command`** (string, optional): The primary command that was executed
- **`result`** (object): Contains the actual command results

#### Result Object
- **`data`** (array, optional): Primary output data when available
- **`hidden_data`** (array, optional): Virtual workspace items like capacities, gateways, managed private endpoints
- **`message`** (string, optional): Success message or operation description
- **`error_code`** (string, optional): Standardized error code (only present on failures)

## Text Output Behavior

### Success Output
Text format provides context-aware formatting:

```bash
# Basic directory listing (names only)
$ fab ls
workspace1
workspace2

# Directory listing with details (-l flag)
$ fab ls -l
name         id                                   capacityName  capacityId                             capacityRegion
---------------------------------------------------------------------------------------------------------------------
workspace1   12345678-1234-1234-1234-123456789012  MyCapacity    87654321-4321-4321-4321-210987654321  East US
workspace2   12345678-1234-1234-1234-123456789013  MyCapacity    87654321-4321-4321-4321-210987654321  East US

# Simple success message
$ fab auth logout
* Logged out of Fabric account

# Data with message (mkdir shows table by default)
$ fab mkdir workspace1
* 'workspace1' created
```

### Error Output
Error messages include the error code in brackets followed by the message:

```bash
$ fab ls invalid-workspace
x ls: [NotFound] The Workspace 'invalid-workspace.Workspace' could not be found
```

### Informational Output
Informational messages (warnings, progress, debug info) are always sent to `stderr` regardless of output format:

```bash
$ fab mv ws1.Workspace/r1.Report ws1.Workspace/
Moving '/ws.Workspace/r1.Report' → '/ws1.Workspace/r1.Report'...
* Move completed
```

## Stream Behavior

### Standard Output (stdout)
- **All command results** (both success and error responses)
- **JSON format**: All JSON responses
- **Text format**: Command results, data, and final status messages

### Standard Error (stderr)  
- Warning messages ([`print_warning()`](../../src/fabric_cli/utils/fab_ui.py:151))
- Informational messages ([`print_info()`](../../src/fabric_cli/utils/fab_ui.py:204))
- Debug messages ([`print_grey()`](../../src/fabric_cli/utils/fab_ui.py:77))
- Progress indicators ([`print_progress()`](../../src/fabric_cli/utils/fab_ui.py:81))

This separation allows users to:
- Redirect command results to files while preserving interactive feedback
- Filter informational messages separately from actual data
- Pipe JSON output to processing tools without interference

## Examples

### Basic Usage
```bash
# List workspaces in text format (names only)
$ fab ls
workspace1
workspace2

# Same command with JSON output
$ fab ls --output_format json
{
    "timestamp": "2026-01-06T08:00:00.000Z",
    "status": "Success",
    "command": "ls", 
    "result": {
        "data": [
            {
                "name": "workspace1"
            },
            {
                "name": "workspace2"
            }
        ]
    }
}
```

### Configuration Examples
```bash
# Check current output format
$ fab config get output_format
text

# Change to JSON as default
$ fab config set output_format json
* Configuration 'output_format' set to 'json'

# All subsequent commands use JSON
$ fab auth status
{
    "timestamp": "2026-01-06T08:00:00.000Z",
    "status": "Success",
    "command": "auth",
    "result": {
        "data": [
            {
                "logged_in": "true",
                "account": "user@example.com",
                "tenant_id": "12345678-1234-1234-1234-123456789012"
            }
        ]
    }
}

# Override for single command
$ fab auth status --output_format text
Logged In: true
Account: user@example.com
Tenant ID: 12345678-1234-1234-1234-123456789012
```

## Implementation for Developers

### Using Output Functions

When implementing CLI commands, use the designated output functions:

#### Success Results
```python
from fabric_cli.utils import fab_ui

# Return data with headers
fab_ui.print_output_format(
    args, 
    data=[{"name": "workspace1", "type": "Workspace"}],
    show_headers=True
)

# Return simple success message
fab_ui.print_output_format(
    args, 
    message="Operation completed successfully"
)

# Return data with hidden information (virtual workspace items)
fab_ui.print_output_format(
    args,
    data=[{"name": "item1"}],
    hidden_data=[".capacities", ".gateways"]
)
```

#### Error Results
```python
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.utils import fab_ui

try:
    # Command logic here
    pass
except SomeException:
    fab_ui.print_output_error(
        FabricCLIError(
            "Unable to complete operation",
            "ERROR_OPERATION_FAILED"
        ),
        command=args.command
    )
```

#### Informational Output
```python
from fabric_cli.utils import fab_ui

# Progress updates (to stderr)
fab_ui.print_progress("Processing items", progress=75)

# Warnings (to stderr) 
fab_ui.print_warning("This feature will be deprecated")

# Debug/info messages (to stderr)
fab_ui.print_grey("Processing request...")
```

### Key Implementation Guidelines

1. **Use designated output functions**: Always use [`print_output_format()`](../../src/fabric_cli/utils/fab_ui.py:91) for command results and [`print_output_error()`](../../src/fabric_cli/utils/fab_ui.py:163) for errors
2. **Separate concerns**: Use [`print_info()`](../../src/fabric_cli/utils/fab_ui.py:204), [`print_warning()`](../../src/fabric_cli/utils/fab_ui.py:151), and [`print_grey()`](../../src/fabric_cli/utils/fab_ui.py:77) for supplementary information that goes to stderr
3. **Test both formats**: Ensure commands work correctly with both `--output_format json` and `--output_format text`
4. **Consistent data structure**: Provide consistent field names and data types across similar commands
5. **Meaningful error codes**: Use standardized error codes from [`fab_constant.py`](../../src/fabric_cli/core/fab_constant.py) and reuse existing values when possible

## Best Practices

### For Users
1. **Automation**: Set `output_format json` in config for scripts and automation
2. **Interactive use**: Keep the default `text` format for better readability
3. **Command-specific override**: Use `--output_format json/text` for specific commands if needed to override the config value

### For Developers
1. **Consistency**: Follow the established JSON schema across all commands
2. **Error codes**: Use meaningful, standardized error codes for different failure scenarios and reuse existing values when possible
3. **Stream separation**: Send informational messages to stderr, results to stdout
4. **Testing**: Test commands with both output formats to ensure compatibility

## Related Documentation

- [Configuration Management](settings.md) - Managing CLI settings and preferences
- [Parameters](parameters.md) - Global flags and command parameters  
- [Exit Codes](exit_codes.md) - Understanding command exit codes
- [Examples](../examples/index.md) - Practical usage examples across different commands