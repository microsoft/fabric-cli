# Output Format - User Guide

The Fabric CLI provides flexible output formatting options to support both human-readable and machine-parseable results. This guide covers how to configure and use output formats effectively.

## Overview

The output format feature allows you to control how command results are displayed. The CLI supports two primary output formats:
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
Set the default output format using the [`fab config set`](../examples/config_examples.md) command:

```bash
# Set JSON as default format
fab config set output_format json

# Set text as default format (default)
fab config set output_format text

# View current setting
fab config get output_format
```

The configuration is stored in your Fabric CLI configuration file and applies to all subsequent commands unless overridden by the `--output_format` flag.

## JSON Help

Help uses the saved output format and supports an explicit override. The override
can appear before or after the help flag:

```bash
fab --help --output_format json
fab mkdir --help --output_format json
fab job run --output_format json --help
```

The aliases `-h` and `-help` support the same behavior. To view human-readable help
when JSON is configured, use `fab mkdir --help --output_format text`.
Help does not execute the command or require authentication.

JSON help uses the standard success response, with the full canonical command name
in `command` (for example, `"job run"`). Root help uses `"fab"`. The `result.data`
array contains exactly one help object with these fields:

| Field | Content |
| --- | --- |
| `schema_version` | Always `"1.0"`. |
| `cli_version` | The installed CLI version. |
| `description` | Command description. |
| `usage` | Usage starting with `fab`, followed by arguments and `[flags]`. |
| `args` | Positional arguments with `name`, `type`, `required`, and `description`. |
| `flags` | Flags with `name`, `aliases`, `type`, `required`, and `description`. |
| `aliases` | Alternate command names. |
| `subcommands` | Available subcommands with `name`, `description`, and `aliases`; aliases are not listed as separate commands. |
| `examples` | Examples with `description` and a complete `command` starting with `fab`. |
| `notes` | Additional guidance from command help. |
| `learn_more` | Documentation URLs. |

All fields are present, including empty arrays for sections that do not apply.
Descriptions are nonempty and `required` is always a boolean. Flags include
`choices` when values are restricted. Value-taking flags also include
`value_optional` and `repeat_behavior` (`"replace"` or `"append"`), derived from
argument parsing behavior. The help aliases are grouped under `--help`.
Hidden internal flags are omitted.

Help describes static parser arguments. Target-specific parameter names and
allowed values are not included; for example, use `fab mkdir nb1.Notebook -P`
to request parameter help for a notebook.

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
- **`hidden_data`** (array, optional): Virtual workspace items like capacities, gateways, managed private endpoints etc...
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
- Warning messages
- Informational messages
- Debug messages
- Progress indicators

This separation allows you to:
- Redirect command results to files while preserving interactive feedback
- Filter informational messages separately from actual data
- Pipe JSON output to processing tools without interference

## Usage Examples

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

### Automation and Scripting Examples

#### Redirecting Output
```bash
# Save results to file while seeing progress
$ fab ls --output_format json > workspaces.json
Processing workspace list...

# Save only errors for logging
$ fab command 2> error.log
```

## Best Practices

### Interactive Use
- Keep the default `text` format for better readability
- Use `-l` flag with text format to see detailed information in tables
- Progress and status messages will appear regardless of output format

### Automation and Scripting
- Set `output_format json` in config for scripts and automation
- Use `--output_format json` for specific commands that need machine parsing
- Always check the `status` field in JSON responses for error handling

### Command-Specific Tips
- Use `--output_format text` override when you need human-readable output from a JSON-configured CLI
- Combine with other flags like `--all` to include hidden data in JSON output
- Use shell redirection to separate data output from informational messages

## Related Documentation

- [Configuration Management](settings.md) - Managing CLI settings and preferences
- [Parameters](parameters.md) - Global flags and command parameters
- [Exit Codes](exit_codes.md) - Understanding command exit codes
- [Configuration Examples](../examples/config_examples.md) - Practical configuration examples