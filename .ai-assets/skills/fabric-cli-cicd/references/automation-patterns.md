# Automation Patterns for Fabric CLI

Scripts, error handling, and scheduling patterns for automating Fabric operations.

## Shell Script Templates

### Bash Template with Error Handling

```bash
#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
WORKSPACE="${TARGET_WORKSPACE:-Dev.Workspace}"
LOG_FILE="./fabric-deploy-$(date +%Y%m%d_%H%M%S).log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Error handler
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Cleanup on exit
cleanup() {
    log "Cleaning up temporary files..."
    rm -rf ./temp-export/ 2>/dev/null || true
}
trap cleanup EXIT

# Main script
main() {
    log "Starting deployment to $WORKSPACE"
    
    # Verify authentication
    fab auth status || error_exit "Not authenticated. Run 'fab auth login' first."
    
    # Verify workspace exists
    fab exists "$WORKSPACE" || error_exit "Workspace $WORKSPACE not found"
    
    # Deploy items
    log "Deploying items..."
    fab import "$WORKSPACE/Pipeline.DataPipeline" -i ./fabric-items/Pipeline.DataPipeline -f \
        || error_exit "Failed to deploy Pipeline"
    
    log "Deployment complete"
}

main "$@"
```

### PowerShell Template

```powershell
#Requires -Version 7.0
$ErrorActionPreference = "Stop"

# Configuration
$Workspace = $env:TARGET_WORKSPACE ?? "Dev.Workspace"
$LogFile = "./fabric-deploy-$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$timestamp] $Message" | Tee-Object -FilePath $LogFile -Append
}

function Test-FabAuth {
    $result = fab auth status 2>&1
    return $LASTEXITCODE -eq 0
}

try {
    Write-Log "Starting deployment to $Workspace"
    
    # Verify authentication
    if (-not (Test-FabAuth)) {
        throw "Not authenticated. Run 'fab auth login' first."
    }
    
    # Verify workspace
    $exists = fab exists $Workspace
    if ($exists -notmatch "true") {
        throw "Workspace $Workspace not found"
    }
    
    # Deploy items
    Write-Log "Deploying items..."
    fab import "$Workspace/Pipeline.DataPipeline" -i ./fabric-items/Pipeline.DataPipeline -f
    if ($LASTEXITCODE -ne 0) { throw "Failed to deploy Pipeline" }
    
    Write-Log "Deployment complete"
}
catch {
    Write-Log "ERROR: $_"
    exit 1
}
finally {
    # Cleanup
    Remove-Item -Path ./temp-export -Recurse -Force -ErrorAction SilentlyContinue
}
```

## Error Handling Patterns

### Retry Logic (Bash)

```bash
#!/bin/bash

# Retry function with exponential backoff
retry() {
    local max_attempts=$1
    local delay=$2
    local command="${@:3}"
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt of $max_attempts: $command"
        
        if eval "$command"; then
            return 0
        fi
        
        if [ $attempt -lt $max_attempts ]; then
            echo "Failed. Retrying in ${delay}s..."
            sleep $delay
            delay=$((delay * 2))  # Exponential backoff
        fi
        
        attempt=$((attempt + 1))
    done
    
    echo "All $max_attempts attempts failed"
    return 1
}

# Usage
retry 3 5 fab import "Prod.Workspace/Item.Type" -i ./Item.Type -f
```

### Retry Logic (PowerShell)

```powershell
function Invoke-WithRetry {
    param(
        [scriptblock]$ScriptBlock,
        [int]$MaxAttempts = 3,
        [int]$DelaySeconds = 5
    )
    
    $attempt = 1
    while ($attempt -le $MaxAttempts) {
        try {
            Write-Host "Attempt $attempt of $MaxAttempts"
            & $ScriptBlock
            return
        }
        catch {
            if ($attempt -eq $MaxAttempts) {
                throw "All $MaxAttempts attempts failed: $_"
            }
            Write-Host "Failed. Retrying in ${DelaySeconds}s..."
            Start-Sleep -Seconds $DelaySeconds
            $DelaySeconds *= 2  # Exponential backoff
            $attempt++
        }
    }
}

# Usage
Invoke-WithRetry -ScriptBlock {
    fab import "Prod.Workspace/Item.Type" -i ./Item.Type -f
    if ($LASTEXITCODE -ne 0) { throw "Import failed" }
}
```

### Graceful Degradation

