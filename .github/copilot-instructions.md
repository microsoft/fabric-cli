# Copilot Instructions — Microsoft Fabric CLI

**Purpose:** This file provides authoritative context for AI coding assistants working with the Microsoft Fabric CLI repository. It defines what the CLI is, how it's architected, the design patterns to follow, coding standards to enforce, and constraints to respect.

**Your role:** You are an expert software engineer contributing to Fabric CLI (`fab`). When assisting with this codebase, you must follow these instructions exactly - they represent the ground truth for how this project works.

**Key expertise areas:**
- Python 3.10-3.12 development with type hints and modern patterns
- CLI architecture using argparse and filesystem-inspired design
- Microsoft Fabric API integration (REST, OneLake, ARM)
- MSAL authentication flows (interactive, service principal, managed identity)
- Error handling with structured exception classes
- Test-driven development with pytest and VCR.py

## What this codebase is

The Microsoft Fabric CLI (`fab`) gives users command-line access to Microsoft Fabric using file-system commands.

**Installation:** `pip install ms-fabric-cli`  
**Authentication:** Interactive browser, service principal, or managed identity  
**Modes:** Interactive shell or command-line  
**Design:** Models Fabric as a file-system hierarchy

**Path examples:**
```bash
/SalesAnalytics.Workspace/Q1Report.Report
/SalesAnalytics.Workspace/Data.Folder/CustomerData.Lakehouse/Files/
```

**User documentation:** https://microsoft.github.io/fabric-cli/

## Entity hierarchy

Use this hierarchy when working with paths:

| Level | What it is | Path pattern | Example |
|-------|------------|--------------|---------|
| Tenant | Root level | `/` | `/` |
| Workspace | Top-level container | `/Name.Workspace` | `/SalesAnalytics.Workspace` |
| Folder | Item organizer (10 levels max) | `/Workspace/Name.Folder` | `/SalesAnalytics.Workspace/Reports.Folder` |
| Item | Fabric resource | `/Workspace/Folder/Name.Type` | `/SalesAnalytics.Workspace/Reports.Folder/Q1.Report` |
| OneLake | Storage in Lakehouse | `/Workspace/Name.Lakehouse/Files/` | `/SalesAnalytics.Workspace/Data.Lakehouse/Files/sales.csv` |
| Hidden | Tenant/workspace resources | `/.capacities` or `/Workspace/.managedidentities` | `/.capacities/MyCapacity.Capacity` |

**Entity type suffixes (always use these):**
- `.Workspace`, `.Folder`, `.Notebook`, `.Lakehouse`, `.SemanticModel`, `.Report`, `.DataPipeline`, `.Capacity`, `.Gateway`, `.ManagedIdentity`

## Code organization

**Python:** 3.10-3.12 with `argparse` for parsing  
**Commands:** `src/fabric_cli/commands/`  
**Utils:** `src/fabric_cli/utils/`  
**Entry:** `src/fabric_cli/main.py`  
**Tests:** `tests/` (use VCR.py recordings)

## Authentication patterns

When implementing authentication:

| Method | How to implement | Required env vars |
|--------|------------------|-------------------|
| Interactive user | Use `fab auth login` with browser flow | None |
| Service principal (secret) | Use `FAB_CLIENT_ID`, `FAB_CLIENT_SECRET`, `FAB_TENANT_ID` | All 3 required |
| Service principal (cert) | Use cert path + `FAB_CLIENT_ID`, `FAB_TENANT_ID` | `FAB_CERTIFICATE_PATH` |
| Service principal (federated) | Use MSAL confidential client with `FAB_SPN_FEDERATED_TOKEN` | Token required |
| Managed identity | System or user-assigned via MSAL | `FAB_CLIENT_ID` (user-assigned only) |

**Security rules:**
- NEVER log tokens, passwords, secrets
- Use `FabAuth` class for secure storage
- Validate all inputs (paths, GUIDs)
- Do NOT persist raw federated tokens

See: https://microsoft.github.io/fabric-cli/examples/auth_examples/

## CLI modes

**Interactive mode:** Shell environment where users run commands without `fab` prefix (like Python REPL)

**Command-line mode:** Single-process execution for scripts and automation

Mode persists between sessions.

## Error handling rules

**Use these error classes:**
```python
from fabric_cli.errors.common import CommonErrors
from fabric_cli.errors.auth import AuthErrors
from fabric_cli.exceptions import FabricCLIError, FabricAPIError, OnelakeAPIError, AzureAPIError
```

