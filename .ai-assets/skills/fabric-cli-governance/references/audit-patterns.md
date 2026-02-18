# Audit Patterns Reference

Guide to auditing and monitoring Fabric activities using the CLI.

## Understanding Fabric Audit

Fabric audit logs capture:
- User activities (view, create, delete, share)
- Admin operations (permission changes, capacity assignment)
- API access and authentication events
- Data access patterns

Audit logs are available through:
- Microsoft Purview Audit
- Office 365 Management API
- Fabric Admin API (limited)

## Querying Activity Events

### Basic Activity Query

```bash
# Get activities for date range
fab api "admin/activityEvents" \
  -P startDateTime=2024-01-01T00:00:00Z,endDateTime=2024-01-02T00:00:00Z
```

### Filter by Activity Type

```bash
# View report activities
fab api "admin/activityEvents" \
  -P startDateTime=2024-01-01T00:00:00Z,endDateTime=2024-01-02T00:00:00Z,activityType=ViewReport

# Export activities
fab api "admin/activityEvents" \
  -P activityType=ExportReport

# Share activities
fab api "admin/activityEvents" \
  -P activityType=ShareReport
```

### Common Activity Types

| Activity Type | Description |
|--------------|-------------|
| `ViewReport` | Report viewed |
| `ExportReport` | Report exported |
| `ShareReport` | Report shared |
| `CreateWorkspace` | Workspace created |
| `DeleteWorkspace` | Workspace deleted |
| `AddWorkspaceUser` | User added to workspace |
| `DeleteWorkspaceUser` | User removed from workspace |
| `RefreshDataset` | Dataset refreshed |
| `GetDatasources` | Data sources queried |

## Workspace Activity Audit

### Audit Workspace Access

```bash
#!/bin/bash
WS_ID=$(fab get "Production.Workspace" -q "id" | tr -d '"')

# Get all activities for workspace
fab api "admin/activityEvents" \
  -P startDateTime=2024-01-01T00:00:00Z,endDateTime=2024-01-31T23:59:59Z \
  -q "value[?workspaceId=='$WS_ID']"
```

### Permission Change Audit

```bash
# Track permission changes
fab api "admin/activityEvents" \
  -P activityType=AddWorkspaceUser

fab api "admin/activityEvents" \
  -P activityType=DeleteWorkspaceUser
```

## User Activity Audit

### Query User Activities

```bash
# Get all activities by specific user
fab api "admin/activityEvents" \
  -P startDateTime=2024-01-01T00:00:00Z,endDateTime=2024-01-31T23:59:59Z \
  -q "value[?userId=='user@company.com']"
```

### Login/Authentication Events

```bash
# Track authentication
fab api "admin/activityEvents" \
  -P activityType=GetWorkspaces
```

## Data Access Audit

### Report View Tracking

```bash
#!/bin/bash
# Track who viewed specific report
REPORT_NAME="SalesReport"

fab api "admin/activityEvents" \
  -P activityType=ViewReport \
  -q "value[?artifactName=='$REPORT_NAME']"
```

### Data Export Tracking

```bash
# Track data exports (potential data exfiltration)
fab api "admin/activityEvents" \
  -P activityType=ExportReport

fab api "admin/activityEvents" \
  -P activityType=ExportArtifact
```

## Automated Audit Reports

### Daily Activity Summary

```bash
#!/bin/bash
# Generate daily activity summary
YESTERDAY=$(date -d "yesterday" +%Y-%m-%dT00:00:00Z)
TODAY=$(date +%Y-%m-%dT00:00:00Z)

echo "=== Fabric Activity Summary ===" > daily-audit.txt
echo "Period: $YESTERDAY to $TODAY" >> daily-audit.txt
echo "" >> daily-audit.txt

# Count by activity type
echo "Activity Counts:" >> daily-audit.txt
fab api "admin/activityEvents" \
  -P startDateTime=$YESTERDAY,endDateTime=$TODAY \
  -q "value | group_by(@, &Activity) | {type: keys(@), count: values(@) | map(&length(@), @)}" >> daily-audit.txt
```

### Weekly Security Audit