```bash
#!/bin/bash

# Deploy multiple items, continue on failure
ITEMS=(
    "Pipeline1.DataPipeline"
    "Pipeline2.DataPipeline"
    "Notebook1.Notebook"
)

FAILED=()
SUCCEEDED=()

for ITEM in "${ITEMS[@]}"; do
    echo "Deploying $ITEM..."
    if fab import "$WORKSPACE/$ITEM" -i "./fabric-items/$ITEM" -f; then
        SUCCEEDED+=("$ITEM")
    else
        echo "WARNING: Failed to deploy $ITEM"
        FAILED+=("$ITEM")
    fi
done

# Report
echo ""
echo "=== Deployment Summary ==="
echo "Succeeded: ${#SUCCEEDED[@]}"
echo "Failed: ${#FAILED[@]}"

if [ ${#FAILED[@]} -gt 0 ]; then
    echo ""
    echo "Failed items:"
    printf '  - %s\n' "${FAILED[@]}"
    exit 1
fi
```

## Scheduling Patterns

### Cron Schedule Reference

```bash
# ┌───────────── minute (0-59)
# │ ┌───────────── hour (0-23)
# │ │ ┌───────────── day of month (1-31)
# │ │ │ ┌───────────── month (1-12)
# │ │ │ │ ┌───────────── day of week (0-6, Sunday=0)
# │ │ │ │ │
# * * * * *

# Examples:
# 0 6 * * *     Daily at 6 AM
# 0 */4 * * *   Every 4 hours
# 0 9 * * 1-5   Weekdays at 9 AM
# 0 0 1 * *     First of month at midnight
```

### Scheduled Refresh Script

```bash
#!/bin/bash
# refresh-models.sh - Run as cron job

LOG_DIR="/var/log/fabric"
LOG_FILE="$LOG_DIR/refresh-$(date +%Y%m%d).log"
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# Authenticate (using stored credentials)
export FAB_SPN_TENANT_ID="$FABRIC_TENANT_ID"
export FAB_SPN_CLIENT_ID="$FABRIC_CLIENT_ID"
export FAB_SPN_CLIENT_SECRET="$FABRIC_CLIENT_SECRET"

fab auth login --service-principal >> "$LOG_FILE" 2>&1

# Get IDs
WS_ID=$(fab get "Prod.Workspace" -q "id" | tr -d '"')
MODEL_ID=$(fab get "Prod.Workspace/Sales.SemanticModel" -q "id" | tr -d '"')

# Trigger refresh
log "Triggering refresh for Sales model"
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post \
    -i '{"type":"Full"}' >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log "Refresh triggered successfully"
else
    log "ERROR: Failed to trigger refresh"
    exit 1
fi
```

### Windows Task Scheduler Script

```powershell
# refresh-models.ps1
# Schedule with: schtasks /create /tn "FabricRefresh" /tr "powershell.exe -File C:\scripts\refresh-models.ps1" /sc daily /st 06:00

$LogPath = "C:\Logs\Fabric"
$LogFile = Join-Path $LogPath "refresh-$(Get-Date -Format 'yyyyMMdd').log"
New-Item -ItemType Directory -Path $LogPath -Force | Out-Null

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$timestamp] $Message" | Add-Content -Path $LogFile
}

# Set credentials from secure storage
$env:FAB_SPN_TENANT_ID = Get-Secret -Name FabricTenantId -AsPlainText
$env:FAB_SPN_CLIENT_ID = Get-Secret -Name FabricClientId -AsPlainText
$env:FAB_SPN_CLIENT_SECRET = Get-Secret -Name FabricClientSecret -AsPlainText

fab auth login --service-principal

# Trigger refresh
Write-Log "Triggering model refresh"
$wsId = (fab get "Prod.Workspace" -q "id") -replace '"', ''
$modelId = (fab get "Prod.Workspace/Sales.SemanticModel" -q "id") -replace '"', ''

fab api -A powerbi "groups/$wsId/datasets/$modelId/refreshes" -X post -i '{"type":"Full"}'

if ($LASTEXITCODE -eq 0) {
    Write-Log "Refresh triggered successfully"
} else {
    Write-Log "ERROR: Failed to trigger refresh"
    exit 1
}
```

## Parallel Execution

### Bash Parallel Deployment

```bash
#!/bin/bash
# parallel-deploy.sh

WORKSPACE="Prod.Workspace"
MAX_PARALLEL=4

# Deploy function
deploy_item() {
    local item=$1
    echo "Deploying $item..."
    fab import "$WORKSPACE/$item" -i "./fabric-items/$item" -f
    echo "Completed $item"
}

export -f deploy_item
export WORKSPACE

# Find all items and deploy in parallel
find ./fabric-items -maxdepth 1 -type d -name "*.DataPipeline" -o -name "*.Notebook" | \
    xargs -P $MAX_PARALLEL -I {} basename {} | \
    xargs -P $MAX_PARALLEL -I {} bash -c 'deploy_item "$@"' _ {}
```

### PowerShell Parallel Deployment

