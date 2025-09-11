# Copilot Context — Microsoft Fabric CLI

This file gives AI coding assistants the **ground truth** for this repository: what the CLI is, how it’s designed, the patterns to follow, and the constraints to respect.

---

## What this repo is

**Fabric CLI** (`fab`) is a Python-based command-line client for **Microsoft Fabric** that works in both **interactive** (equivalent to REPL environment) and **non‑interactive** (regular command line) modes. Users install it with `pip install ms-fabric-cli`, then authenticate via interactive browser, service principal (secret/cert/**federated credential**), or managed identity, and run commands to list, navigate, and operate Fabric resources. [1](https://learn.microsoft.com/en-us/fabric/admin/fabric-command-line-interface)
**Key design principle:** The CLI models Fabric as a **filesystem-like hierarchy** with a consistent **dot (.) entity suffix** (e.g., `.Workspace`, `.Folder`, `.SemanticModel`), supports nested folders (up to ~10 levels), and produces intuitive paths like:

- `/Workspace1.Workspace/Notebook1.Notebook`  
- `/Workspace1.Workspace/FolderA.Folder/SemanticModel1.SemanticModel`
---

## High-level architecture & code layout

- **Language & framework:** Python 3.10-3.12 with `argparse` for command parsing. When adding commands, define prompts under the appropriate parser module and follow the parser conventions.
- **Representative paths in the codebase:**  
  - Commands: `src/fabric_cli/commands/...`  
  - Core utils/UI: `src/fabric_cli/utils/...`  
  - Entry points / main: `src/fabric_cli/main.py`  
  - Tests: `tests/...`  
  (For example changes in `fab_api_request.py` and `fab_ui.py`, and tests in `tests/test_utils/test_fab_ui.py` have appeared in recent PRs.)
- **Hierarchy structure**:
    - **Tenant**: The top-level container for everything.
    - **Workspace**: The personal or team's workspace, holding folders, items, and workspace level elements. (e.g., `fab get /Workspace1.Workspace/`)
    - **Folder**: The container for organizing items within a workspace. (e.g., `fab get /Workspace1.Workspace/FolderA.Folder/`)
    - **Item**: The individual resource within a workspace or a folder. (e.g., `fab get /Workspace1.Workspace/FolderA.Folder/Item1.<ItemType>`)
    - **OneLakeItem**: A OneLake storage item, resides within a Lakehouse item. Could be a table, file, etc. (e.g., `fab get /Workspace1.Workspace/FolderA.Folder/lh1.Lakehouse/Tables`)
    - **Hidden entities**: Special resources not normally visible to users. (e.g., `.capacities`, `.sparkpools`, etc. See hidden entities section below)

---

## Authentication

Copilot should prefer these patterns and avoid inventing new ones:

1) **Interactive user** — `fab auth login` (Web Account Manager on supported platforms or browser flow).  
2) **Service principal (secret/cert)** — env vars and secure storage.  
3) **Service principal (federated credential)** — use the **MSAL Python** confidential client with the federated token (`FAB_SPN_FEDERATED_TOKEN`); do **not** persist the raw token. 
4) Never log or print sensitive information (tokens, passwords, secrets)
5) Use secure token storage mechanisms provided by `FabAuth` class
6) Validate all user inputs that could affect security (paths, GUIDs, etc.)
7) Ensure proper scope handling for different authentication types

---

## Modes

The Fabric CLI supports two primary modes to accommodate a variety of workflows: command line and interactive. The selected mode is preserved between sessions. If you exit and login to the CLI later, it will resume in the same mode you last used.

- **Interactive mode**: Provides a REPL-like environment in which you can run Fabric CLI commands directly without the `fab` prefix.
- **Command line mode**: Executes commands in a single process. Best suited for scripted tasks, automation, or when you prefer running single commands without a prompt.

---

## Error handling

- Raise **`FabricCLIError`** with stable **error codes** and user‑friendly messages.  
- New messages go under `/errors/<module>.py`; new codes belong in `constants.py` under the error codes region; first try to **reuse** existing messages/codes.  
- Command wrappers render error *message + code* consistently.

---

## File storage

The Fabric CLI maintains several files in the user's home directory under .config/fab/:

- **cache.bin**	stores sensitive authentication data and is encrypted by default on supported platforms (Windows, MacOS, and Linux)
- **config.json** contains non-sensitive CLI configuration settings and preferences.
- **auth.json**	maintains CLI authentication non-sensitive information
- **context-<session_id>**: stores the CLI path context for each session; used exclusively in command_line mode.

Additionally, Fabric CLI writes debug logs to a file named fabcli_debug.log, stored in the following locations by platform:

- Windows: %AppData%
- macOS: ~/Library/Logs
- Linux: ~/.local/state

---

## Caching

- **Token Caching** managed via Microsoft Authentication Library (MSAL) extensions. By default, tokens are securely encrypted and stored in the user's home directory under .config/fab/cache.bin.
- **HTTP Response Caching** in interactive mode, certain endpoints are cached by default to diminish network traffic and improve overall responsiveness.

---

## Hidden entities

- In Fabric CLI, a hidden entity refers to any entity that is not a primary focus of the CLI. The primary focus of the CLI includes Workspaces, Items, or Folders. The rest of the entities considered as hidden entities and follow a UNIX-style convention similar to hidden files and directories, meaning they are not shown by default, require explicit navigation or path specification to access (e.g., using cd or ls with the full path).
- Hidden entities include tenant-level entities (such as connections, capacities, gateways, and domains) and workspace-level entities (such as managed identities, managed private endpoints, external data shares, and spark pools). They are identified by a dot-prefixed naming convention. To view hidden resources, users must use the `ls -a` or `ls --all` command, which displays all resources, including these hidden, dot-prefixed collections.

```sh
# List all capacities
fab ls .capacities

# Get a capacity
fab get .capacities/<capacity-name>.Capacity

# List all gateways
fab ls .gateways

# Get a gateway
fab get .gateways/<gateway-name>.Gateway

# List all connections
fab ls .connections

# Get a connection
fab get .connections/<connection-name>.Connection

# List all domains
fab ls .domains

# Get a domain
fab get .domains/<domain-name>.Domain

# List all managed identities
fab ls ws1.Workspace/.managedidentities

# Get a managed identity
fab get ws1.Workspace/.managedidentities/<managed-identity-name>.ManagedIdentity

# List all managed private endpoints
fab ls ws1.Workspace/.managedprivateendpoints

# Get a managed private endpoint
fab get ws1.Workspace/.managedprivateendpoints/<managed-private-endpoint-name>.ManagedPrivateEndpoint

# List all external data shares
fab ls ws1.Workspace/.externaldatashares

# Get external data share
fab get ws1.Workspace/.externaldatashares/<external-data-share-name>.ExternalDataShare

# List all spark pools
fab ls ws1.Workspace/.sparkpools

# Get spark pool
fab get ws1.Workspace/.sparkpools/<spark-pool-name>.SparkPool

```

---

## Limitations

- Python supported version are 3.10, 3.11 and 3.12 (>=3.13 not supported per releases).
- Supported platforms are: Windows, Linux and MacOS.
- Supported shells are: zsh, bash, PowerShell and cmd (command prompt in Windows).

---

## Prompting patterns for Copilot Chat (examples)

- “Create a new `fab` subcommand to **list semantic models** under a workspace path. Parse `--workspace-path`, validate the dot‑suffix, call the existing list APIs, and print via `print_output_format`. Add unit tests for parsing and happy/sad paths.” 
- “Refactor error handling in `X` to raise `FabricCLIError` with a **reused code** where possible; add a new message in `errors/<module>.py` only if needed. Update tests.” 
- “Add **service principal federated credential** login support in the auth parser; accept a `--federated-token` arg or `FAB_SPN_FEDERATED_TOKEN`. Use MSAL confidential client and do not persist raw tokens.”

---

## Pull Request Review and Coding Guidelines

When reviewing Pull Requests for fabric-cli, or developing new features, or fixing bugs, focus on these critical areas to ensure code quality, security, and maintainability.

### Code Style and Standards

**Required Standards**:

- **Type Hints**: All functions must include proper type annotations using `typing` module
  ```python
  from typing import Any, Optional, List, Dict
  def process_item(item: Dict[str, Any], timeout: Optional[int] = None) -> List[str]:
  ```
- **Import Organization**: Group imports in standard order (stdlib, third-party, local)
- **Naming Conventions**: Use `snake_case` for functions/variables, `PascalCase` for classes
- **Copyright Headers**: All new files must include Microsoft copyright header
- **Code Formatting**: Must pass `black src/ tests/` formatting check
- **Documentation**: Public functions require docstrings with parameter and return type descriptions

**Check for**:

- Consistent indentation and formatting (use `black --check` to validate)
- Proper error handling with appropriate exception types
- Clear variable and function names that express intent
- No unused imports or variables (use `mypy` to catch these)
- No hardcoded strings or magic numbers; use constants from `fab_constant`
- No circular imports

### Error Handling and Error Codes

**Error Class Usage** - All errors must use structured error classes:
- **`FabricCLIError`**: Base exception with message and optional status_code
- **`FabricAPIError`**: For Fabric REST API errors with errorCode, message, moreDetails
- **`OnelakeAPIError`**: For Data Lake Storage API errors  
- **`AzureAPIError`**: For Azure REST API errors

**Error Message Standards**:

- Use error message classes from `src/fabric_cli/errors/` directory:
  ```python
  from fabric_cli.errors.common import CommonErrors
  from fabric_cli.errors.auth import AuthErrors

  # Good
  raise FabricCLIError(
      CommonErrors.invalid_path(path),
      fab_constant.ERROR_INVALID_INPUT
  )

  # Bad - hardcoded message
  raise FabricCLIError("Invalid path provided")
  ```
- Include specific error codes from `fab_constant` (e.g., `ERROR_INVALID_INPUT`, `ERROR_SPN_AUTH_MISSING`)
- Provide actionable error messages that guide users toward solutions
- Include request IDs for API errors to aid debugging

**Error Handling Patterns**:

- Catch specific exceptions rather than broad `except Exception`
- Use proper error propagation - don't swallow exceptions silently
- Include context information in error messages (file paths, resource names, etc.)
- Validate inputs early and provide clear validation error messages

### Security Aspects

**Authentication and Authorization**:

- Never log or print sensitive information (tokens, passwords, secrets)
- Use secure token storage mechanisms provided by `FabAuth` class
- Validate all user inputs that could affect security (paths, GUIDs, etc.)
- Ensure proper scope handling for different authentication types
- Implement proper session cleanup (`Context().cleanup_context_files()`)

**Input Validation**:

- Sanitize all user inputs, especially file paths and API parameters
- Use GUID validation for resource identifiers: `CommonErrors.invalid_guid(parameter_name)`
- Validate JSON inputs: `CommonErrors.invalid_json_format()`
- Check file permissions before operations: `CommonErrors.file_not_accessible(file_path)`

**Data Protection**:

- Never commit secrets, tokens, or credentials to code
- Use environment variables for sensitive configuration
- Ensure temporary files are properly cleaned up
- Validate certificate paths and formats for SPN authentication

### Performance Considerations

**Resource Management**:

- Clear caches appropriately using `utils_mem_store.clear_caches()`
- Implement proper cleanup in finally blocks or context managers
- Avoid memory leaks in long-running operations
- Use pagination for large data sets

**API Efficiency**:

- Minimize API calls by batching operations where possible
- Use VCR.py recordings for tests (`--playback` flag) to avoid live API calls
- Implement proper retry logic with exponential backoff
- Set appropriate timeouts for network operations

**File Operations**:

- Stream large files rather than loading entirely into memory
- Use appropriate buffer sizes for I/O operations
- Check file sizes before processing to prevent resource exhaustion
- Implement progress indicators for long-running operations

### Code Correctness

**Testing Requirements**:

- All new functionality must include corresponding tests
- Use existing test patterns in `tests/test_commands/` with VCR.py recordings
- Verify error paths are tested, not just happy paths
- Run full test suite: `python3 -m pytest tests/test_commands --playback`

**Logic Validation**:

- Check for proper null/None handling throughout the code
- Validate edge cases (empty inputs, maximum values, etc.)
- Ensure proper handling of optional parameters
- Verify correct return types match function signatures

**Integration Points**:

- Ensure commands work correctly with different authentication modes
- Test output formatters work with all supported formats (JSON, table, etc.)
- Validate CLI argument parsing and help text accuracy
- Check context switching and workspace operations

### Review Checklist

Before approving any PR, verify:

1. **Pre-commit Validation Passed**:
   - [ ] `black src/ tests/` (formatting)
   - [ ] `mypy src/ tests/ --ignore-missing-imports` (type checking)
   - [ ] `python3 -m pytest tests/test_core tests/test_utils` (unit tests)
   - [ ] `python3 -m pytest tests/test_commands --playback` (integration tests)

2. **Code Quality**:
   - [ ] Proper error handling with structured error classes
   - [ ] Type hints on all new functions and methods
   - [ ] No security vulnerabilities or credential exposure
   - [ ] Performance considerations addressed
   - [ ] Test coverage for new functionality

3. **Documentation**:
   - [ ] Function docstrings for public APIs
   - [ ] Updated help text for new commands or options
   - [ ] README updates if new functionality affects user workflows

**Rejection Criteria** - Reject PRs that:

- Bypass structured error handling patterns
- Include hardcoded credentials or secrets
- Lack proper type annotations
- Don't include tests for new functionality
- Fail any of the pre-commit validation steps
- Introduce performance regressions without justification
