# Exit Codes

The Fabric CLI uses standardized exit codes to communicate command execution status to the shell and automation scripts. These codes follow UNIX conventions and enable reliable scripting and error handling.

## Standard Exit Codes

| Code | Status | Description | When It Occurs |
|------|--------|-------------|----------------|
| `0` | Success | Command completed successfully | Normal successful execution |
| `1` | General Error | Command failed for any reason | Most error conditions, validation failures, API errors |
| `2` | Usage Error | Command was cancelled or misused | Invalid syntax, missing arguments, cancelled operations |
| `4` | Authentication Required | Command requires authentication | User not logged in, expired tokens |

**Usage:** in Scripts

Exit codes are particularly useful for automation and error handling in scripts:

### Bash Examples

``` linenums="1"
# Check if command succeeded
if fab get ws1.Workspace; then
    echo "Workspace found"
else
    echo "Failed to get workspace (exit code: $?)"
fi

# Handle specific exit codes
fab auth status
case $? in
    0) echo "Authenticated successfully" ;;
    4) echo "Authentication required"; fab auth login ;;
    *) echo "Unexpected error" ;;
esac

# Stop script on any error
set -e
fab ls ws1.Workspace
fab cd ws1.Workspace
```

### PowerShell Examples

```powershell linenums="1"
# Check exit code in PowerShell
fab get ws1.Workspace
if ($LASTEXITCODE -eq 0) {
    Write-Host "Success"
} elseif ($LASTEXITCODE -eq 4) {
    Write-Host "Authentication required"
    fab auth login
} else {
    Write-Host "Command failed with exit code: $LASTEXITCODE"
}
```

## Error Handling Strategies

### Graceful Degradation
``` linenums="1"
# Continue execution even if optional commands fail
fab get OptionalItem.Notebook || echo "Optional item not found, continuing..."
```

### Retry Logic
``` linenums="1"
# Retry authentication on failure
for i in {1..3}; do
    if fab auth status; then
        break
    elif [ $? -eq 4 ]; then
        echo "Attempt $i: Re-authenticating..."
        fab auth login
    else
        echo "Authentication check failed"
        exit 1
    fi
done
```

### Conditional Execution
``` linenums="1"
# Only proceed if workspace exists
if fab exists MyWorkspace.Workspace; then
    fab cd MyWorkspace.Workspace
    fab ls -l
else
    echo "Workspace not found, creating..."
    fab mkdir MyWorkspace.Workspace
fi
```

### Integration with CI/CD

Exit codes are essential for CI/CD pipeline integration:

```yaml linenums="1"
# GitHub Actions example
- name: Deploy Fabric Resources
  run: |
    fab auth login -u ${{ secrets.CLIENT_ID }} -p ${{ secrets.CLIENT_SECRET }}
    fab mkdir ProductionWorkspace.Workspace || exit 1
    fab job run DataPipeline.DataPipeline --timeout 3600
```
