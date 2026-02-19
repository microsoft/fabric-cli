---
name: fabric-cli
description: Use Microsoft Fabric CLI (fab) to manage workspaces, semantic models, reports, notebooks, lakehouses, and other Fabric resources via file-system metaphor and commands. Use when deploying Fabric items, running jobs, querying data, managing OneLake files, or automating Fabric operations. Invoke this skill automatically whenever a user mentions the Fabric CLI, fab, or Fabric.
---

# Microsoft Fabric CLI Operations

> **Note:** If you have access to a Bash tool (e.g., Claude Code), execute `fab` commands directly via Bash rather than using an MCP server.

Expert guidance for using the `fab` CLI to programmatically manage Fabric

## When to Use This Skill

Activate automatically when tasks involve:

- Mention of the Fabric CLI, Fabric items, Power BI, `fab`, or `fab` commands
- Managing workspaces, items, or resources
- Deploying or migrating semantic models, reports, notebooks, pipelines
- Running or scheduling jobs (notebooks, pipelines, Spark)
- Working with lakehouse/warehouse tables and data
- Using the Fabric, Power BI, or OneLake APIs
- Automating Fabric operations in scripts

## Critical

- If workspace or item name is unclear, ask the user first, then verify with `fab ls` or `fab exists` before proceeding
- The first time you use `fab` run `fab auth status` to make sure the user is authenticated. If not, ask the user to run `fab auth login` to login
- Always use `fab --help` and `fab <command> --help` the first time you use a command to understand its syntax, first
- Always try the simple `fab` command alone, first before piping it
- Always use `-f` when executing command if the flag is available to do so non-interactively
- Ensure that you avoid removing or moving items, workspaces, or definitions, or changing properties without explicit user direction
- If a command is blocked in your permissions and you try to use it, stop and ask the user for clarification; never try to circumvent it
- Use `fab` in non-interactive mode. Interactive mode doesn't work with coding agents

## First Run

```bash
fab auth login          # Authenticate (opens browser)
fab auth status         # Verify authentication
fab ls                  # List your workspaces
fab ls "Name.Workspace" # List items in a workspace
```

## Variable Extraction Pattern

Most workflows need IDs. Extract them like this:

```bash
WS_ID=$(fab get "ws.Workspace" -q "id" | tr -d '"')
MODEL_ID=$(fab get "ws.Workspace/Model.SemanticModel" -q "id" | tr -d '"')

# Then use in API calls
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{"type":"Full"}'
```

## Quick Start

**New to Fabric CLI?** Here are some references you can read:

