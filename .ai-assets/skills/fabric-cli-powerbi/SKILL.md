---
name: fabric-cli-powerbi
description: Use Fabric CLI for Power BI operations — semantic models, reports, DAX queries, refresh, gateways. Activate when users work with Power BI items, need to refresh datasets, execute DAX, manage reports, or troubleshoot refresh failures.
---

# Fabric CLI Power BI Operations

Expert guidance for working with Power BI items (semantic models, reports, dashboards) using the `fab` CLI.

## When to Use This Skill

Activate automatically when tasks involve:

- Semantic model (dataset) operations — get, export, refresh, update
- Report management — export, clone, rebind to different model
- Executing DAX queries against semantic models
- Managing refresh schedules and troubleshooting failures
- Gateway and data source configuration
- TMDL (Tabular Model Definition Language) operations

## Prerequisites

- Load `fabric-cli-core` skill first for foundational CLI guidance
- User must be authenticated: `fab auth status`
- Appropriate workspace permissions for target items

## Automation Scripts

Ready-to-use Python scripts for Power BI tasks. Run any script with `--help` for full options.

| Script | Purpose | Usage |
|--------|---------|-------|
| `refresh_model.py` | Trigger and monitor semantic model refresh | `python scripts/refresh_model.py <model> [--wait] [--timeout 300]` |
| `list_refresh_history.py` | Show refresh history and failure details | `python scripts/list_refresh_history.py <model> [--last N]` |
| `rebind_report.py` | Rebind report to different semantic model | `python scripts/rebind_report.py <report> --model <new-model>` |

Scripts are located in the `scripts/` folder of this skill.

## 1 - Power BI Item Types

| Entity Suffix | Type | Description |
|---------------|------|-------------|
| `.SemanticModel` | Semantic Model | Power BI dataset (tabular model) |
| `.Report` | Report | Power BI report (visualizations) |
| `.Dashboard` | Dashboard | Power BI dashboard (pinned tiles) |
| `.Dataflow` | Dataflow | Power Query dataflow |
| `.PaginatedReport` | Paginated Report | RDL-based paginated report |

### Path Examples

```
# Semantic model
Production.Workspace/Sales.SemanticModel

# Report connected to model
Production.Workspace/SalesReport.Report

# Dashboard
Production.Workspace/ExecutiveDash.Dashboard
```

## 2 - Semantic Model Operations

### Get Model Information

```bash
# Check if model exists
fab exists "ws.Workspace/Model.SemanticModel"

# Get model properties
fab get "ws.Workspace/Model.SemanticModel"

# Get model ID (needed for Power BI API calls)
fab get "ws.Workspace/Model.SemanticModel" -q "id"

# Get full definition (TMDL)
fab get "ws.Workspace/Model.SemanticModel" -q "definition"
```

### Export Model

```bash
# Export to local directory (PBIP format with TMDL)
fab export "ws.Workspace/Model.SemanticModel" -o ./exports -f
```

Creates folder structure:
```
Model.SemanticModel/
├── .platform
├── definition.pbism
└── definition/
    ├── model.tmdl
    ├── tables/
    │   ├── Sales.tmdl
    │   └── Date.tmdl
    └── relationships.tmdl
```

### Import/Update Model

```bash
# Import from PBIP folder
fab import "ws.Workspace/Model.SemanticModel" -i ./exports/Model.SemanticModel -f

# Copy between workspaces
fab cp "Dev.Workspace/Model.SemanticModel" "Prod.Workspace/Model.SemanticModel" -f
```

## 3 - Refresh Operations

### Trigger Refresh

```bash
# Get IDs
WS_ID=$(fab get "ws.Workspace" -q "id" | tr -d '"')
MODEL_ID=$(fab get "ws.Workspace/Model.SemanticModel" -q "id" | tr -d '"')

# Trigger full refresh
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{"type":"Full"}'

# Check refresh status
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes?\$top=1"
```

### Enhanced Refresh (Partition-Level)

```bash
# Refresh specific tables
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{
  "type": "Full",
  "commitMode": "transactional",
  "objects": [
    {"table": "Sales"},
    {"table": "Inventory"}
  ]
}'

# Refresh with retry
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{
  "type": "Full",
  "retryCount": 3
}'
```

### Refresh Schedule

```bash
# Get current schedule
fab api -A powerbi "datasets/$MODEL_ID/refreshSchedule"

# Set daily refresh at 6 AM UTC
fab api -A powerbi "datasets/$MODEL_ID/refreshSchedule" -X patch -i '{
  "enabled": true,
  "days": ["Monday","Tuesday","Wednesday","Thursday","Friday"],
  "times": ["06:00"],
  "localTimeZoneId": "UTC"
}'
```

### Troubleshoot Refresh Failures

```bash
# Get refresh history
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes"

# Common failure patterns:
# - "credentials" → Update data source credentials
# - "gateway" → Check gateway status
# - "timeout" → Use enhanced refresh with smaller batches
# - "memory" → Optimize model or use incremental refresh
```

## 4 - DAX Query Execution

Execute DAX queries against semantic models:

```bash
MODEL_ID=$(fab get "ws.Workspace/Model.SemanticModel" -q "id" | tr -d '"')

# Simple query
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{"query": "EVALUATE VALUES(Date[Year])"}]
}'

# Aggregation query
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{
    "query": "EVALUATE SUMMARIZECOLUMNS(Date[Year], \"Total\", SUM(Sales[Amount]))"
  }]
}'

# TOPN query
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{
    "query": "EVALUATE TOPN(10, Product, [Total Sales], DESC)"
  }]
}'

# Query with parameters
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{
    "query": "EVALUATE FILTER(Sales, Sales[Year] = @Year)",
    "parameters": [{"name": "@Year", "value": "2024"}]
  }]
}'
```

