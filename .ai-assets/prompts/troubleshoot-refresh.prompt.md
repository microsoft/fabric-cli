# Troubleshoot Refresh Failure

Diagnose refresh issues for **${input:itemName}** in workspace **${input:workspaceName}**.

## Step 1: Get Recent Job History

List recent job runs for the item:
```
fab job run-list {workspaceName}.Workspace/{itemName}.{ItemType}
```

## Step 2: Get Failed Job Details

Get details of a specific job run:
```
fab job run-status {workspaceName}.Workspace/{itemName}.{ItemType} --id {jobId}
```

## Step 3: Common Failure Patterns

### Data Source Connectivity
- **Symptoms**: "Cannot connect to data source", timeout errors
- **Check**: Credentials, gateway status, network connectivity
- **Fix**: `fab auth` to refresh credentials, check gateway logs

### Memory/Capacity Issues
- **Symptoms**: "Out of memory", "Capacity throttled"
- **Check**: Workspace capacity utilization
- **Fix**: Scale capacity, optimize model, schedule during off-peak

### Data Source Changes
- **Symptoms**: "Column not found", "Table not found"
- **Check**: Source schema hasn't changed
- **Fix**: Update model schema, re-map columns

### Credential Expiration
- **Symptoms**: "Authentication failed", "Token expired"
- **Check**: Data source credentials
- **Fix**: Update credentials in workspace settings

### Gateway Issues
- **Symptoms**: "Gateway unreachable", "Gateway timeout"
- **Check**: Gateway online status, version
- **Fix**: Restart gateway, update gateway version

## Step 4: Trigger Manual Refresh

After fixing the issue, trigger a new refresh:
```
fab job run {workspaceName}.Workspace/{itemName}.{ItemType}
```

Monitor the job:
```
fab job run-status {workspaceName}.Workspace/{itemName}.{ItemType} --id {newJobId}
```

## Step 5: Verify Success

Confirm the refresh completed by listing job runs:
```
fab job run-list {workspaceName}.Workspace/{itemName}.{ItemType}
```

## Escalation

If issue persists:
1. Check Fabric service health at status.cloud.microsoft
2. Export detailed logs via `fab api` for support ticket
3. Contact workspace administrator for capacity issues
