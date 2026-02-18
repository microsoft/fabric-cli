# Streaming Patterns Reference

End-to-end streaming architecture patterns for Microsoft Fabric.

## Architecture Overview

Fabric real-time intelligence provides a complete streaming platform:

```
Sources                    Processing                Storage/Analysis           Consumption
─────────                  ──────────                ────────────────           ───────────
Event Hub    ─┐                                      ┌─ KQL Database ──── KQL Queries
IoT Hub      ─┼─► Eventstream ─► Transform ─────────┼─ Lakehouse ─────── Notebooks
Custom API   ─┤                                      └─ Activator ─────── Alerts
Kafka        ─┘
```

## Pattern 1: IoT Telemetry Pipeline

### Use Case
Process millions of IoT sensor readings with real-time analytics and alerting.

### Architecture

```bash
#!/bin/bash
# IoT Telemetry Pipeline Setup

WORKSPACE="IoTAnalytics.Workspace"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')

# 1. Create Eventhouse for time-series data
echo "Creating Eventhouse..."
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "TelemetryHub",
  "type": "Eventhouse"
}'

sleep 15
EVENTHOUSE_ID=$(fab get "$WORKSPACE/TelemetryHub.Eventhouse" -q "id" | tr -d '"')

# 2. Create KQL Database for hot data
echo "Creating KQL Database..."
fab api -X post "workspaces/$WS_ID/items" -i "{
  \"displayName\": \"SensorDataDB\",
  \"type\": \"KQLDatabase\",
  \"properties\": {
    \"parentEventhouseId\": \"$EVENTHOUSE_ID\"
  }
}"

sleep 10
KQL_DB_ID=$(fab get "$WORKSPACE/SensorDataDB.KQLDatabase" -q "id" | tr -d '"')

# 3. Create tables with optimized schema
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".create table SensorReadings (timestamp: datetime, deviceId: string, sensorType: string, value: real, unit: string)"
}'

fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".create table DeviceEvents (timestamp: datetime, deviceId: string, eventType: string, details: dynamic)"
}'

# 4. Set retention and caching policies
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".alter-merge table SensorReadings policy retention softdelete = 30d"
}'

fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".alter table SensorReadings policy caching hot = 7d"
}'

# 5. Create Eventstream for ingestion
echo "Creating Eventstream..."
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "IoTDataStream",
  "type": "Eventstream"
}'

# 6. Create Lakehouse for cold storage
echo "Creating Lakehouse for archive..."
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "TelemetryArchive",
  "type": "Lakehouse"
}'

# 7. Create Activator for alerts
echo "Creating alerting..."
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "SensorAlerts",
  "type": "Reflex"
}'

echo "IoT Pipeline infrastructure created!"
echo "Next steps:"
echo "1. Configure IoT Hub connection for Eventstream"
echo "2. Add KQL Database and Lakehouse as Eventstream destinations"
echo "3. Configure Activator alert conditions"
```

### Data Flow

1. **Ingestion**: IoT Hub → Eventstream
2. **Real-time Processing**: Eventstream transforms (filter, enrich)
3. **Hot Storage**: KQL Database (7-day cache, 30-day retention)
4. **Cold Storage**: Lakehouse (historical archive)
5. **Alerting**: Activator monitors thresholds

## Pattern 2: Event-Driven Architecture

### Use Case
Process business events with immediate notifications and analytics.

### Architecture

```bash
#!/bin/bash
# Event-Driven Architecture Setup

WORKSPACE="EventDriven.Workspace"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')

# 1. Domain-specific Eventstreams
DOMAINS=("Orders" "Inventory" "Payments" "Shipping")

for DOMAIN in "${DOMAINS[@]}"; do
  echo "Creating ${DOMAIN}Stream..."
  fab api -X post "workspaces/$WS_ID/items" -i "{
    \"displayName\": \"${DOMAIN}Stream\",
    \"type\": \"Eventstream\"
  }"
done

# 2. Unified Eventhouse
echo "Creating EventHub..."
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "BusinessEventsHub",
  "type": "Eventhouse"
}'

sleep 15
EVENTHOUSE_ID=$(fab get "$WORKSPACE/BusinessEventsHub.Eventhouse" -q "id" | tr -d '"')

# 3. Domain-specific KQL databases
for DOMAIN in "${DOMAINS[@]}"; do
  echo "Creating ${DOMAIN}DB..."
  fab api -X post "workspaces/$WS_ID/items" -i "{
    \"displayName\": \"${DOMAIN}DB\",
    \"type\": \"KQLDatabase\",
    \"properties\": {
      \"parentEventhouseId\": \"$EVENTHOUSE_ID\"
    }
  }"
done

# 4. Create aggregation views
sleep 10
KQL_DB_ID=$(fab get "$WORKSPACE/OrdersDB.KQLDatabase" -q "id" | tr -d '"')

fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".create table Orders (timestamp: datetime, orderId: string, customerId: string, status: string, amount: real)"
}'

# 5. Alerting per domain
for DOMAIN in "${DOMAINS[@]}"; do
  fab api -X post "workspaces/$WS_ID/items" -i "{
    \"displayName\": \"${DOMAIN}Alerts\",
    \"type\": \"Reflex\"
  }"
done

echo "Event-Driven Architecture created!"
```

