# GitHub Copilot Instructions - Microsoft Fabric CLI

Context for GitHub Copilot helping users work with the Fabric CLI. Copy or symlink to `.github/copilot-instructions.md`.

---

## What is Fabric CLI?

**Fabric CLI** (`fab`) is a command-line tool for **Microsoft Fabric** with interactive (REPL) and command-line modes.

- **Install**: `pip install ms-fabric-cli`
- **Python**: 3.10, 3.11, 3.12, 3.13
- **Platforms**: Windows, Linux, macOS
- **Shells**: PowerShell, Bash, Zsh, cmd

---

## Core Design Pattern

The CLI models Fabric as a **filesystem-like hierarchy** with **dot entity suffixes**:

```
/Workspace1.Workspace/Notebook1.Notebook
/Workspace1.Workspace/FolderA.Folder/SemanticModel1.SemanticModel
/Prod.Workspace/Lakehouse1.Lakehouse/Tables/customers
```

---

## Hierarchy Structure

- **Tenant** → top-level container
- **Workspace** → personal or team workspace
- **Folder** → organizes items (up to ~10 levels)
- **Item** → individual resource (Notebook, SemanticModel, Lakehouse, etc.)
- **OneLakeItem** → storage within Lakehouse (Tables, Files)

---

## Modes

- **Interactive mode**: REPL environment, commands without `fab` prefix
- **Command-line mode**: Single command execution, best for scripts

Switch modes with `fab config set mode interactive` or `fab config set mode cli`.

---

## Common Commands

```bash
# Authentication
fab auth login                    # Interactive login
fab auth status                   # Check auth status

# Navigation
fab ls                            # List items in current location
fab ls -a                         # Include hidden entities
fab cd /Workspace1.Workspace      # Change directory

# Item operations
fab get MyNotebook.Notebook       # Get item details
fab cp source.Notebook dest.Notebook  # Copy item
fab rm OldItem.Report             # Delete item

# Workspace operations
fab ls /                          # List all workspaces
fab mkdir /NewWorkspace.Workspace # Create workspace
```

---

## Authentication

Supported patterns:

1. **Interactive user**: `fab auth login` (browser/WAM)
2. **Service principal (secret)**:
   ```bash
   export FAB_SPN_TENANT_ID="<tenant>"
   export FAB_SPN_CLIENT_ID="<client>"
   export FAB_SPN_CLIENT_SECRET="<secret>"
   fab auth login --service-principal
   ```
3. **Federated credential**: `FAB_SPN_FEDERATED_TOKEN` environment variable
4. **Managed identity**: For Azure-hosted workloads

---

## Hidden Entities

Dot-prefixed entities not shown by default. Use `ls -a` to view.

- **Tenant-level**: `.capacities`, `.gateways`, `.connections`, `.domains`
- **Workspace-level**: `.managedidentities`, `.sparkpools`, `.externaldatashares`

```bash
fab ls .capacities
fab ls ws1.Workspace/.sparkpools
```

---

## Common Item Types

| Suffix | Type |
|--------|------|
| `.Workspace` | Workspace |
| `.Folder` | Folder |
| `.Notebook` | Notebook |
| `.SemanticModel` | Power BI dataset |
| `.Report` | Power BI report |
| `.Lakehouse` | Lakehouse |
| `.DataPipeline` | Data pipeline |
| `.Warehouse` | Data warehouse |
| `.Eventhouse` | Eventhouse (real-time) |
| `.KQLDatabase` | KQL Database |

---

## File Storage Locations

Config files in `~/.config/fab/`:
- `cache.bin` - encrypted token cache
- `config.json` - CLI settings
- `auth.json` - auth info (non-sensitive)

Debug logs:
- **Windows**: `%AppData%/fabcli_debug.log`
- **macOS**: `~/Library/Logs/fabcli_debug.log`
- **Linux**: `~/.local/state/fabcli_debug.log`

---

## Best Practices

1. **Always verify paths** before destructive operations
2. **Use `--dry-run`** when available for preview
3. **Check auth status** with `fab auth status` if commands fail
4. **Use relative paths** when working within a workspace
5. **Prefer `fab get --output json`** for scripting

---

## Getting Help

```bash
fab --help              # General help
fab <command> --help    # Command-specific help
fab docs                # Open documentation
```
