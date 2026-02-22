---
name: fabric-cli-core
description: Use Microsoft Fabric CLI (fab) to manage workspaces, semantic models, reports, notebooks, and Fabric resources. Activate when users mention fab, Fabric CLI, or need to automate Fabric operations.
---

# Fabric CLI Core

This skill defines safe, consistent defaults for an AI agent helping users operate **Microsoft Fabric** via the **Fabric CLI (`fab`)**.

## 1 - Fabric CLI mental model (paths and entities)

### Automation Scripts

Ready-to-use Python scripts for core CLI tasks. Run any script with `--help` for full options.

| Script | Purpose | Usage |
|--------|---------|-------|
| `health_check.py` | Verify CLI installation, auth status, and connectivity | `python scripts/health_check.py [--workspace WS]` |

Scripts are located in the `scripts/` folder of this skill.

### Paths and Entities

- Treat Fabric as a **filesystem-like hierarchy** with consistent **dot (.) entity suffixes** in paths (e.g., `.Workspace`, `.Folder`, `.SemanticModel`).
- The hierarchy structure is:
  - **Tenant**: The top-level container for everything.
  - **Workspace**: Personal or team workspace holding folders, items, and workspace-level elements.
  - **Folder**: Container for organizing items within a workspace (supports ~10 levels of nesting).
  - **Item**: Individual resource within a workspace or folder (e.g., Notebook, SemanticModel, Lakehouse).
  - **OneLakeItem**: OneLake storage item residing within a Lakehouse (tables, files, etc.).
- Prefer and generate paths like:
  - `/Workspace1.Workspace/Notebook1.Notebook`
  - `/Workspace1.Workspace/FolderA.Folder/SemanticModel1.SemanticModel`
  - `/Workspace1.Workspace/FolderA.Folder/lh1.Lakehouse/Tables` (OneLakeItem)
- When a user provides an ambiguous identifier, ask for the full path (or infer with stated assumptions).

## 2 - Modes (interactive vs command line)
- Be explicit about which mode a user is in:
  - **Interactive mode** behaves like a REPL and runs commands without the `fab` prefix.
  - **Command line mode** runs one command per invocation and is best for scripts/automation.
- The selected mode is **preserved between sessions**. If a user exits and logs back in, the CLI resumes in the same mode last used.
- When you provide instructions, show commands in **command line mode** unless the user says they're in interactive mode.

## 3 - Authentication (public-safe guidance)
- Prefer these auth patterns and do not invent new flows:
  1) **Interactive user**: `fab auth login` (browser/WAM where supported).
  2) **Service principal (secret/cert)**: use environment variables / secure mechanisms; avoid embedding secrets in files.
  3) **Service principal (federated credential)**: use the federated token environment variable (`FAB_SPN_FEDERATED_TOKEN`) and **do not persist the raw token**.
  4) **Managed identity**: supported for Azure-hosted workloads; no credentials required.
- Never ask users to paste secrets into chat or print them back.

## 4 - Sensitive data handling (strict)
- Never log or output tokens, passwords, client secrets, or raw federated tokens.
- Validate all user inputs that could affect security:
  - **Paths**: Sanitize file paths and API parameters.
  - **GUIDs**: Validate resource identifiers before use.
  - **JSON**: Validate JSON inputs for proper format.
- If a user shares sensitive strings, advise rotating/regenerating them and moving to secure storage.

## 5 - Hidden entities and discovery
- Hidden entities are special resources not normally visible, following a **dot-prefixed naming convention** (similar to UNIX hidden files).
- **Tenant-level hidden entities** (accessed from root):
  - `.capacities` — `fab ls .capacities` / `fab get .capacities/<name>.Capacity`
  - `.gateways` — `fab ls .gateways` / `fab get .gateways/<name>.Gateway`
  - `.connections` — `fab ls .connections` / `fab get .connections/<name>.Connection`
  - `.domains` — `fab ls .domains` / `fab get .domains/<name>.Domain`
- **Workspace-level hidden entities** (accessed within a workspace):
  - `.managedidentities` — `fab ls ws1.Workspace/.managedidentities`
  - `.managedprivateendpoints` — `fab ls ws1.Workspace/.managedprivateendpoints`
  - `.externaldatashares` — `fab ls ws1.Workspace/.externaldatashares`
  - `.sparkpools` — `fab ls ws1.Workspace/.sparkpools`