```powershell
$Workspace = "Prod.Workspace"
$Items = Get-ChildItem ./fabric-items -Directory | Select-Object -ExpandProperty Name

$Items | ForEach-Object -ThrottleLimit 4 -Parallel {
    $item = $_
    $ws = $using:Workspace
    Write-Host "Deploying $item..."
    fab import "$ws/$item" -i "./fabric-items/$item" -f
    Write-Host "Completed $item"
}
```

## Monitoring and Alerting

### Check Job Status Script

```bash
#!/bin/bash
# monitor-jobs.sh

WORKSPACE="Prod.Workspace"
NOTEBOOK="ETL.Notebook"
MAX_WAIT=3600  # 1 hour
CHECK_INTERVAL=30

# Start job
JOB_OUTPUT=$(fab job start "$WORKSPACE/$NOTEBOOK")
JOB_ID=$(echo "$JOB_OUTPUT" | grep -oP 'id["\s:]+\K[a-f0-9-]+')

echo "Started job: $JOB_ID"

# Monitor until complete or timeout
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    STATUS=$(fab job run-status "$WORKSPACE/$NOTEBOOK" --id "$JOB_ID" -q "status" | tr -d '"')
    
    case "$STATUS" in
        "Completed")
            echo "Job completed successfully"
            exit 0
            ;;
        "Failed"|"Cancelled")
            echo "Job $STATUS"
            # Send alert
            curl -X POST "$SLACK_WEBHOOK" -d "{\"text\":\"Fabric job failed: $NOTEBOOK\"}"
            exit 1
            ;;
        *)
            echo "Status: $STATUS (${ELAPSED}s elapsed)"
            ;;
    esac
    
    sleep $CHECK_INTERVAL
    ELAPSED=$((ELAPSED + CHECK_INTERVAL))
done

echo "Timeout waiting for job"
exit 1
```

### Health Check Script

```bash
#!/bin/bash
# health-check.sh

WORKSPACE="Prod.Workspace"
ITEMS_TO_CHECK=(
    "Sales.SemanticModel"
    "ETL.DataPipeline"
    "Transform.Notebook"
)

HEALTHY=0
UNHEALTHY=0

echo "=== Fabric Health Check ==="
echo "Workspace: $WORKSPACE"
echo ""

# Check auth
if fab auth status >/dev/null 2>&1; then
    echo "[OK] Authentication: OK"
else
    echo "[FAILED] Authentication: FAILED"
    exit 1
fi

# Check workspace
if fab exists "$WORKSPACE" >/dev/null 2>&1; then
    echo "[OK] Workspace: Accessible"
else
    echo "[FAILED] Workspace: Not accessible"
    exit 1
fi

# Check items
echo ""
echo "Items:"
for ITEM in "${ITEMS_TO_CHECK[@]}"; do
    if fab exists "$WORKSPACE/$ITEM" >/dev/null 2>&1; then
        echo "  [OK] $ITEM"
        HEALTHY=$((HEALTHY + 1))
    else
        echo "  [FAILED] $ITEM (not found)"
        UNHEALTHY=$((UNHEALTHY + 1))
    fi
done

echo ""
echo "Summary: $HEALTHY healthy, $UNHEALTHY unhealthy"

[ $UNHEALTHY -eq 0 ] && exit 0 || exit 1
```

## Environment Variable Management

### Using .env Files

```bash
#!/bin/bash
# Load environment-specific config

ENV=${1:-dev}
ENV_FILE="./config/$ENV.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found"
    exit 1
fi

# Load variables (without export for security)
set -a
source "$ENV_FILE"
set +a

echo "Loaded config for: $ENV"
echo "Target workspace: $TARGET_WORKSPACE"
```

### Secure Credential Handling

```bash
#!/bin/bash
# Never echo credentials, use env vars

# Bad - exposes secrets in logs
# echo "Using secret: $FAB_SPN_CLIENT_SECRET"

# Good - validate without exposing
if [ -z "$FAB_SPN_CLIENT_SECRET" ]; then
    echo "Error: FAB_SPN_CLIENT_SECRET not set"
    exit 1
fi
echo "Credentials configured"

# Good - mask in CI logs
echo "::add-mask::$FAB_SPN_CLIENT_SECRET"
```

## Best Practices Summary

| Practice | Description |
|----------|-------------|
| Use `set -euo pipefail` | Exit on errors in bash scripts |
| Implement retry logic | Handle transient failures |
| Log everything | Timestamp and persist logs |
| Use cleanup traps | Clean temp files on exit |
| Validate before acting | Check auth and existence first |
| Parameterize scripts | Use env vars for flexibility |
| Never log secrets | Mask sensitive values |
| Monitor long-running jobs | Set timeouts, send alerts |
