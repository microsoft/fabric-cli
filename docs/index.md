---
hide:
  - navigation
---

# Fabric CLI

The Fabric CLI (`fab`) gives you command-line access to Microsoft Fabric. Manage workspaces, run pipelines, and automate data workflows - all from your terminal.

---

## Why use the CLI?

Get powerful control over your Fabric resources:

- **Navigate like a file system** - Browse workspaces and items using familiar commands
- **Automate workflows** - Run pipelines and notebooks from scripts or CI/CD pipelines
- **Integrate with DevOps** - Add Fabric to GitHub Actions, Azure Pipelines, and other tools
- **Work your way** - Use Unix or Windows command styles on any platform

## What you can do

- **File system navigation** - `ls`, `cd`, `mkdir`, `cp`, `rm`, `run`. Work seamlessly in both Unix-style and Windows-style command names for file system operations. You can use whichever style you're most familiar with. For more details see [File System Commands](./commands/index.md#file-system-operations-fs).
- **Scripting & interactive modes** - Switch fluidly between live shell and one-off commands.
- **Autocompletion** - Enable [tab completion](./essentials/autocompletion.md) for commands, subcommands, and flags.
- **Cross-platform** - Windows Terminal, macOS Terminal, Linux shells.
- **Built on public APIs** - Fabric REST, OneLake, and Microsoft.Fabric ARM endpoints.


## Get started

### What you need

- Python 3.10, 3.11, 3.12 or 3.13
- `python` in your `PATH` environment variable

Check if Python is ready:

```bash
python --version
```

### Install the CLI

Use pip on Windows, macOS, or Linux:

```bash
pip install ms-fabric-cli
```

This installs the latest version of `fab` on Windows, macOS, and Linux.

Upgrade an existing installation:

```bash
pip install --upgrade ms-fabric-cli
```

Make sure it installed correctly:

```bash
fab --version
```

**Note:** Looking for other installation options? Check the [Release Notes](./release-notes.md) for standalone binaries and package managers as they become available.


### Sign in

Before you can use the CLI, sign in to Microsoft Fabric. Choose the authentication method that works for your scenario.

#### Authentication methods

`fab` supports **user**, **service principal**, and **managed identity** identity types for sign-in.

| **Identity Type**        | **Scenario**                       | **Command Usage**                                                                                    |
|----------------------|------------------------------------|------------------------------------------------------------------------------------------------|
| **User**             | Interactive browser login          | `fab auth login` and select *Interactive with a web browser*                                                                               |
| **Service Principal**| Secret                             | `fab auth login -u <client_id> -p <client_secret> --tenant <tenant_id>`                        |
|                      | Certificate              | `fab auth login -u <client_id> --certificate </path/to/certificate.[pem\|p12\|pfx]> --tenant <tenant_id>` |
|                      | Certificate + password   | `fab auth login -u <client_id> --certificate </path/to/certificate.[pem\|p12\|pfx]> -p <certificate_secret> --tenant <tenant_id>` |
|                      | Federated token          | `fab auth login -u <client_id> --federated-token <token> --tenant <tenant_id>` |
| **Managed Identity** | System-assigned                    | `fab auth login --identity`                                                                    |
|                      | User-assigned                      | `fab auth login --identity -u <client_id>`                                                     |

For more details and scripts, see the [auth examples](./examples/auth_examples.md).

#### Sign in interactively

For local development, sign in with your Microsoft account:

```bash
fab auth login
```

Select *Interactive with a web browser*. This opens your browser to complete authentication.

## Run your first command

Once you're signed in, you're one command away from exploring Fabric:

```bash
fab ls
```

This lists all workspaces you have access to. For a detailed list of available commands, see [Commands](./commands/index.md), or explore advanced scenarios in our [Usage examples](./examples/index.md).

## Common tasks

### Browse workspaces and items

```bash
# See all workspaces
fab ls

# See what's inside a workspace
fab ls "Sales Analytics.Workspace"
```

### Run notebooks and pipelines

```bash
# Run a pipeline
fab run <name of the workspace>.Workspace/<name of the pipeline>.DataPipeline -i <optional input>

# Start a notebook
fab start <name of the workspace>.Workspace/<name of the notebook>.Notebook
```

### Move files to OneLake

```bash
# Upload a local file
fab cp ./local/data.csv <name of workspace>.Workspace/<name of lakehouse>.Lakehouse/Files/data.csv

# Download from OneLake
fab cp <name of workspace>.Workspace/<name of lakehouse>.Lakehouse/Files/data.csv ./local/
```

## Use in automation

Add Fabric CLI to GitHub Actions, Azure Pipelines, and other DevOps tools. The same commands you use locally work in CI/CD.

### GitHub Actions example

```yaml
- name: Deploy to Fabric
  run: |
    pip install ms-fabric-cli
    fab auth login -u ${{ secrets.CLIENT_ID }} -p ${{ secrets.CLIENT_SECRET }} --tenant ${{ secrets.TENANT_ID }}
    fab import Production.Workspace/Data.Lakehouse -i ./artifacts/DataToImport.Lakehouse
```

### Azure Pipelines example

```yaml
- script: |
    pip install ms-fabric-cli
    fab auth login -u $(CLIENT_ID) -p $(CLIENT_SECRET) --tenant $(TENANT_ID)
    fab run ETL.Workspace/DailyRefresh.DataPipeline
  displayName: 'Run Fabric pipeline'
```

## Get help

**Found a bug or have a suggestion?**

- [Report an issue](https://github.com/microsoft/fabric-cli/issues)
- [Request a feature](https://github.com/microsoft/fabric-cli/discussions)
- [Share feedback via Microsoft Form](https://forms.office.com/r/uhL6b6tNsi)
- [Submit ideas to Fabric Ideas Portal](https://ideas.fabric.microsoft.com/)

**Need help using the CLI?**

- See [Troubleshooting](./troubleshooting.md) for common problems and solutions
- Ask questions in [GitHub Discussions](https://github.com/microsoft/fabric-cli/discussions)
- Connect with the community on [r/MicrosoftFabric](https://www.reddit.com/r/MicrosoftFabric/)
- Join the [Microsoft Developer Community](https://community.fabric.microsoft.com/t5/Developer/bd-p/Developer)

**Need enterprise assistance?**

- Contact your Microsoft account manager
- Open a ticket with the [Fabric Support Team](https://support.fabric.microsoft.com/)