### Event Flow

1. **Domain Events**: Separate Eventstreams per domain
2. **Event Store**: KQL databases for queryable event history
3. **Event Processing**: Real-time aggregations
4. **Reactions**: Domain-specific Activators for business rules

## Pattern 3: Lambda Architecture

### Use Case
Combine real-time and batch processing for complete analytics.

### Architecture

```bash
#!/bin/bash
# Lambda Architecture Setup

WORKSPACE="Lambda.Workspace"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')

# Speed Layer (Real-time)
echo "Creating Speed Layer..."

# Eventhouse for real-time queries
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "SpeedLayerHub",
  "type": "Eventhouse"
}'

sleep 15
SPEED_EH_ID=$(fab get "$WORKSPACE/SpeedLayerHub.Eventhouse" -q "id" | tr -d '"')

fab api -X post "workspaces/$WS_ID/items" -i "{
  \"displayName\": \"RealtimeDB\",
  \"type\": \"KQLDatabase\",
  \"properties\": {
    \"parentEventhouseId\": \"$SPEED_EH_ID\"
  }
}"

# Eventstream for ingestion
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "IngestionStream",
  "type": "Eventstream"
}'

# Batch Layer (Historical)
echo "Creating Batch Layer..."

# Bronze Lakehouse
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "BronzeLakehouse",
  "type": "Lakehouse"
}'

# Silver Lakehouse
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "SilverLakehouse",
  "type": "Lakehouse"
}'

# Gold Lakehouse
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "GoldLakehouse",
  "type": "Lakehouse"
}'

# Serving Layer
echo "Creating Serving Layer..."

fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "AnalyticsModel",
  "type": "SemanticModel"
}'

echo "Lambda Architecture created!"
echo ""
echo "Architecture:"
echo "┌─────────────────────────────────────────────┐"
echo "│           Data Sources                       │"
echo "└─────────────────┬───────────────────────────┘"
echo "                  │"
echo "         ┌────────┴────────┐"
echo "         ▼                 ▼"
echo "  ┌─────────────┐   ┌──────────────┐"
echo "  │ Speed Layer │   │ Batch Layer  │"
echo "  │  (KQL DB)   │   │ (Lakehouse)  │"
echo "  └──────┬──────┘   └───────┬──────┘"
echo "         │                  │"
echo "         └────────┬─────────┘"
echo "                  ▼"
echo "         ┌──────────────┐"
echo "         │Serving Layer │"
echo "         │(Semantic Mdl)│"
echo "         └──────────────┘"
```

### Data Flow

1. **Speed Layer**: Eventstream → KQL Database (real-time, ~hours retention)
2. **Batch Layer**: Eventstream → Lakehouse (medallion architecture, historical)
3. **Serving Layer**: Combined queries via Semantic Model

## Pattern 4: Stream-to-Lakehouse

### Use Case
Stream data directly to Delta Lake for unified batch and streaming.

### Architecture

```bash
#!/bin/bash
# Stream-to-Lakehouse Pattern

WORKSPACE="StreamLake.Workspace"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')

# 1. Create streaming Lakehouse
echo "Creating streaming Lakehouse..."
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "StreamingLakehouse",
  "type": "Lakehouse"
}'

# 2. Create Eventstream
echo "Creating Eventstream..."
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "LakehouseStream",
  "type": "Eventstream"
}'

# 3. Create Notebook for streaming queries
echo "Creating streaming notebook..."
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "StreamingQueries",
  "type": "Notebook"
}'

echo "Stream-to-Lakehouse infrastructure created!"
echo ""
echo "Configuration steps:"
echo "1. Configure Eventstream source (Event Hub, IoT Hub, etc.)"
echo "2. Add Lakehouse as Eventstream destination"
echo "3. Configure table and partitioning in Lakehouse destination"
echo "4. Use Notebook for streaming DataFrame queries"
```

### Streaming Query Example

