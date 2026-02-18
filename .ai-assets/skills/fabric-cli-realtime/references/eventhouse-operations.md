# Eventhouse Operations Reference

Complete guide to managing Eventhouses in Microsoft Fabric using CLI.

## Understanding Eventhouses

Eventhouses are optimized storage for high-velocity streaming data:

- **High throughput** — Millions of events per second
- **Time-series optimized** — Built for temporal queries
- **Auto-scaling** — Adapts to ingestion volume
- **Integrated** — Works with Eventstreams, KQL, Activator

## Creating Eventhouses

### Basic Creation

```bash
WS_ID=$(fab get "Workspace" -q "id" | tr -d '"')

fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "TelemetryEventhouse",
  "type": "Eventhouse",
  "description": "Central telemetry data store"
}'
```

### Verify Creation

```bash
# List eventhouses
fab ls "Workspace/*.Eventhouse"

# Get details
fab get "Workspace/TelemetryEventhouse.Eventhouse"
```

## Managing Eventhouses

### List All Eventhouses

```bash
# In current workspace
fab ls "Workspace/*.Eventhouse" -l

# Across all workspaces (admin)
fab ls -R "*.Eventhouse"

# With specific details
fab api "workspaces/$WS_ID/items" -q "value[?type=='Eventhouse'].{name: displayName, id: id}"
```

### Get Eventhouse Properties

```bash
EVENTHOUSE_ID=$(fab get "Workspace/MyEventhouse.Eventhouse" -q "id" | tr -d '"')

# Full properties
fab api "workspaces/$WS_ID/items/$EVENTHOUSE_ID"

# Specific property
fab get "Workspace/MyEventhouse.Eventhouse" -q "properties.state"
```

### Update Eventhouse

```bash
# Update display name
fab api -X patch "workspaces/$WS_ID/items/$EVENTHOUSE_ID" -i '{
  "displayName": "RenamedEventhouse"
}'

# Update description
fab api -X patch "workspaces/$WS_ID/items/$EVENTHOUSE_ID" -i '{
  "description": "Updated description for telemetry eventhouse"
}'
```

### Delete Eventhouse

```bash
# Delete by path
fab rm "Workspace/OldEventhouse.Eventhouse"

# Delete by ID
fab api -X delete "workspaces/$WS_ID/items/$EVENTHOUSE_ID"
```

## KQL Database Management

Each eventhouse can contain multiple KQL databases.

### Create KQL Database

```bash
EVENTHOUSE_ID=$(fab get "Workspace/MyEventhouse.Eventhouse" -q "id" | tr -d '"')

fab api -X post "workspaces/$WS_ID/items" -i "{
  \"displayName\": \"SensorData\",
  \"type\": \"KQLDatabase\",
  \"properties\": {
    \"parentEventhouseId\": \"$EVENTHOUSE_ID\",
    \"configuration\": {
      \"kind\": \"ReadWrite\"
    }
  }
}"
```

### List KQL Databases

```bash
# All KQL databases in workspace
fab ls "Workspace/*.KQLDatabase"

# Get parent eventhouse
fab get "Workspace/SensorData.KQLDatabase" -q "properties.parentEventhouseId"
```

### Shortcut Database (Read-Only)

Create a read-only reference to another KQL database:

```bash
# Create shortcut database
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "SharedSensorData",
  "type": "KQLDatabase",
  "properties": {
    "parentEventhouseId": "<local-eventhouse-id>",
    "configuration": {
      "kind": "ReadOnly",
      "sourceKqlDatabaseId": "<source-kql-db-id>"
    }
  }
}'
```

## Table Operations

### Create Table via KQL

```bash
KQL_DB_ID=$(fab get "Workspace/SensorData.KQLDatabase" -q "id" | tr -d '"')

# Execute table creation command
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".create table SensorReadings (timestamp: datetime, deviceId: string, temperature: real, humidity: real)"
}'
```

### Create Table with Mapping

```bash
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".create table SensorReadings ingestion json mapping \"SensorMapping\" \"[{\"column\":\"timestamp\",\"path\":\"$.ts\"},{\"column\":\"deviceId\",\"path\":\"$.device\"},{\"column\":\"temperature\",\"path\":\"$.temp\"},{\"column\":\"humidity\",\"path\":\"$.humid\"}]\""
}'
```

### List Tables

```bash
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".show tables"
}'
```

### Drop Table

```bash
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".drop table SensorReadings"
}'
```

## Configuration Options

### Data Retention

```bash
# Set retention policy
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".alter-merge table SensorReadings policy retention softdelete = 30d recoverability = enabled"
}'
```

### Caching Policy

```bash
# Configure hot cache period
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".alter table SensorReadings policy caching hot = 7d"
}'
```

### Ingestion Batching

