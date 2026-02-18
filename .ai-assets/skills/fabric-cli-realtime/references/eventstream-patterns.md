# Eventstream Patterns Reference

Guide to configuring Eventstreams for streaming data pipelines in Fabric.

## Understanding Eventstreams

Eventstreams provide no-code stream processing:

- **Sources** — Ingest from Event Hubs, IoT Hub, custom apps
- **Destinations** — Route to KQL databases, lakehouses, reflexes
- **Transformations** — Filter, aggregate, enrich in-flight
- **Real-time** — Sub-second latency processing

## Creating Eventstreams

### Basic Creation

```bash
WS_ID=$(fab get "Workspace" -q "id" | tr -d '"')

fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "SensorEventStream",
  "type": "Eventstream",
  "description": "IoT sensor data ingestion"
}'
```

### Verify Creation

```bash
# List eventstreams
fab ls "Workspace/*.Eventstream"

# Get details
fab get "Workspace/SensorEventStream.Eventstream"
```

## Managing Eventstreams

### List Eventstreams

```bash
# All eventstreams in workspace
fab ls "Workspace/*.Eventstream" -l

# With filtering
fab api "workspaces/$WS_ID/items" -q "value[?type=='Eventstream']"
```

### Get Eventstream Definition

```bash
EVENTSTREAM_ID=$(fab get "Workspace/MyStream.Eventstream" -q "id" | tr -d '"')

# Get full definition
fab api "workspaces/$WS_ID/items/$EVENTSTREAM_ID/getDefinition"

# Get specific configuration
fab api "workspaces/$WS_ID/items/$EVENTSTREAM_ID/getDefinition" -q "definition.parts"
```

### Update Eventstream Definition

```bash
# Get current definition
DEFINITION=$(fab api "workspaces/$WS_ID/items/$EVENTSTREAM_ID/getDefinition")

# Update definition (after modifying)
fab api -X post "workspaces/$WS_ID/items/$EVENTSTREAM_ID/updateDefinition" -i '{
  "definition": {
    "parts": [...]
  }
}'
```

### Delete Eventstream

```bash
fab rm "Workspace/OldStream.Eventstream"

# Or via API
fab api -X delete "workspaces/$WS_ID/items/$EVENTSTREAM_ID"
```

## Source Configuration

### Event Hub Source

```bash
# Configure Event Hub as source
# (Typically done via UI, definition shown for reference)
{
  "sources": [{
    "type": "EventHub",
    "eventHubNamespaceName": "my-namespace",
    "eventHubName": "sensor-data",
    "consumerGroup": "$Default",
    "connectionId": "<connection-id>"
  }]
}
```

### IoT Hub Source

```bash
# IoT Hub configuration
{
  "sources": [{
    "type": "IoTHub",
    "iotHubName": "my-iothub",
    "consumerGroup": "$Default",
    "connectionId": "<connection-id>"
  }]
}
```

### Custom Endpoint Source

```bash
# Get custom endpoint for API ingestion
fab api "workspaces/$WS_ID/items/$EVENTSTREAM_ID/getDefinition" -q "definition.sources[?type=='CustomEndpoint'].endpoint"
```

### Sample Data Source

```bash
# Useful for testing
{
  "sources": [{
    "type": "SampleData",
    "datasetName": "StockTrades"
  }]
}
```

## Destination Configuration

### KQL Database Destination

```bash
# Route to KQL database
{
  "destinations": [{
    "type": "KQLDatabase",
    "kqlDatabaseId": "<kql-db-id>",
    "tableName": "SensorReadings",
    "inputDataFormat": "Json",
    "mappingRuleName": "SensorMapping"
  }]
}
```

### Lakehouse Destination

```bash
# Route to lakehouse table
{
  "destinations": [{
    "type": "Lakehouse",
    "lakehouseId": "<lakehouse-id>",
    "tableName": "streaming_data",
    "inputDataFormat": "Json"
  }]
}
```

### Reflex (Activator) Destination

```bash
# Route to Activator for alerting
{
  "destinations": [{
    "type": "Reflex",
    "reflexId": "<reflex-id>"
  }]
}
```

## Transformation Patterns

### Filter Transformation

Filter events based on conditions:

```bash
# Filter definition
{
  "transformations": [{
    "type": "Filter",
    "condition": "temperature > 100"
  }]
}
```

### Aggregate Transformation

Windowed aggregations:

```bash
# Tumbling window aggregation
{
  "transformations": [{
    "type": "Aggregate",
    "windowType": "Tumbling",
    "windowSize": "PT5M",
    "groupBy": ["deviceId"],
    "aggregates": [
      {"function": "Avg", "column": "temperature", "alias": "avgTemp"},
      {"function": "Max", "column": "temperature", "alias": "maxTemp"}
    ]
  }]
}
```

### Derived Column

Add computed columns:

```bash
{
  "transformations": [{
    "type": "DerivedColumn",
    "columns": [{
      "name": "processed_time",
      "expression": "CURRENT_TIMESTAMP()"
    }]
  }]
}
```

## End-to-End Patterns

### IoT Telemetry Pipeline