```bash
#!/bin/bash
WEEK_AGO=$(date -d "7 days ago" +%Y-%m-%dT00:00:00Z)
NOW=$(date +%Y-%m-%dT23:59:59Z)

echo "=== Weekly Security Audit ===" > security-audit.txt

# Permission changes
echo "Permission Changes:" >> security-audit.txt
fab api "admin/activityEvents" \
  -P startDateTime=$WEEK_AGO,endDateTime=$NOW,activityType=AddWorkspaceUser >> security-audit.txt

# Exports
echo "Data Exports:" >> security-audit.txt
fab api "admin/activityEvents" \
  -P startDateTime=$WEEK_AGO,endDateTime=$NOW,activityType=ExportReport >> security-audit.txt

# Failed authentications
echo "Authentication Issues:" >> security-audit.txt
fab api "admin/activityEvents" \
  -P startDateTime=$WEEK_AGO,endDateTime=$NOW \
  -q "value[?contains(Activity, 'Failed')]" >> security-audit.txt
```

### Compliance Report

```bash
#!/bin/bash
# Generate compliance report for sensitive workspaces
WORKSPACE="Financial-Prod.Workspace"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')
START_DATE="2024-01-01T00:00:00Z"
END_DATE="2024-01-31T23:59:59Z"

echo "Compliance Report: $WORKSPACE" > compliance-report.csv
echo "Date Range: $START_DATE to $END_DATE" >> compliance-report.csv
echo "" >> compliance-report.csv
echo "Timestamp,User,Activity,Artifact" >> compliance-report.csv

fab api "admin/activityEvents" \
  -P startDateTime=$START_DATE,endDateTime=$END_DATE \
  -q "value[?workspaceId=='$WS_ID']" | \
  jq -r '.[] | [.CreationTime, .UserId, .Activity, .ArtifactName] | @csv' >> compliance-report.csv
```

## Real-Time Monitoring

### Alert on Sensitive Operations

```bash
#!/bin/bash
# Monitor for sensitive operations (run periodically)
LAST_HOUR=$(date -d "1 hour ago" +%Y-%m-%dT%H:%M:%SZ)
NOW=$(date +%Y-%m-%dT%H:%M:%SZ)

# Check for bulk exports
EXPORTS=$(fab api "admin/activityEvents" \
  -P startDateTime=$LAST_HOUR,endDateTime=$NOW,activityType=ExportReport \
  -q "value | length")

if [ "$EXPORTS" -gt 10 ]; then
  echo "ALERT: High export activity detected: $EXPORTS exports in last hour"
  # Send alert notification
fi

# Check for permission escalations
ADMIN_ADDS=$(fab api "admin/activityEvents" \
  -P startDateTime=$LAST_HOUR,endDateTime=$NOW,activityType=AddWorkspaceUser \
  -q "value[?contains(AdditionalData, 'Admin')] | length")

if [ "$ADMIN_ADDS" -gt 0 ]; then
  echo "ALERT: Admin permission granted: $ADMIN_ADDS new admins"
fi
```

## Audit Log Retention

### Export Logs for Long-Term Storage

```bash
#!/bin/bash
# Export audit logs to storage
MONTH=$(date +%Y-%m)
START_DATE="${MONTH}-01T00:00:00Z"
END_DATE=$(date -d "${MONTH}-01 +1 month -1 day" +%Y-%m-%dT23:59:59Z)

# Get all activities for month
fab api "admin/activityEvents" \
  -P startDateTime=$START_DATE,endDateTime=$END_DATE \
  -o /archive/audit-logs-$MONTH.json

# Upload to lakehouse for analysis
fab cp /archive/audit-logs-$MONTH.json "Audit.Workspace/AuditLogs.Lakehouse/Files/logs/"
```

## Purview Integration

### Query Purview Audit Logs

For comprehensive audit, use Microsoft Purview:

```bash
# Purview audit logs provide:
# - 90+ days retention
# - Advanced filtering
# - Search across Microsoft 365

# Access via Purview portal or API
# https://compliance.microsoft.com/auditlogsearch
```

## Troubleshooting

### No Activity Events Returned

- Check date range format (ISO 8601 with Z suffix)
- Verify you have Fabric Admin role
- Events may have 15-30 minute delay

### Activity Type Not Found

```bash
# List available activity types
fab api "admin/activityEvents" \
  -P startDateTime=2024-01-01T00:00:00Z,endDateTime=2024-01-02T00:00:00Z \
  -q "value[].Activity | unique(@)"
```

### Rate Limiting

- Audit API has rate limits
- For large queries, paginate with continuation token
- Consider exporting to lakehouse for analysis
