# Activator Alerts Reference

Guide to creating and managing Activator (Reflex) alerts in Fabric.

## Understanding Activator

Activator (formerly known as Reflex) provides real-time alerting:

- **Event-driven** — Trigger on data conditions
- **No-code** — Visual alert configuration
- **Actions** — Email, Teams, Power Automate, custom
- **Integration** — Works with Eventstreams, KQL, Power BI

## Creating Activators

### Basic Creation

```bash
WS_ID=$(fab get "Workspace" -q "id" | tr -d '"')

fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "SensorAlerts",
  "type": "Reflex",
  "description": "Real-time sensor anomaly alerts"
}'
```

### Verify Creation

```bash
# List activators
fab ls "Workspace/*.Reflex"

# Get details
fab get "Workspace/SensorAlerts.Reflex"
```

## Managing Activators

### List All Activators

```bash
# In workspace
fab ls "Workspace/*.Reflex" -l

# Across workspaces
fab ls -R "*.Reflex"
```

### Get Activator Properties

```bash
REFLEX_ID=$(fab get "Workspace/SensorAlerts.Reflex" -q "id" | tr -d '"')

# Full details
fab api "workspaces/$WS_ID/items/$REFLEX_ID"

# Get definition
fab api "workspaces/$WS_ID/items/$REFLEX_ID/getDefinition"
```

### Update Activator

```bash
# Update name/description
fab api -X patch "workspaces/$WS_ID/items/$REFLEX_ID" -i '{
  "displayName": "RenamedAlerts",
  "description": "Updated description"
}'
```

### Delete Activator

```bash
fab rm "Workspace/OldAlerts.Reflex"

# Or via API
fab api -X delete "workspaces/$WS_ID/items/$REFLEX_ID"
```

## Alert Configuration Patterns

### Temperature Alert

Configure alert for temperature threshold:

```bash
# 1. Create Activator
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "HighTempAlert",
  "type": "Reflex"
}'

# 2. Configure in UI:
# - Data source: Eventstream or KQL Database
# - Condition: temperature > 100
# - Action: Send email/Teams message
```

### Anomaly Detection Alert

```bash
# 1. Create Activator for anomalies
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "AnomalyDetector",
  "type": "Reflex",
  "description": "Alerts on statistical anomalies"
}'

# 2. Connect to KQL database with anomaly detection query
# 3. Configure threshold for anomaly scores
```

### Error Rate Alert

```bash
# 1. Create Activator
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "ErrorRateAlert",
  "type": "Reflex"
}'

# 2. Connect to Eventstream
# 3. Configure condition: error_rate > 5%
# 4. Set action: Teams channel notification
```

## Data Sources

### Connect to Eventstream

```bash
# Create Activator connected to Eventstream
# 1. Create the Activator
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "StreamAlerts",
  "type": "Reflex"
}'

# 2. In Eventstream, add Activator as destination
EVENTSTREAM_ID=$(fab get "Workspace/MyStream.Eventstream" -q "id" | tr -d '"')
# Add Reflex destination via Eventstream configuration
```

### Connect to KQL Database

```bash
# Activator can query KQL database for conditions
# Configure data source pointing to KQL database
# Set up scheduled query evaluation
```

### Connect to Power BI

```bash
# Activator can monitor Power BI datasets
# Configure connection to semantic model
# Set up measure-based conditions
```

## Action Types

### Email Notification

```bash
# Configure email action
{
  "actions": [{
    "type": "Email",
    "recipients": ["alerts@company.com"],
    "subject": "Alert: {{alertName}}",
    "body": "Value: {{value}}, Threshold: {{threshold}}"
  }]
}
```

### Teams Notification

```bash
# Configure Teams action
{
  "actions": [{
    "type": "Teams",
    "channelId": "<channel-id>",
    "message": "🚨 Alert triggered: {{alertName}}"
  }]
}
```

### Power Automate Flow

```bash
# Trigger Power Automate flow
{
  "actions": [{
    "type": "PowerAutomate",
    "flowId": "<flow-id>",
    "parameters": {
      "alertName": "{{alertName}}",
      "value": "{{value}}"
    }
  }]
}
```

### Custom Webhook

```bash
# Call custom webhook
{
  "actions": [{
    "type": "Webhook",
    "url": "https://api.company.com/alerts",
    "method": "POST",
    "body": {
      "alert": "{{alertName}}",
      "timestamp": "{{timestamp}}",
      "value": "{{value}}"
    }
  }]
}
```

## Automation Scripts

### Complete Alert Pipeline

