# Refresh Operations

Comprehensive guide for managing semantic model refresh operations using Fabric CLI.

## Basic Refresh

### Get Required IDs

```bash
# Workspace ID
WS_ID=$(fab get "ws.Workspace" -q "id" | tr -d '"')

# Model ID
MODEL_ID=$(fab get "ws.Workspace/Model.SemanticModel" -q "id" | tr -d '"')
```

### Trigger Full Refresh

```bash
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{"type":"Full"}'
```

### Check Refresh Status

```bash
# Latest refresh
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes?\$top=1"

# Refresh history
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes"
```

## Enhanced Refresh

Enhanced refresh provides more control for large models.

### Table-Level Refresh

```bash
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{
  "type": "Full",
  "commitMode": "transactional",
  "objects": [
    {"table": "Sales"},
    {"table": "Products"}
  ]
}'
```

### Partition-Level Refresh

```bash
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{
  "type": "Full",
  "commitMode": "transactional",
  "objects": [
    {"table": "Sales", "partition": "Sales-2024-Q1"},
    {"table": "Sales", "partition": "Sales-2024-Q2"}
  ]
}'
```

### Refresh with Retry

```bash
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{
  "type": "Full",
  "retryCount": 3,
  "maxParallelism": 4
}'
```

### Apply Incremental Refresh Policy

```bash
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{
  "type": "Full",
  "applyRefreshPolicy": true
}'
```

## Refresh Scheduling

### Get Current Schedule

```bash
fab api -A powerbi "datasets/$MODEL_ID/refreshSchedule"
```

### Set Daily Schedule

```bash
fab api -A powerbi "datasets/$MODEL_ID/refreshSchedule" -X patch -i '{
  "enabled": true,
  "days": ["Monday","Tuesday","Wednesday","Thursday","Friday"],
  "times": ["06:00", "18:00"],
  "localTimeZoneId": "UTC"
}'
```

### Set Weekly Schedule

```bash
fab api -A powerbi "datasets/$MODEL_ID/refreshSchedule" -X patch -i '{
  "enabled": true,
  "days": ["Sunday"],
  "times": ["02:00"],
  "localTimeZoneId": "Pacific Standard Time"
}'
```

### Disable Schedule

```bash
fab api -A powerbi "datasets/$MODEL_ID/refreshSchedule" -X patch -i '{
  "enabled": false
}'
```

## Troubleshooting Refresh Failures

### Common Error Patterns

| Error | Cause | Solution |
|-------|-------|----------|
| `InvalidCredentials` | Data source credentials expired | Update credentials in gateway settings |
| `GatewayNotReachable` | Gateway offline | Check gateway server, restart service |
| `DataSourceNotFound` | Connection string changed | Update data source configuration |
| `OutOfMemory` | Model too large | Use incremental refresh, optimize model |
| `Timeout` | Refresh exceeded limit | Use enhanced refresh with smaller batches |
| `QueryTimeout` | Source query too slow | Optimize source queries, add indexes |

### Get Detailed Error Info

```bash
# Get failed refresh details
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes?\$top=10" | \
  jq '.value[] | select(.status == "Failed") | {startTime, endTime, status, serviceExceptionJson}'
```

### Check Data Source Status

```bash
# List bound gateways
fab api -A powerbi "datasets/$MODEL_ID/Default.GetBoundGatewayDatasources"

# Check gateway status
GATEWAY_ID="<gateway-id>"
fab api -A powerbi "gateways/$GATEWAY_ID"
```

### Cancel Running Refresh

```bash
REFRESH_ID="<refresh-request-id>"
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes/$REFRESH_ID" -X delete
```

## Monitoring Patterns

### Script: Monitor Refresh Until Complete

```bash
#!/bin/bash
WS_ID=$1
MODEL_ID=$2

# Trigger refresh
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{"type":"Full"}'

# Poll until complete
while true; do
  STATUS=$(fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes?\$top=1" -q "value[0].status")
  echo "Status: $STATUS"
  
  case $STATUS in
    "Completed") echo "Refresh successful"; exit 0 ;;
    "Failed") echo "Refresh failed"; exit 1 ;;
    "Cancelled") echo "Refresh cancelled"; exit 2 ;;
    *) sleep 30 ;;
  esac
done
```

### Script: Refresh with Notification

```bash
#!/bin/bash
WS_ID=$1
MODEL_ID=$2
EMAIL=$3

fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{"type":"Full"}'

# Wait and check
sleep 300  # Wait 5 minutes
STATUS=$(fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes?\$top=1" -q "value[0].status")

if [ "$STATUS" != "Completed" ]; then
  echo "Refresh status: $STATUS - sending alert"
  # Add notification logic here
fi
```

## Incremental Refresh

For large historical tables, use incremental refresh.

### Prerequisites

1. Model must have `RangeStart` and `RangeEnd` date parameters
2. Source query must filter on date column using these parameters
3. Configure refresh policy in Power BI Desktop before publishing

### How It Works

- Historical partitions: Loaded once, not refreshed
- Rolling window: Configurable period always refreshed
- Current partition: Contains most recent data

### Monitor Partition Creation

```bash
# After first refresh, check partitions were created
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes?\$top=1" -q "value[0]"
```

### Override Incremental Policy (XMLA)

For advanced scenarios, use XMLA endpoint to:
- Refresh specific historical partitions
- Bootstrap large initial loads
- Bypass refresh policy for one-time operations