## 5 - Report Operations

### Get Report Info

```bash
# Check exists
fab exists "ws.Workspace/Report.Report"

# Get properties
fab get "ws.Workspace/Report.Report"

# Get connected model
fab get "ws.Workspace/Report.Report" -q "definition.parts[?contains(path, 'definition.pbir')].payload | [0]"
```

### Export Report

```bash
# Export to PBIP format
fab export "ws.Workspace/Report.Report" -o ./exports -f
```

### Clone Report

```bash
# Copy within workspace
fab cp "ws.Workspace/Report.Report" "ws.Workspace/ReportCopy.Report" -f

# Copy to another workspace
fab cp "Dev.Workspace/Report.Report" "Prod.Workspace/Report.Report" -f
```

### Rebind Report to Different Model

```bash
WS_ID=$(fab get "ws.Workspace" -q "id" | tr -d '"')
REPORT_ID=$(fab get "ws.Workspace/Report.Report" -q "id" | tr -d '"')
NEW_MODEL_ID=$(fab get "ws.Workspace/NewModel.SemanticModel" -q "id" | tr -d '"')

fab api -A powerbi "groups/$WS_ID/reports/$REPORT_ID/Rebind" -X post -i "{
  \"datasetId\": \"$NEW_MODEL_ID\"
}"
```

### Export Report to File (PDF/PPTX)

```bash
# Export to PDF
fab api -A powerbi "groups/$WS_ID/reports/$REPORT_ID/ExportTo" -X post -i '{
  "format": "PDF"
}'

# Poll for completion, then download
```

## 6 - Gateway Operations

### List Gateways

```bash
# Tenant-level gateways (hidden entity)
fab ls .gateways

# Get gateway details
fab get ".gateways/MyGateway.Gateway"
```

### Data Source Management

```bash
GATEWAY_ID=$(fab get ".gateways/MyGateway.Gateway" -q "id" | tr -d '"')

# List data sources on gateway
fab api -A powerbi "gateways/$GATEWAY_ID/datasources"

# Get data source status
fab api -A powerbi "gateways/$GATEWAY_ID/datasources/$DATASOURCE_ID"
```

### Update Data Source Credentials

```bash
# Update credentials (basic auth example)
fab api -A powerbi "gateways/$GATEWAY_ID/datasources/$DATASOURCE_ID" -X patch -i '{
  "credentialDetails": {
    "credentialType": "Basic",
    "credentials": "{\"credentialData\":[{\"name\":\"username\",\"value\":\"user\"},{\"name\":\"password\",\"value\":\"pass\"}]}",
    "encryptedConnection": "Encrypted",
    "encryptionAlgorithm": "None",
    "privacyLevel": "Organizational"
  }
}'
```

## 7 - Take Over Ownership

When a semantic model owner leaves the organization:

```bash
WS_ID=$(fab get "ws.Workspace" -q "id" | tr -d '"')
MODEL_ID=$(fab get "ws.Workspace/Model.SemanticModel" -q "id" | tr -d '"')

# Take over semantic model ownership
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/Default.TakeOver" -X post
```

## 8 - Common Patterns

### Dev to Production Deployment

```bash
#!/bin/bash
DEV_WS="Dev.Workspace"
PROD_WS="Prod.Workspace"

# 1. Export from dev
fab export "$DEV_WS/Sales.SemanticModel" -o ./deploy -f
fab export "$DEV_WS/SalesReport.Report" -o ./deploy -f

# 2. Import to prod
fab import "$PROD_WS/Sales.SemanticModel" -i ./deploy/Sales.SemanticModel -f
fab import "$PROD_WS/SalesReport.Report" -i ./deploy/SalesReport.Report -f

# 3. Trigger refresh
PROD_WS_ID=$(fab get "$PROD_WS" -q "id" | tr -d '"')
MODEL_ID=$(fab get "$PROD_WS/Sales.SemanticModel" -q "id" | tr -d '"')
fab api -A powerbi "groups/$PROD_WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{"type":"Full"}'

# 4. Verify
fab api -A powerbi "groups/$PROD_WS_ID/datasets/$MODEL_ID/refreshes?\$top=1" -q "value[0].status"
```

### Backup Semantic Model

```bash
# Export definition for version control
fab export "Prod.Workspace/Model.SemanticModel" -o ./backups/$(date +%Y%m%d) -f
git add ./backups/
git commit -m "Backup Model $(date +%Y-%m-%d)"
```

### Incremental Refresh Setup

For large models, use incremental refresh:

1. Configure in Power BI Desktop with RangeStart/RangeEnd parameters
2. Publish to workspace
3. First refresh creates partitions:

```bash
# Monitor partition creation
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes?\$top=5"
```

## 9 - Safety Guidelines

- **Always verify workspace context** before refresh operations
- **Test in dev first** — never refresh production without testing
- **Monitor refresh duration** — set appropriate timeouts
- **Backup before major changes** — export definition before updates
- **Use enhanced refresh** for large models to avoid timeouts

## 10 - References

For detailed patterns, see:

- [references/semantic-models.md](./references/semantic-models.md) — Full TMDL operations
- [references/reports.md](./references/reports.md) — Report management
- [references/refresh.md](./references/refresh.md) — Refresh troubleshooting
- [references/dax-queries.md](./references/dax-queries.md) — Advanced DAX patterns
- [references/gateways.md](./references/gateways.md) — Gateway configuration