**Pattern to follow:**
```python
# CORRECT
raise FabricCLIError(
    CommonErrors.invalid_path(path),
    fab_constant.ERROR_INVALID_INPUT
)

# WRONG - never hardcode messages
raise FabricCLIError("Invalid path provided")
```

**Rules:**
- Add new messages to `src/fabric_cli/errors/<module>.py`
- Add new codes to `constants.py` under error codes region
- Reuse existing messages/codes when possible
- Include error codes from `fab_constant`
- Catch specific exceptions (NOT `except Exception`)
- Include context (file paths, resource names) in errors

## File storage locations

CLI stores files in `~/.config/fab/`:

| File | Contains | Encrypted? |
|------|----------|------------|
| `cache.bin` | Auth tokens | Yes (Windows, macOS, Linux) |
| `config.json` | CLI settings | No |
| `auth.json` | Auth metadata | No |
| `context-<session_id>` | Path context (command-line mode only) | No |

**Debug logs:**
- Windows: `%AppData%/fabcli_debug.log`
- macOS: `~/Library/Logs/fabcli_debug.log`
- Linux: `~/.local/state/fabcli_debug.log`

## Caching behavior

**Tokens:** MSAL stores encrypted tokens in `cache.bin`  
**HTTP responses:** Interactive mode caches certain endpoints to reduce network calls

## Hidden entities

Hidden entities start with `.` (like UNIX hidden files). Not shown by default.

**Tenant-level:** `/.capacities`, `/.gateways`, `/.connections`, `/.domains`  
**Workspace-level:** `/WorkspaceName.Workspace/.managedidentities`, `/.managedprivateendpoints`, `/.externaldatashares`, `/.sparkpools`

**Show with:** `fab ls -a` or `fab ls --all`

**Examples:**
```bash
fab ls .capacities                                    # List all capacities
fab get .capacities/MyCapacity.Capacity              # Get specific capacity
fab ls SalesWorkspace.Workspace/.managedidentities   # List workspace managed identities
```

## Platform support

**Python:** 3.10, 3.11, 3.12 (NOT 3.13+)  
**OS:** Windows, Linux, macOS  
**Shells:** zsh, bash, PowerShell, cmd

## When adding new code

**Required:**
- Type hints on ALL functions using `typing` module
- Imports grouped: stdlib → third-party → local
- `snake_case` for functions/variables, `PascalCase` for classes
- Microsoft copyright header on new files
- Pass `black src/ tests/` formatting
- Docstrings on public functions with param/return types
- Tests for all new functionality
- Follow patterns in existing code (check similar commands/functions for reference)

**Forbidden:**
- Hardcoded strings (use `fab_constant`)
- Magic numbers (use constants)
- Circular imports
- Unused imports/variables
- Broad `except Exception`
- Logging sensitive data

## When writing tests

- Use VCR.py recordings in `tests/test_commands/`
- Test error paths, not just happy paths
- Run: `python3 -m pytest tests/test_commands --playback`
- Follow existing test patterns

## When writing user-facing text

Follow patterns from user documentation:

**Headings:** Use sentence case ("Quick start" not "Quick Start")  
**Authentication:** Say "sign in" not "login"  
**Tone:** Direct, concise, active voice  

See:
- Commands: https://microsoft.github.io/fabric-cli/commands/
- Examples: https://microsoft.github.io/fabric-cli/examples/
- Auth: https://microsoft.github.io/fabric-cli/examples/auth_examples/

## Security checklist

Before submitting code, verify:
- No tokens/passwords in logs or stdout
- Use `FabAuth` class for token storage
- Validate inputs (paths, GUIDs, JSON)
- Sanitize file paths and API params
- Clean up temp files and sessions
- No secrets committed to code

## Performance checklist

Before submitting code, verify:
- Clear caches with `utils_mem_store.clear_caches()`
- Cleanup in `finally` blocks or context managers
- Pagination for large datasets
- Batch API calls when possible
- Stream large files (don't load into memory)
- Set appropriate timeouts
- Progress indicators for long operations

## Pre-commit validation

Run these before submitting:
```bash
black src/ tests/                                      # Formatting
mypy src/ tests/ --ignore-missing-imports              # Type checking
python3 -m pytest tests/test_core tests/test_utils     # Unit tests
python3 -m pytest tests/test_commands --playback       # Integration tests
```

All must pass.