- To show hidden resources, recommend `ls -a` / `ls --all`.

## 6 - Errors and troubleshooting guidance
- When describing failures, include:
  - What the command was trying to do
  - The likely cause
  - The next actionable step
- If the CLI surfaces an error code/message, keep it intact and do not paraphrase away the key identifiers. (Fabric CLI emphasizes stable error codes/messages.)
- Include request IDs for API errors to aid debugging when available.

## 7 - Output conventions for the agent
- Default to concise, runnable steps.
- When recommending commands, include:
  - Preconditions (auth, correct workspace/path)
  - Expected result
  - How to verify (e.g., follow-up `fab ls` / `fab get`)

## 8 - Safety defaults
- Ask before suggesting commands that delete, overwrite, or change access/permissions.
- If the user explicitly confirms, proceed with a clear rollback note when possible.

## 9 - Platform and troubleshooting reference
- **Supported platforms**: Windows, Linux, macOS.
- **Supported shells**: zsh, bash, PowerShell, cmd (Windows command prompt).
- **Python versions**: 3.10, 3.11, 3.12, 3.13.
- **CLI file storage** (useful for troubleshooting):
  - Config files are stored in `~/.config/fab/`:
    - `cache.bin` — encrypted auth token cache
    - `config.json` — non-sensitive CLI settings
    - `auth.json` — non-sensitive auth info
    - `context-<session_id>` — path context for command-line mode sessions
  - Debug logs are written to:
    - Windows: `%AppData%/fabcli_debug.log`
    - macOS: `~/Library/Logs/fabcli_debug.log`
    - Linux: `~/.local/state/fabcli_debug.log`

## 10 - Critical operational rules
- **First run**: Always run `fab auth status` to verify authentication before executing commands. If not authenticated, ask the user to run `fab auth login`.
- **Learn before executing**: Always use `fab --help` and `fab <command> --help` the first time you use a command to understand its syntax.
- **Start simple**: Try the basic `fab` command alone first before piping or chaining.
- **Non-interactive mode**: Use `fab` in command-line mode when working with coding agents. Interactive mode doesn't work with automation.
- **Force flag**: Use `-f` when executing commands if the flag is available to run non-interactively (skips confirmation prompts).
- **Verify before acting**: If workspace or item name is unclear, ask the user first, then verify with `fab ls` or `fab exists` before proceeding.
- **Permission errors**: If a command is blocked by permissions, stop and ask the user for clarification; never try to circumvent it.

## 11 - Common item types

| Extension | Description |
|-----------|-------------|
| `.Workspace` | Workspace container |
| `.Folder` | Folder within workspace |
| `.SemanticModel` | Power BI dataset/semantic model |
| `.Report` | Power BI report |
| `.Dashboard` | Power BI dashboard |
| `.Notebook` | Fabric notebook |
| `.Lakehouse` | Lakehouse |
| `.Warehouse` | Data warehouse |
| `.DataPipeline` | Data pipeline |
| `.SparkJobDefinition` | Spark job definition |
| `.Eventstream` | Real-time event stream |
| `.KQLDatabase` | KQL database |
| `.MLModel` | ML model |
| `.MLExperiment` | ML experiment |
| `.Capacity` | Fabric capacity (hidden) |
| `.Gateway` | Data gateway (hidden) |
| `.Connection` | Connection (hidden) |

Use `fab desc .<ItemType>` to explore any item type.

## 12 - Command references

For detailed command syntax and working examples, see:

- [Quick Start Guide](./references/quickstart.md) — Copy-paste examples for common tasks
- [Full Command Reference](./references/reference.md) — All commands with flags and patterns
- [Semantic Models](./references/semantic-models.md) — TMDL, DAX queries, refresh, storage modes
- [Notebooks](./references/notebooks.md) — Job execution, parameters, scheduling
- [Reports](./references/reports.md) — Export, import, rebind to models
- [Workspaces](./references/workspaces.md) — Create, manage, permissions
- [Querying Data](./references/querying-data.md) — DAX and lakehouse table queries
- [API Reference](./references/fab-api.md) — Direct REST API access patterns
- [Create Workspaces](./references/create-workspaces.md) — Workspace creation workflows
