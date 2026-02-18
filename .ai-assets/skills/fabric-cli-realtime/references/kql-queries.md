# KQL Queries Reference

Guide to executing KQL queries using Fabric CLI.

## KQL Query Fundamentals

Kusto Query Language (KQL) is optimized for log and time-series data:

- **Read-optimized** — Fast analytical queries
- **Pipe syntax** — Chain operators sequentially
- **Built-in functions** — Time-series, ML, geospatial
- **Real-time** — Sub-second query response

## Executing Queries via CLI

### Basic Query Execution

```bash
WS_ID=$(fab get "Workspace" -q "id" | tr -d '"')
KQL_DB_ID=$(fab get "Workspace/MyDatabase.KQLDatabase" -q "id" | tr -d '"')

# Simple query
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "SensorReadings | take 10"
}'
```

### Query with JMESPath Filter

```bash
# Extract specific columns from results
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "SensorReadings | take 10"
}' -q "results[].{device: deviceId, temp: temperature}"
```

### Query with Timeout

```bash
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "LargeTable | summarize count() by bin(timestamp, 1h)",
  "requestProperties": {
    "queryTimeout": "PT5M"
  }
}'
```

## Common Query Patterns

### Time-Based Filtering

```bash
# Events from last hour
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "Events | where timestamp > ago(1h)"
}'

# Events in time range
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "Events | where timestamp between (datetime(2024-01-01) .. datetime(2024-01-31))"
}'

# Events from specific date
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "Events | where timestamp > startofday(now())"
}'
```

### Aggregations

```bash
# Count by time bucket
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "Events | summarize count() by bin(timestamp, 5m)"
}'

# Statistics by group
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "SensorReadings | summarize avg(temperature), max(temperature), min(temperature) by deviceId"
}'

# Top N
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "Events | summarize count() by eventType | top 10 by count_"
}'
```

### Filtering and Projection

```bash
# Filter with multiple conditions
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "SensorReadings | where temperature > 100 and deviceId startswith \"sensor-\" | project timestamp, deviceId, temperature"
}'

# Text search
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "Logs | where message contains \"error\" | take 100"
}'

# Regex matching
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "Logs | where message matches regex \"Error: [A-Z]{3}[0-9]{4}\""
}'
```

### Joins

```bash
# Inner join
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "Events | join kind=inner (Devices | project deviceId, deviceName) on deviceId"
}'

# Left outer join
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "Events | join kind=leftouter (Alerts | where severity == \"High\") on deviceId"
}'
```

### Time Series Analysis

```bash
# Moving average
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "SensorReadings | make-series avgTemp=avg(temperature) on timestamp step 5m | extend movingAvg=series_fir(avgTemp, repeat(1, 3))"
}'

# Anomaly detection
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "SensorReadings | make-series avgTemp=avg(temperature) on timestamp step 5m | extend anomalies=series_decompose_anomalies(avgTemp)"
}'

# Forecasting
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "SensorReadings | make-series avgTemp=avg(temperature) on timestamp step 1h | extend forecast=series_decompose_forecast(avgTemp, 24)"
}'
```

## Management Commands

### Show Tables

```bash
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".show tables"
}'
```

### Show Table Schema

```bash
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".show table SensorReadings schema"
}'

# Columns only
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "SensorReadings | getschema"
}'
```

### Show Table Statistics

```bash
# Row count and size
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".show table SensorReadings details"
}'

# Data statistics
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "SensorReadings | summarize count(), min(timestamp), max(timestamp), dcount(deviceId)"
}'
```

### Show Policies

```bash
# Retention policy
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".show table SensorReadings policy retention"
}'

# Caching policy
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".show table SensorReadings policy caching"
}'

# All policies
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".show table SensorReadings policies"
}'
```

## Query Automation

### Scheduled Query Script

