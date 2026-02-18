---
name: fabric-cli-realtime
description: Use Fabric CLI for real-time intelligence — eventhouses, eventstreams, KQL databases, and Activator alerts. Activate when users work with streaming data, real-time analytics, or time-series data.
---

# Fabric CLI Real-Time Intelligence Skill

Comprehensive skill for managing real-time analytics in Microsoft Fabric using the Fabric CLI.

## Skill Overview

Real-time intelligence in Fabric enables streaming analytics with eventhouses, eventstreams, KQL databases, and Activator alerts. This skill covers CLI operations for building and managing real-time data pipelines.

## Prerequisites

- Fabric CLI installed and authenticated (`fab auth login`)
- Workspace with Eventhouse capability
- Understanding of streaming data concepts
- Familiarity with KQL (Kusto Query Language)

## Automation Scripts

Ready-to-use Python scripts for real-time intelligence tasks. Run any script with `--help` for full options.

| Script | Purpose | Usage |
|--------|---------|-------|
| `setup_streaming.py` | Create complete streaming pipeline | `python scripts/setup_streaming.py <workspace> --name <pipeline>` |
| `kql_query.py` | Execute KQL query and return results | `python scripts/kql_query.py <database> --query <kql-file>` |
| `monitor_eventstream.py` | Check eventstream health and throughput | `python scripts/monitor_eventstream.py <eventstream>` |

Scripts are located in the `scripts/` folder of this skill.

## Core Capabilities

### 1. Eventhouse Operations

Eventhouses are optimized for streaming data ingestion and analytics.

**Create Eventhouse:**
```bash
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "TelemetryEventhouse",
  "type": "Eventhouse"
}'
```

**List Eventhouses:**
```bash
fab ls "Workspace/*.Eventhouse"
fab ls "Workspace" -q "[?type=='Eventhouse']"
```

**Get Eventhouse Details:**
```bash
fab get "Workspace/TelemetryEventhouse.Eventhouse"
fab get "Workspace/TelemetryEventhouse.Eventhouse" -q "properties"
```

### 2. KQL Database Management

KQL databases within eventhouses store streaming data.

**Create KQL Database:**
```bash
EVENTHOUSE_ID=$(fab get "Workspace/MyEventhouse.Eventhouse" -q "id" | tr -d '"')

fab api -X post "workspaces/$WS_ID/items" -i "{
  \"displayName\": \"SensorData\",
  \"type\": \"KQLDatabase\",
  \"properties\": {
    \"parentEventhouseId\": \"$EVENTHOUSE_ID\"
  }
}"
```

**List KQL Databases:**
```bash
fab ls "Workspace/*.KQLDatabase"
```

### 3. Eventstream Configuration

Eventstreams capture and route streaming data.

**Create Eventstream:**
```bash
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "IoTEventStream",
  "type": "Eventstream"
}'
```

**List Eventstreams:**
```bash
fab ls "Workspace/*.Eventstream"
```

### 4. KQL Queryset Operations

**Create KQL Queryset:**
```bash
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "SensorAnalytics",
  "type": "KQLQueryset"
}'
```

### 5. Activator (Reflex) Alerts

**Create Activator:**
```bash
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "AnomalyAlerts",
  "type": "Reflex"
}'
```

## Common Patterns

### Real-Time Pipeline Setup

```bash
#!/bin/bash
# Set up complete real-time analytics pipeline

WORKSPACE="RealTime.Workspace"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')

# 1. Create Eventhouse
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "TelemetryHub",
  "type": "Eventhouse"
}'

# 2. Create KQL Database
EVENTHOUSE_ID=$(fab get "$WORKSPACE/TelemetryHub.Eventhouse" -q "id" | tr -d '"')
fab api -X post "workspaces/$WS_ID/items" -i "{
  \"displayName\": \"SensorDB\",
  \"type\": \"KQLDatabase\",
  \"properties\": {
    \"parentEventhouseId\": \"$EVENTHOUSE_ID\"
  }
}"

# 3. Create Eventstream
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "SensorStream",
  "type": "Eventstream"
}'

# 4. Create KQL Queryset
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "SensorQueries",
  "type": "KQLQueryset"
}'

# 5. Create Activator for alerts
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "SensorAlerts",
  "type": "Reflex"
}'
```

### Streaming Data Ingestion

Configure eventstream sources:

```bash
# Get eventstream for configuration
EVENTSTREAM_ID=$(fab get "$WORKSPACE/SensorStream.Eventstream" -q "id" | tr -d '"')

# View eventstream definition
fab api "workspaces/$WS_ID/items/$EVENTSTREAM_ID/getDefinition"
```

### KQL Query Execution

```bash
# Execute KQL query via API
KQL_DB_ID=$(fab get "$WORKSPACE/SensorDB.KQLDatabase" -q "id" | tr -d '"')

fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "SensorData | where timestamp > ago(1h) | summarize count() by bin(timestamp, 5m)"
}'
```

## Item Types Reference

| Item Type | CLI Type | Purpose |
|-----------|----------|---------|
| Eventhouse | `.Eventhouse` | Streaming data store |
| KQL Database | `.KQLDatabase` | Time-series database |
| Eventstream | `.Eventstream` | Stream ingestion/routing |
| KQL Queryset | `.KQLQueryset` | Saved KQL queries |
| Activator | `.Reflex` | Alert triggers |

## Best Practices

1. **Workspace Organization**
   - Dedicate workspaces to real-time workloads
   - Separate dev/test/prod eventhouses
   - Use clear naming conventions

2. **Data Architecture**
   - Design for high-velocity ingestion
   - Partition by time for query performance
   - Set appropriate retention policies

3. **Monitoring**
   - Set up alerts for ingestion lag
   - Monitor query performance
   - Track storage consumption

4. **Security**
   - Use workspace permissions for access control
   - Implement row-level security where needed
   - Audit query access patterns

## Reference Files

- `references/eventhouse-operations.md` — Eventhouse creation and management
- `references/eventstream-patterns.md` — Eventstream configuration patterns
- `references/kql-queries.md` — KQL query examples and CLI execution
- `references/activator-alerts.md` — Alert configuration and management
- `references/streaming-patterns.md` — End-to-end streaming architectures

## Related Skills

- **fabric-cli-core** — Foundation CLI operations
- **fabric-cli-dataengineering** — Lakehouse integration patterns
- **fabric-cli-governance** — Security and compliance

## Troubleshooting

### Eventhouse Creation Fails
```bash
# Check workspace capacity supports Eventhouse
fab get "Workspace" -q "properties.capacityId"
```

### Eventstream Not Ingesting
```bash
# Check eventstream status
fab get "Workspace/MyStream.Eventstream" -q "properties"

# Verify source connection
fab api "workspaces/$WS_ID/items/$EVENTSTREAM_ID/getDefinition"
```

### KQL Query Timeout
```bash
# Add timeout parameter
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "...",
  "requestProperties": {
    "queryTimeout": "5m"
  }
}'
```