```bash
#!/bin/bash
# Set up complete alerting infrastructure

WORKSPACE="Monitoring.Workspace"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')

# 1. Create Eventhouse for real-time data
echo "Creating Eventhouse..."
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "MonitoringHub",
  "type": "Eventhouse"
}'

sleep 10
EVENTHOUSE_ID=$(fab get "$WORKSPACE/MonitoringHub.Eventhouse" -q "id" | tr -d '"')

# 2. Create KQL Database
echo "Creating KQL Database..."
fab api -X post "workspaces/$WS_ID/items" -i "{
  \"displayName\": \"AlertsDB\",
  \"type\": \"KQLDatabase\",
  \"properties\": {
    \"parentEventhouseId\": \"$EVENTHOUSE_ID\"
  }
}"

sleep 10

# 3. Create Eventstream
echo "Creating Eventstream..."
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "MonitoringStream",
  "type": "Eventstream"
}'

# 4. Create multiple Activators for different conditions
ALERT_TYPES=("HighTemperature" "ErrorRate" "Latency" "Availability")

for ALERT in "${ALERT_TYPES[@]}"; do
  echo "Creating ${ALERT}Alert..."
  fab api -X post "workspaces/$WS_ID/items" -i "{
    \"displayName\": \"${ALERT}Alert\",
    \"type\": \"Reflex\",
    \"description\": \"Alert for $ALERT conditions\"
  }"
done

echo "Alert infrastructure created. Configure conditions in UI."
```

### Multi-Environment Alerting

```bash
#!/bin/bash
# Deploy alerts across environments

ENVIRONMENTS=("Dev" "Staging" "Prod")
ALERTS=("CriticalErrors" "PerformanceDegraded" "SecurityEvents")

for ENV in "${ENVIRONMENTS[@]}"; do
  WORKSPACE="${ENV}Monitoring.Workspace"
  WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')
  
  echo "Deploying to $ENV..."
  
  for ALERT in "${ALERTS[@]}"; do
    fab api -X post "workspaces/$WS_ID/items" -i "{
      \"displayName\": \"${ALERT}_${ENV}\",
      \"type\": \"Reflex\",
      \"description\": \"$ALERT monitoring for $ENV environment\"
    }"
  done
done

echo "Alerts deployed to all environments"
```

## Monitoring Activators

### Check Alert Status

```bash
# Get Activator state
fab get "Workspace/SensorAlerts.Reflex" -q "properties"

# List all Activators with status
fab ls "Workspace/*.Reflex" -l
```

### View Alert History

```bash
# Alert history is typically viewed in UI
# Or query from connected KQL database if logging enabled
```

### Enable/Disable Alerts

```bash
# Activator enable/disable typically done via UI
# Can export/import definitions for version control

# Export current state
fab export "Workspace/SensorAlerts.Reflex" -d "./backup/"

# To disable: delete and recreate when needed
```

## Best Practices

### Alert Design

| Principle | Description |
|-----------|-------------|
| Specific conditions | Avoid overly broad alerts |
| Actionable | Each alert should prompt action |
| Deduplication | Prevent alert storms |
| Severity levels | Differentiate critical vs warning |
| Clear naming | Descriptive alert names |

### Condition Configuration

- Set realistic thresholds based on historical data
- Use time windows to avoid false positives
- Consider business hours for non-critical alerts
- Test conditions before production deployment

### Action Configuration

- Verify notification channels work
- Set up escalation paths
- Include context in alert messages
- Consider rate limiting for high-volume alerts

### Naming Conventions

| Component | Convention | Example |
|-----------|------------|---------|
| Activator | `<Condition><Severity>Alert` | `HighTempCriticalAlert` |
| Alert groups | `<System>Alerts` | `ProductionAlerts` |

## Integration Patterns

### Eventstream to Activator

```bash
#!/bin/bash
# Set up Eventstream -> Activator flow

WORKSPACE="Alerts.Workspace"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')

# Create Eventstream
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "AlertDataStream",
  "type": "Eventstream"
}'

# Create Activator
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "StreamBasedAlerts",
  "type": "Reflex"
}'

echo "Configure Eventstream to route to Activator in UI"
```

### KQL Query to Activator

```bash
#!/bin/bash
# Set up KQL-based alerting

WORKSPACE="Analytics.Workspace"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')
KQL_DB_ID=$(fab get "$WORKSPACE/AnalyticsDB.KQLDatabase" -q "id" | tr -d '"')

# Create alert query (stored as function)
fab api -X post "workspaces/$WS_ID/items/$KQL_DB_ID/query" -i '{
  "query": ".create function AlertCondition() { Events | where timestamp > ago(5m) | summarize errorCount=countif(eventType==\"error\") | where errorCount > 100 }"
}'

# Create Activator
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "KQLBasedAlert",
  "type": "Reflex"
}'

echo "Configure Activator to use KQL query in UI"
```

## Troubleshooting

### Alerts Not Firing

```bash
# Check Activator exists
fab ls "Workspace/*.Reflex" -l

# Verify data source connection
fab get "Workspace/MyAlert.Reflex" -q "properties"

# Check condition - manually query the data
# to verify condition should be met
```

### Too Many Alerts

```bash
# Review alert conditions
# - Add time windows
# - Increase thresholds
# - Add deduplication logic
# - Consider aggregated alerts
```

### Action Not Executing

```bash
# Verify action configuration
# - Check email addresses
# - Verify Teams channel access
# - Test webhook endpoint manually
# - Check Power Automate flow status
```

### Performance Issues

```bash
# If Activator causing performance issues:
# - Reduce query frequency
# - Optimize underlying KQL queries
# - Consider sampling for high-volume streams
# - Use materialized views for complex conditions
```
