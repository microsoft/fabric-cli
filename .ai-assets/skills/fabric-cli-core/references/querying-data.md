# Querying Data

## Query a Semantic Model (DAX)

```bash
# 1. Get workspace and model IDs
WS_ID=$(fab get "ws.Workspace" -q "id" | tr -d '"')
MODEL_ID=$(fab get "ws.Workspace/Model.SemanticModel" -q "id" | tr -d '"')

# 2. Execute DAX query
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/executeQueries" \
  -X post -i '{"queries":[{"query":"EVALUATE TOPN(10, '\''TableName'\'')"}]}'
```

## Query a Lakehouse Table

Lakehouse tables cannot be queried directly via API. Create a Direct Lake semantic model first, then query via DAX.

## Get Lakehouse SQL Endpoint

For external SQL clients:

```bash
fab get "ws.Workspace/LH.Lakehouse" -q "properties.sqlEndpointProperties"
```

Returns `connectionString` and `id` for SQL connections.