```bash
#!/bin/bash
# Run daily analytics query and export results

WORKSPACE="Analytics.Workspace"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')
KQL_DB_ID=$(fab get "$WORKSPACE/AnalyticsDB.KQLDatabase" -q "id" | tr -d '"')

# Daily summary query
QUERY='
Events 
| where timestamp > ago(1d) 
| summarize 
    totalEvents=count(), 
    uniqueDevices=dcount(deviceId),
    errorCount=countif(eventType == "error")
  by bin(timestamp, 1h)
| order by timestamp asc
'

# Execute and save results
RESULTS=$(fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i "{
  \"query\": \"$QUERY\"
}")

echo "$RESULTS" > daily_summary_$(date +%Y%m%d).json
echo "Daily summary exported"
```

### Alert Query Script

```bash
#!/bin/bash
# Check for anomalies and alert

WORKSPACE="Monitoring.Workspace"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')
KQL_DB_ID=$(fab get "$WORKSPACE/MonitoringDB.KQLDatabase" -q "id" | tr -d '"')

# Check for high error rate
ERRORS=$(fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "Events | where timestamp > ago(5m) | summarize errorRate=countif(eventType==\"error\") * 100.0 / count()"
}' -q "results[0].errorRate")

if (( $(echo "$ERRORS > 10" | bc -l) )); then
  echo "ALERT: Error rate is $ERRORS%"
  # Send notification...
fi
```

### Batch Query Runner

```bash
#!/bin/bash
# Run multiple queries and compile report

WORKSPACE="Reports.Workspace"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')
KQL_DB_ID=$(fab get "$WORKSPACE/ReportsDB.KQLDatabase" -q "id" | tr -d '"')

QUERIES=(
  "Events | where timestamp > ago(1d) | count"
  "Events | where timestamp > ago(1d) | summarize count() by eventType"
  "SensorReadings | where timestamp > ago(1d) | summarize avg(temperature) by deviceId"
)

for i in "${!QUERIES[@]}"; do
  echo "Running query $((i+1))..."
  fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i "{
    \"query\": \"${QUERIES[$i]}\"
  }" > "query_${i}_results.json"
done

echo "All queries completed"
```

## KQL Querysets

### Create KQL Queryset

```bash
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "AnalyticsQueries",
  "type": "KQLQueryset"
}'
```

### List Querysets

```bash
fab ls "Workspace/*.KQLQueryset"
```

### Export Queryset

```bash
fab export "Workspace/AnalyticsQueries.KQLQueryset" -d "./exports/"
```

### Import Queryset

```bash
fab import -p "Workspace" -d "./querysets/analytics.json" -t KQLQueryset
```

## Performance Optimization

### Query Best Practices

```kql
// Use time filters early
Events
| where timestamp > ago(1h)  // Filter first
| where eventType == "error"
| summarize count() by deviceId

// Avoid wildcards at start
Events
| where message startswith "Error"  // Good
// | where message contains "Error"  // Less efficient

// Project only needed columns
Events
| project timestamp, deviceId, eventType  // Early projection
| where eventType == "error"
```

### Materialized Views

```bash
# Create materialized view for common aggregations
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".create materialized-view HourlySummary on table Events { Events | summarize count() by bin(timestamp, 1h), eventType }"
}'

# Query materialized view
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "HourlySummary | where timestamp > ago(7d)"
}'
```

### Functions

```bash
# Create stored function
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".create function GetRecentErrors(hours: int = 1) { Events | where timestamp > ago(hours * 1h) | where eventType == \"error\" }"
}'

# Call function
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "GetRecentErrors(24)"
}'
```

## Troubleshooting

### Query Timeout

```bash
# Increase timeout
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "LargeQuery...",
  "requestProperties": {
    "queryTimeout": "PT10M"
  }
}'

# Simplify query - add early filters
# Use summarize to reduce data volume
```

### No Results

```bash
# Check table has data
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "TableName | count"
}'

# Check time range
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "TableName | summarize min(timestamp), max(timestamp)"
}'

# Verify column names
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": "TableName | getschema"
}'
```

### Permission Errors

```bash
# Verify database access
fab acl get "Workspace/MyDatabase.KQLDatabase"

# Check workspace role
fab acl get "Workspace"
```