```bash
# Configure batching for ingestion
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".alter table SensorReadings policy ingestionbatching @\"{ \\\"MaximumBatchingTimeSpan\\\": \\\"00:00:30\\\", \\\"MaximumNumberOfItems\\\": 500, \\\"MaximumRawDataSizeMB\\\": 100 }\""
}'
```

## Automation Scripts

### Complete Eventhouse Setup

```bash
#!/bin/bash
# Create complete eventhouse with KQL database and tables

WORKSPACE="RealTime.Workspace"
EVENTHOUSE_NAME="TelemetryHub"
DATABASE_NAME="DeviceData"

WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')

# 1. Create Eventhouse
echo "Creating eventhouse..."
fab api -X post "workspaces/$WS_ID/items" -i "{
  \"displayName\": \"$EVENTHOUSE_NAME\",
  \"type\": \"Eventhouse\"
}"

sleep 10

# 2. Get Eventhouse ID
EVENTHOUSE_ID=$(fab get "$WORKSPACE/$EVENTHOUSE_NAME.Eventhouse" -q "id" | tr -d '"')
echo "Eventhouse ID: $EVENTHOUSE_ID"

# 3. Create KQL Database
echo "Creating KQL database..."
fab api -X post "workspaces/$WS_ID/items" -i "{
  \"displayName\": \"$DATABASE_NAME\",
  \"type\": \"KQLDatabase\",
  \"properties\": {
    \"parentEventhouseId\": \"$EVENTHOUSE_ID\"
  }
}"

sleep 10

# 4. Get Database ID
KQL_DB_ID=$(fab get "$WORKSPACE/$DATABASE_NAME.KQLDatabase" -q "id" | tr -d '"')
echo "KQL Database ID: $KQL_DB_ID"

# 5. Create tables
echo "Creating tables..."
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".create table DeviceReadings (timestamp: datetime, deviceId: string, metric: string, value: real)"
}'

fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".create table DeviceEvents (timestamp: datetime, deviceId: string, eventType: string, details: dynamic)"
}'

# 6. Set retention policies
echo "Configuring policies..."
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".alter-merge table DeviceReadings policy retention softdelete = 90d"
}'

echo "Eventhouse setup complete!"
```

### Multi-Environment Deployment

```bash
#!/bin/bash
# Deploy eventhouse across environments

ENVIRONMENTS=("Dev" "Test" "Prod")
BASE_NAME="TelemetryHub"

for ENV in "${ENVIRONMENTS[@]}"; do
  WORKSPACE="${ENV}RealTime.Workspace"
  WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')
  
  echo "Deploying to $ENV environment..."
  
  fab api -X post "workspaces/$WS_ID/items" -i "{
    \"displayName\": \"${BASE_NAME}_${ENV}\",
    \"type\": \"Eventhouse\",
    \"description\": \"$ENV environment eventhouse\"
  }"
  
  echo "Created $BASE_NAME in $ENV"
done
```

## Monitoring

### Check Eventhouse Status

```bash
# Get eventhouse state
fab get "Workspace/MyEventhouse.Eventhouse" -q "properties"

# Check all eventhouses in workspace
fab ls "Workspace/*.Eventhouse" -l -q "[].{name: displayName, state: properties.state}"
```

### Ingestion Metrics

```bash
# Query ingestion statistics
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".show ingestion failures | where FailedOn > ago(1h)"
}'

# Recent ingestion volume
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".show commands | where StartedOn > ago(1h) | where CommandType == \"DataIngestPull\" | summarize count() by bin(StartedOn, 5m)"
}'
```

## Best Practices

### Naming Conventions

| Component | Convention | Example |
|-----------|------------|---------|
| Eventhouse | `<Domain>Eventhouse` | `TelemetryEventhouse` |
| KQL Database | `<DataDomain>DB` | `SensorDataDB` |
| Tables | `<Entity><Type>` | `DeviceReadings`, `SystemEvents` |

### Capacity Planning

- Monitor ingestion rate trends
- Set appropriate retention based on query patterns
- Use caching policies for frequently queried data
- Consider partitioning for large tables

### Security

- Use workspace roles for access control
- Configure row-level security for multi-tenant scenarios
- Audit data access patterns

## Troubleshooting

### Eventhouse Creation Timeout

```bash
# Check workspace capacity
fab get "Workspace" -q "properties.capacityId"

# Verify capacity supports Eventhouse
fab api "capacities/<capacity-id>" -q "properties.sku"
```

### KQL Database Connection Issues

```bash
# Verify database state
fab get "Workspace/MyDB.KQLDatabase" -q "properties.state"

# Check parent eventhouse
PARENT_ID=$(fab get "Workspace/MyDB.KQLDatabase" -q "properties.parentEventhouseId" | tr -d '"')
fab api "workspaces/$WS_ID/items/$PARENT_ID"
```

### Ingestion Failures

```bash
# View recent failures
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".show ingestion failures | where FailedOn > ago(1h) | project FailedOn, FailureKind, Details | take 50"
}'
```