```bash
#!/bin/bash
# Set up IoT telemetry streaming pipeline

WORKSPACE="IoT.Workspace"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')

# 1. Create Eventstream
echo "Creating eventstream..."
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "IoTTelemetryStream",
  "type": "Eventstream"
}'

# 2. Get eventhouse and KQL database IDs
EVENTHOUSE_ID=$(fab get "$WORKSPACE/TelemetryHub.Eventhouse" -q "id" | tr -d '"')
KQL_DB_ID=$(fab get "$WORKSPACE/DeviceData.KQLDatabase" -q "id" | tr -d '"')

# 3. Create connection for Event Hub
echo "Setting up Event Hub connection..."
fab api -X post "connections" -i '{
  "displayName": "IoTEventHubConnection",
  "connectionDetails": {
    "type": "EventHub",
    "parameters": {
      "server": "my-namespace.servicebus.windows.net",
      "eventHub": "telemetry"
    }
  },
  "credentialDetails": {
    "credentialType": "SharedAccessKey"
  }
}'

echo "Eventstream created. Configure sources and destinations in UI."
```

### Multi-Destination Routing

Route same stream to multiple destinations:

```bash
#!/bin/bash
# Configure eventstream for multi-destination routing

WORKSPACE="Analytics.Workspace"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')

# Create eventstream
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "MultiRouteStream",
  "type": "Eventstream",
  "description": "Routes to KQL, Lakehouse, and Activator"
}'

echo "Configure in UI:"
echo "1. Add source (Event Hub/IoT Hub/Custom Endpoint)"
echo "2. Add KQL Database destination for real-time queries"
echo "3. Add Lakehouse destination for historical analysis"
echo "4. Add Activator destination for alerting"
```

### Stream Processing with Aggregation

```bash
#!/bin/bash
# Set up aggregation stream

WORKSPACE="Metrics.Workspace"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')

# Create raw eventstream
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "RawMetricsStream",
  "type": "Eventstream"
}'

# Create aggregated eventstream
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "AggregatedMetricsStream",
  "type": "Eventstream",
  "description": "5-minute aggregated metrics"
}'

echo "Configure aggregation:"
echo "1. RawMetricsStream: Source -> Lakehouse (raw data)"
echo "2. AggregatedMetricsStream: Derived from raw with 5-min tumbling window -> KQL"
```

## Connection Management

### List Streaming Connections

```bash
# List all connections
fab ls ".connections" -l

# Filter for Event Hub connections
fab ls ".connections/*.Connection" -q "[?type=='EventHub']"
```

### Create Event Hub Connection

```bash
fab api -X post "connections" -i '{
  "displayName": "EventHubConn",
  "connectionDetails": {
    "type": "EventHub",
    "parameters": {
      "server": "namespace.servicebus.windows.net",
      "eventHub": "eventhub-name"
    }
  },
  "credentialDetails": {
    "credentialType": "SharedAccessKey",
    "sharedAccessKey": {
      "keyName": "RootManageSharedAccessKey",
      "key": "<key-value>"
    }
  }
}'
```

### Create IoT Hub Connection

```bash
fab api -X post "connections" -i '{
  "displayName": "IoTHubConn",
  "connectionDetails": {
    "type": "IoTHub",
    "parameters": {
      "server": "iothub-name.azure-devices.net"
    }
  },
  "credentialDetails": {
    "credentialType": "SharedAccessKey"
  }
}'
```

## Monitoring Eventstreams

### Check Stream Status

```bash
# Get eventstream properties
fab get "Workspace/MyStream.Eventstream" -q "properties"

# Check for errors in definition
fab api "workspaces/$WS_ID/items/$EVENTSTREAM_ID/getDefinition" -q "definition.errors"
```

### View Metrics (via KQL)

If routing to KQL database, query ingestion metrics:

```bash
# Query events processed
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "TableName | where ingestion_time() > ago(1h) | summarize count() by bin(ingestion_time(), 5m)"
}'
```

## Best Practices

### Design Principles

1. **Single Responsibility** — One eventstream per data domain
2. **Schema Evolution** — Design for schema changes
3. **Error Handling** — Configure dead-letter destinations
4. **Monitoring** — Route subset to monitoring tables

### Naming Conventions

| Component | Convention | Example |
|-----------|------------|---------|
| Eventstream | `<Source><Domain>Stream` | `IoTSensorStream` |
| Connections | `<Service>Conn` | `EventHubConn` |

### Performance Tips

- Use appropriate partitioning at source
- Configure batching for destinations
- Filter early in the pipeline
- Monitor for backpressure

## Troubleshooting

### Stream Not Receiving Data

```bash
# Check eventstream status
fab get "Workspace/MyStream.Eventstream"

# Verify source connection
fab ls ".connections" -l

# Check connection credentials
fab get ".connections/EventHubConn.Connection" -q "credentialDetails"
```

### High Latency

```bash
# Check destination configuration
# Ensure batching is appropriate for use case
# Monitor Event Hub/IoT Hub consumer lag
```

### Data Loss

```bash
# Verify checkpointing is enabled
# Check consumer group offset
# Review dead-letter queue if configured
```