```python
# In Notebook: Query streaming table
from pyspark.sql.functions import *

# Read from streaming table
df = spark.readStream \
    .format("delta") \
    .table("StreamingLakehouse.streaming_events")

# Real-time aggregation
agg_df = df \
    .withWatermark("timestamp", "10 minutes") \
    .groupBy(
        window("timestamp", "5 minutes"),
        "eventType"
    ) \
    .count()

# Write to output table
agg_df.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", "Tables/_checkpoints/agg") \
    .toTable("StreamingLakehouse.event_aggregates")
```

## Pattern 5: Real-Time Monitoring

### Use Case
System health monitoring with immediate alerting.

### Architecture

```bash
#!/bin/bash
# Real-Time Monitoring Setup

WORKSPACE="Monitoring.Workspace"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')

# 1. Metrics Eventhouse
echo "Creating Metrics Hub..."
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "MetricsHub",
  "type": "Eventhouse"
}'

sleep 15
EVENTHOUSE_ID=$(fab get "$WORKSPACE/MetricsHub.Eventhouse" -q "id" | tr -d '"')

# 2. Specialized databases
METRIC_TYPES=("Infrastructure" "Application" "Business")

for TYPE in "${METRIC_TYPES[@]}"; do
  fab api -X post "workspaces/$WS_ID/items" -i "{
    \"displayName\": \"${TYPE}MetricsDB\",
    \"type\": \"KQLDatabase\",
    \"properties\": {
      \"parentEventhouseId\": \"$EVENTHOUSE_ID\"
    }
  }"
done

# 3. Ingestion Eventstreams
for TYPE in "${METRIC_TYPES[@]}"; do
  fab api -X post "workspaces/$WS_ID/items" -i "{
    \"displayName\": \"${TYPE}MetricsStream\",
    \"type\": \"Eventstream\"
  }"
done

# 4. Alert Activators
ALERT_TYPES=(
  "CriticalInfrastructure"
  "ApplicationErrors"
  "SLAViolation"
  "SecurityAnomaly"
)

for ALERT in "${ALERT_TYPES[@]}"; do
  fab api -X post "workspaces/$WS_ID/items" -i "{
    \"displayName\": \"${ALERT}Alert\",
    \"type\": \"Reflex\"
  }"
done

# 5. Dashboard Queryset
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "MonitoringDashboardQueries",
  "type": "KQLQueryset"
}'

echo "Monitoring infrastructure created!"
```

### Monitoring Queries

```bash
# Infrastructure health
fab api -X post "workspaces/$WS_ID/items/$INFRA_DB_ID/query" -i '{
  "query": "Metrics | where timestamp > ago(5m) | summarize avgCPU=avg(cpu_percent), avgMemory=avg(memory_percent) by bin(timestamp, 1m), hostName"
}'

# Error rates
fab api -X post "workspaces/$WS_ID/items/$APP_DB_ID/query" -i '{
  "query": "Logs | where timestamp > ago(5m) | summarize errorRate=countif(level==\"ERROR\") * 100.0 / count() by bin(timestamp, 1m)"
}'

# SLA tracking
fab api -X post "workspaces/$WS_ID/items/$BIZ_DB_ID/query" -i '{
  "query": "Transactions | where timestamp > ago(1h) | summarize p99_latency=percentile(latency_ms, 99), success_rate=countif(status==\"success\") * 100.0 / count() by bin(timestamp, 5m)"
}'
```

## Best Practices

### Design Principles

| Principle | Description |
|-----------|-------------|
| Schema design | Design for query patterns, not ingestion |
| Partitioning | Partition by time for efficient querying |
| Retention | Match retention to use case |
| Deduplication | Handle duplicates at ingestion |

### Performance Optimization

- Use appropriate time windows for aggregations
- Enable caching for frequently queried data
- Create materialized views for common aggregations
- Optimize KQL queries for time-series patterns

### Operational Considerations

- Monitor ingestion lag and throughput
- Set up alerts for data freshness
- Implement dead-letter handling
- Plan for schema evolution

## Troubleshooting Common Issues

### Data Latency

```bash
# Check Eventstream lag
fab get "Workspace/MyStream.Eventstream" -q "properties"

# Query ingestion delay in KQL
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "TableName | summarize max(ingestion_time() - timestamp)"
}'
```

### Missing Data

```bash
# Check for ingestion failures
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".show ingestion failures | where FailedOn > ago(1h)"
}'

# Verify source connectivity
fab ls ".connections" -l
```

### Query Performance

```bash
# Analyze slow queries
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".show queries | where StartedOn > ago(1h) | where Duration > 30s | project StartedOn, Duration, Text"
}'

# Check table statistics
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".show table TableName extents | summarize count(), sum(OriginalSize), sum(CompressedSize)"
}'
```
