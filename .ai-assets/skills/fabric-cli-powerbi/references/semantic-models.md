# Semantic Models Reference

Working with Power BI semantic models (formerly datasets) via Fabric CLI.

## Item Type

Use `.SemanticModel` suffix when referencing semantic models:

```bash
# Reference format
ws.Workspace/ModelName.SemanticModel
```

## List Semantic Models

```bash
# List in current workspace
fab ls . -t SemanticModel

# List in specific workspace
fab ls "ws.Workspace" -t SemanticModel

# List with verbose details
fab ls "ws.Workspace" -t SemanticModel -v
```

## Get Model Details

```bash
# Get model metadata
fab get "ws.Workspace/Model.SemanticModel"

# Get specific property
fab get "ws.Workspace/Model.SemanticModel" -q "id"

# Store ID for API calls
MODEL_ID=$(fab get "ws.Workspace/Model.SemanticModel" -q "id" | tr -d '"')
```

## Export Semantic Model

### Export as PBIX (Power BI Desktop)

```bash
fab export "ws.Workspace/Model.SemanticModel" -d ./exports
```

### Export via API

```bash
WS_ID=$(fab get "ws.Workspace" -q "id" | tr -d '"')
MODEL_ID=$(fab get "ws.Workspace/Model.SemanticModel" -q "id" | tr -d '"')

# Start export
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/Default.Export" -X post -o model.pbix
```

## Import Semantic Model

### Import PBIX

```bash
fab import ./model.pbix -d "ws.Workspace"

# With conflict handling (CreateOrOverwrite)
fab import ./model.pbix -d "ws.Workspace" -c CreateOrOverwrite
```

### Import via Large Upload API

For files >1GB:

```bash
# Create upload session
fab api -A powerbi "groups/$WS_ID/imports/createUploadSession" -X post -i '{
  "nameConflict": "CreateOrOverwrite",
  "name": "LargeModel"
}'
```

## Clone Semantic Model

```bash
# Get source model details
SOURCE_WS_ID=$(fab get "source.Workspace" -q "id" | tr -d '"')
SOURCE_MODEL_ID=$(fab get "source.Workspace/Model.SemanticModel" -q "id" | tr -d '"')
TARGET_WS_ID=$(fab get "target.Workspace" -q "id" | tr -d '"')

# Clone to target workspace
fab api -A powerbi "groups/$SOURCE_WS_ID/datasets/$SOURCE_MODEL_ID/Default.Clone" -X post -i '{
  "targetWorkspaceId": "'"$TARGET_WS_ID"'",
  "targetModelName": "ModelCopy"
}'
```

## Model Configuration

### Get Model Parameters

```bash
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/parameters"
```

### Update Parameters

```bash
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/Default.UpdateParameters" -X post -i '{
  "updateDetails": [
    {
      "name": "ServerName",
      "newValue": "newserver.database.windows.net"
    },
    {
      "name": "DatabaseName", 
      "newValue": "newdatabase"
    }
  ]
}'
```

### Get Data Sources

```bash
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/datasources"
```

### Update Data Sources

```bash
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/Default.UpdateDatasources" -X post -i '{
  "updateDetails": [
    {
      "datasourceSelector": {
        "datasourceType": "Sql",
        "connectionDetails": {
          "server": "oldserver.database.windows.net",
          "database": "olddb"
        }
      },
      "connectionDetails": {
        "server": "newserver.database.windows.net",
        "database": "newdb"
      }
    }
  ]
}'
```

## Model Permissions

### Take Over Ownership

```bash
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/Default.TakeOver" -X post
```

### Get Model Users

```bash
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/users"
```

### Add Model User

```bash
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/users" -X post -i '{
  "identifier": "user@contoso.com",
  "principalType": "User",
  "datasetUserAccessRight": "Read"
}'
```

## Model Lineage

### Get Upstream Datasets

```bash
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/upstreamDatasets"
```

## Quick Reference

| Operation | Command |
|-----------|---------|
| List models | `fab ls "ws.Workspace" -t SemanticModel` |
| Get model | `fab get "ws.Workspace/Model.SemanticModel"` |
| Export PBIX | `fab export "ws.Workspace/Model.SemanticModel" -d ./` |
| Import PBIX | `fab import ./model.pbix -d "ws.Workspace"` |
| Get parameters | `fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/parameters"` |
| Take over | `fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/Default.TakeOver" -X post` |

## See Also

- [Refresh Operations](./refresh.md) - Refresh semantic models
- [DAX Queries](./dax-queries.md) - Query semantic model data
- [Gateways](./gateways.md) - Gateway binding