- [Quick Start Guide](./references/quickstart.md) - Copy-paste examples
- [Querying Data](./references/querying-data.md) - Query semantic models and lakehouse tables
- [Semantic Models](./references/semantic-models.md) - TMDL, DAX, refresh, storage mode
- [Reports](./references/reports.md) - Export, import, visuals, fields
- [Notebooks](./references/notebooks.md) - Job execution, parameters
- [Workspaces](./references/workspaces.md) - Create, manage, permissions
- [Full Command Reference](./references/reference.md) - All commands detailed
- [Command Reference Table](#command-reference) - At-a-glance command syntax

### Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| **Finding Items** |||
| `fab ls` | List items | `fab ls "Sales.Workspace"` |
| `fab ls -l` | List with details | `fab ls "Sales.Workspace" -l` |
| `fab exists` | Check if exists | `fab exists "Sales.Workspace/Model.SemanticModel"` |
| `fab get` | Get item details | `fab get "Sales.Workspace/Model.SemanticModel"` |
| `fab get -q` | Query specific field | `fab get "Sales.Workspace" -q "id"` |
| **Definitions** |||
| `fab get -q "definition"` | Get full definition | `fab get "ws.Workspace/Model.SemanticModel" -q "definition"` |
| `fab export` | Export to local | `fab export "ws.Workspace/Nb.Notebook" -o ./backup` |
| `fab import` | Import from local | `fab import "ws.Workspace/Nb.Notebook" -i ./backup/Nb.Notebook` |
| **Running Jobs** |||
| `fab job run` | Run synchronously | `fab job run "ws.Workspace/ETL.Notebook"` |
| `fab job start` | Run asynchronously | `fab job start "ws.Workspace/ETL.Notebook"` |
| `fab job run -P` | Run with params | `fab job run "ws.Workspace/Nb.Notebook" -P date:string=2025-01-01` |
| `fab job run-list` | List executions | `fab job run-list "ws.Workspace/Nb.Notebook"` |
| `fab job run-status` | Check status | `fab job run-status "ws.Workspace/Nb.Notebook" --id <job-id>` |
| **Refreshing Models** |||
| `fab api -A powerbi` | Trigger refresh | `fab api -A powerbi "groups/<ws-id>/datasets/<model-id>/refreshes" -X post -i '{"type":"Full"}'` |
| `fab api -A powerbi` | Check refresh status | `fab api -A powerbi "groups/<ws-id>/datasets/<model-id>/refreshes?\$top=1"` |
| **DAX Queries** |||
| `fab get -q "definition"` | Get model schema first | `fab get "ws.Workspace/Model.SemanticModel" -q "definition"` |
| `fab api -A powerbi` | Execute DAX | `fab api -A powerbi "groups/<ws-id>/datasets/<model-id>/executeQueries" -X post -i '{"queries":[{"query":"EVALUATE..."}]}'` |
| **Lakehouse** |||
| `fab ls` | Browse files/tables | `fab ls "ws.Workspace/LH.Lakehouse/Files"` |
| `fab table schema` | Get table schema | `fab table schema "ws.Workspace/LH.Lakehouse/Tables/sales"` |
| `fab cp` | Upload/download | `fab cp ./local.csv "ws.Workspace/LH.Lakehouse/Files/"` |
| **Management** |||
| `fab cp` | Copy items | `fab cp "dev.Workspace/Item.Type" "prod.Workspace" -f` |
| `fab set` | Update properties | `fab set "ws.Workspace/Item.Type" -q displayName -i "New Name"` |
| `fab rm` | Delete item | `fab rm "ws.Workspace/Item.Type" -f` |

## Core Concepts

### Path Format

Fabric uses filesystem-like paths with type extensions:

`/WorkspaceName.Workspace/ItemName.ItemType`

For lakehouses this is extended into files and tables:

`/WorkspaceName.Workspace/LakehouseName.Lakehouse/Files/FileName.extension` or `/WorkspaceName.Workspace/LakehouseName.Lakehouse/Tables/TableName`

For Fabric capacities you have to use `fab ls .capacities`

Examples:

- `"/Production.Workspace/Sales Model.SemanticModel"`
- `/Data.Workspace/MainLH.Lakehouse/Files/data.csv`
- `/Data.Workspace/MainLH.Lakehouse/Tables/dbo/customers`

### Common Item Types

- `.Workspace` - Workspaces
- `.SemanticModel` - Power BI datasets
- `.Report` - Power BI reports
- `.Notebook` - Fabric notebooks
- `.DataPipeline` - Data pipelines
- `.Lakehouse` / `.Warehouse` - Data stores
- `.SparkJobDefinition` - Spark jobs

Full list: 35+ types. Use `fab desc .<ItemType>` to explore.

## Essential Commands

### Navigation & Discovery

```bash
# List resources
fab ls                                    # List workspaces
fab ls "Production.Workspace"             # List items in workspace
fab ls "Production.Workspace" -l          # Detailed listing
fab ls "Data.Workspace/LH.Lakehouse"      # List lakehouse contents

# Check existence
fab exists "Production.Workspace/Sales.SemanticModel"

# Get details
fab get "Production.Workspace/Sales.Report"
fab get "Production.Workspace" -q "id"    # Query with JMESPath
```

### Creating & Managing Resources

```bash
# Create workspace after using `fab ls .capacities` to check capacities
fab mkdir "NewWorkspace.Workspace" -P capacityname=MyCapacity

# Create items
fab mkdir "Production.Workspace/NewLakehouse.Lakehouse"
fab mkdir "Production.Workspace/Pipeline.DataPipeline"

# Update properties
fab set "Production.Workspace/Item.Notebook" -q displayName -i "New Name"
fab set "Production.Workspace" -q description -i "Production environment"
```

### Copy, Move, Export, Import

```bash
# Copy between workspaces
fab cp "Dev.Workspace/Pipeline.DataPipeline" "Production.Workspace"
fab cp "Dev.Workspace/Report.Report" "Production.Workspace/ProdReport.Report"

# Export to local
fab export "Production.Workspace/Model.SemanticModel" -o /tmp/exports
fab export "Production.Workspace" -o /tmp/backup -a  # Export all items

# Import from local
fab import "Production.Workspace/Pipeline.DataPipeline" -i /tmp/exports/Pipeline.DataPipeline -f

# IMPORTANT: Use -f flag for non-interactive execution
# Without -f, import/export operations expect an interactive terminal for confirmation
# This will fail in scripts, automation, or when stdin is not a terminal
fab import "ws.Workspace/Item.Type" -i ./Item.Type -f  # Required for scripts
```

### API Operations

Direct REST API access with automatic authentication.

**Audiences:**

- `fabric` (default) - Fabric REST API
- `powerbi` - Power BI REST API
- `storage` - OneLake Storage API
- `azure` - Azure Resource Manager

```bash
# Fabric API (default)
fab api workspaces
fab api workspaces -q "value[?type=='Workspace']"
fab api "workspaces/<workspace-id>/items"

# Power BI API (for DAX queries, dataset operations)
fab api -A powerbi groups
fab api -A powerbi "datasets/<model-id>/executeQueries" -X post -i '{"queries": [{"query": "EVALUATE VALUES(Date[Year])"}]}'

# POST/PUT/DELETE
fab api -X post "workspaces/<ws-id>/items" -i '{"displayName": "New Item", "type": "Lakehouse"}'
fab api -X put "workspaces/<ws-id>/items/<item-id>" -i /tmp/config.json
fab api -X delete "workspaces/<ws-id>/items/<item-id>"

# OneLake Storage API
fab api -A storage "WorkspaceName.Workspace/LH.Lakehouse/Files" -P resource=filesystem,recursive=false
```

### Job Management

```bash
# Run synchronously (wait for completion)
fab job run "Production.Workspace/ETL.Notebook"
fab job run "Production.Workspace/Pipeline.DataPipeline" --timeout 300

# Run with parameters
fab job run "Production.Workspace/ETL.Notebook" -P date:string=2024-01-01,batch:int=1000,debug:bool=false

# Start asynchronously
fab job start "Production.Workspace/LongProcess.Notebook"

# Monitor
fab job run-list "Production.Workspace/ETL.Notebook"
fab job run-status "Production.Workspace/ETL.Notebook" --id <job-id>

# Schedule
fab job run-sch "Production.Workspace/Pipeline.DataPipeline" --type daily --interval 10:00,16:00 --start 2024-11-15T09:00:00 --enable
fab job run-sch "Production.Workspace/Pipeline.DataPipeline" --type weekly --interval 10:00 --days Monday,Friday --enable

# Cancel
fab job run-cancel "Production.Workspace/ETL.Notebook" --id <job-id>
```

### Table Operations

```bash
# View schema
fab table schema "Data.Workspace/LH.Lakehouse/Tables/dbo/customers"

# Load data (non-schema lakehouses only)
fab table load "Data.Workspace/LH.Lakehouse/Tables/sales" --file "Data.Workspace/LH.Lakehouse/Files/daily_sales.csv" --mode append

# Optimize (lakehouses only)
fab table optimize "Data.Workspace/LH.Lakehouse/Tables/transactions" --vorder --zorder customer_id,region

# Vacuum (lakehouses only)
fab table vacuum "Data.Workspace/LH.Lakehouse/Tables/temp_data" --retain_n_hours 48
```

## Common Workflows

### Semantic Model Management

```bash
# Find models
fab ls "ws.Workspace" | grep ".SemanticModel"

# Get definition
fab get "ws.Workspace/Model.SemanticModel" -q definition

# Trigger refresh
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{"type":"Full"}'

# Check refresh status
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes?\$top=1"
```

**Execute DAX:**

```bash
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/executeQueries" -X post \
  -i '{"queries":[{"query":"EVALUATE TOPN(5, '\''TableName'\'')"}]}'
```

**DAX rules:** EVALUATE required, single quotes around tables (`'Sales'`), qualify columns (`'Sales'[Amount]`).

For full details: [semantic-models.md](./references/semantic-models.md) | [querying-data.md](./references/querying-data.md)

### Report Operations

```bash
# Get report definition
fab get "ws.Workspace/Report.Report" -q definition

# Export to local
fab export "ws.Workspace/Report.Report" -o /tmp/exports -f

# Import from local
fab import "ws.Workspace/Report.Report" -i /tmp/exports/Report.Report -f

# Rebind to different model
fab set "ws.Workspace/Report.Report" -q semanticModelId -i "<new-model-id>"
```

For full details: [reports.md](./references/reports.md)

### Lakehouse/Warehouse Operations

```bash
# Browse contents
fab ls "Data.Workspace/LH.Lakehouse/Files"
fab ls "Data.Workspace/LH.Lakehouse/Tables/dbo"

# Upload/download files
fab cp ./local-data.csv "Data.Workspace/LH.Lakehouse/Files/data.csv"
fab cp "Data.Workspace/LH.Lakehouse/Files/data.csv" ~/Downloads/

# Load and optimize tables
fab table load "Data.Workspace/LH.Lakehouse/Tables/sales" --file "Data.Workspace/LH.Lakehouse/Files/sales.csv"
fab table optimize "Data.Workspace/LH.Lakehouse/Tables/sales" --vorder --zorder customer_id
```

### Environment Migration

```bash
# Export from dev
fab export "Dev.Workspace" -o /tmp/migration -a

# Import to production (item by item)
fab import "Production.Workspace/Pipeline.DataPipeline" -i /tmp/migration/Pipeline.DataPipeline
fab import "Production.Workspace/Report.Report" -i /tmp/migration/Report.Report
```

## Key Patterns

### JMESPath Queries

Filter and transform JSON responses with `-q`:

```bash
# Get single field
-q "id"
-q "displayName"

# Get nested field
-q "properties.sqlEndpointProperties"
-q "definition.parts[0]"

# Filter arrays
-q "value[?type=='Lakehouse']"
-q "value[?contains(name, 'prod')]"

# Get first element
-q "value[0]"
-q "definition.parts[?path=='model.tmdl'] | [0]"
```

### Error Handling & Debugging

```bash
# Show response headers
fab api workspaces --show_headers

# Verbose output
fab get "Production.Workspace/Item" -v

# Save responses for debugging
fab api workspaces -o /tmp/workspaces.json
```

### Performance Optimization

1. **Use `ls` for fast listing** - Much faster than `get`
2. **Use `exists` before operations** - Check before get/modify
3. **Filter with `-q`** - Get only what you need
4. **Use GUIDs in automation** - More stable than names

## Common Flags

- `-f, --force` - Skip confirmation prompts
- `-v, --verbose` - Verbose output
- `-l` - Long format listing
- `-a` - Show hidden items
- `-o, --output` - Output file path
- `-i, --input` - Input file or JSON string
- `-q, --query` - JMESPath query
- `-P, --params` - Parameters (key=value)
- `-X, --method` - HTTP method (get/post/put/delete/patch)
- `-A, --audience` - API audience (fabric/powerbi/storage/azure)
- `--show_headers` - Show response headers
- `--timeout` - Timeout in seconds

## Important Notes

- **All examples assume `fab` is installed and authenticated**
- **Paths require proper extensions** (`.Workspace`, `.SemanticModel`, etc.)
- **Quote paths with spaces**: `"My Workspace.Workspace"`
- **Use `-f` for non-interactive scripts** (skips prompts)
- **Semantic model updates**: Use Power BI API (`-A powerbi`) for DAX queries and dataset operations

## Need More Details?

For specific item type help:

```bash
fab desc .<ItemType>
```

For command help:

```bash
fab --help
fab <command> --help
```

## References

**Skill references:**

- [Querying Data](./references/querying-data.md) - Query semantic models and lakehouse tables
- [Semantic Models](./references/semantic-models.md) - TMDL, DAX, refresh, storage mode
- [Reports](./references/reports.md) - Export, import, visuals, fields
- [Notebooks](./references/notebooks.md) - Job execution, parameters
- [Workspaces](./references/workspaces.md) - Create, manage, permissions
- [API Reference](./references/fab-api.md) - Capacities, gateways, pipelines, domains, dataflows, apps, admin
- [Full Command Reference](./references/reference.md) - All commands detailed
- [Quick Start Guide](./references/quickstart.md) - Copy-paste examples

**External references** (request markdown when possible):

- fab CLI: [GitHub Source](https://github.com/microsoft/fabric-cli) | [Docs](https://microsoft.github.io/fabric-cli/)
- Microsoft: [Fabric CLI Learn](https://learn.microsoft.com/en-us/rest/api/fabric/articles/fabric-command-line-interface)
- APIs: [Fabric API](https://learn.microsoft.com/en-us/rest/api/fabric/articles/) | [Power BI API](https://learn.microsoft.com/en-us/rest/api/power-bi/)
- DAX: [dax.guide](https://dax.guide/) - use `dax.guide/<function>/` e.g. `dax.guide/addcolumns/`
- Power Query: [powerquery.guide](https://powerquery.guide/) - use `powerquery.guide/function/<function>`
- [Power Query Best Practices](https://learn.microsoft.com/en-us/power-query/best-practices)
