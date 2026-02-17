# Semantic Model Refresh

This guide shows how to trigger and monitor Power BI semantic model refresh using the Fabric CLI `api` command.

## Run Refresh On Demand

To refresh a semantic model, you can use the `api` command as follows:

```bash
fab api -A powerbi -X post "groups/$WORKSPACE_ID/datasets/$SEMANTIC_MODEL_ID/refreshes"
```

Where `$SEMANTIC_MODEL_ID` and `$WORKSPACE_ID` are set to your semantic model ID and workspace ID respectively.

## Run Refresh With Parameters

You can also provide additional parameters to the refresh job, based on the supported payload documented in [Refresh Dataset In Group](https://learn.microsoft.com/rest/api/power-bi/datasets/refresh-dataset-in-group#request-body), as follows:

```bash
fab api -A powerbi -X post "groups/$WORKSPACE_ID/datasets/$SEMANTIC_MODEL_ID/refreshes" --show_headers -i '{"retryCount":"1","timeout":"00:20:00"}'
```

## Check Refresh Status

You can check the status of a specific refresh operation using the refresh ID. The refresh ID is returned in the `Location` or `RequestId` response headers when you run a refresh.

```bash
fab api -A powerbi -X get "groups/$WORKSPACE_ID/datasets/$SEMANTIC_MODEL_ID/refreshes/$REFRESH_ID"
```

This command uses the [Get Refresh Execution Details In Group](https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/get-refresh-execution-details-in-group) API endpoint.

## End-to-End Example: Run Refresh and Poll for Completion

Replace the following placeholders before running:

- **`{WORKSPACE_ID}`** - Your workspace ID
- **`{SEMANTIC_MODEL_ID}`** - Your semantic model ID
- **`{POLLING_INTERVAL}`** - Polling interval in seconds

=== "PowerShell"
    ```powershell
    # Configuration
    $WorkspaceId = "{WORKSPACE_ID}"
    $SemanticModelId = "{SEMANTIC_MODEL_ID}"
    $PollingInterval = {POLLING_INTERVAL}  # seconds
      
    # Customize the request body according to your needs
    $requestBody = '{\"retryCount\":\"1\"}'
    
    $refreshResponse = fab api -A powerbi -X post "groups/$WorkspaceId/datasets/$SemanticModelId/refreshes" --show_headers -i $requestBody
    
    # Parse the response as JSON and check status code

    $refreshJson = $refreshResponse | ConvertFrom-Json
    $statusCode = $refreshJson.status_code
        
    # Check POST response status (expecting 202 Accepted)
    if ($statusCode -ne 202) {
        exit 1
    }
    
    $pollingEndpoint = $null
    
    # Try to extract Location header first (preferred method)
    if ($refreshJson.headers.Location) {
        $locationUrl = $refreshJson.headers.Location
        if ($locationUrl -match 'https?://[^/]+/v1\.0/myorg/(.+)') {
            $pollingEndpoint = $Matches[1].Trim()
        }
    }
    
    # Fallback to RequestId header if Location not present
    if (-not $pollingEndpoint) {
        if ($refreshJson.headers.RequestId) {
            $refreshId = $refreshJson.headers.RequestId
            $pollingEndpoint = "groups/$WorkspaceId/datasets/$SemanticModelId/refreshes/$refreshId"
        }
    }
    
    if (-not $pollingEndpoint) {
        exit 1
    }
        
    $status = ""
    
    while ($true) {
        Start-Sleep -Seconds $PollingInterval
        
        $statusResponse = fab api -A powerbi $pollingEndpoint --show_headers
        
        $statusResponseJson = $statusResponse | ConvertFrom-Json
        $getStatusCode = $statusResponseJson.status_code
        
        # Check GET response status (expecting 200 or 202)
        if ($getStatusCode -ne 200 -and $getStatusCode -ne 202) {
            Write-Host $statusResponse
        }
        
        $statusJson = $statusResponseJson.text
        
        $status = if ($statusJson.extendedStatus) { $statusJson.extendedStatus } else { $statusJson.status }
        
        Write-Host "  Refresh Status: $status" -ForegroundColor Cyan
        
        # Then handle completion states
        switch -Regex ($status) {
            "^Completed$" {
                exit 0
            }
            "^(Failed|Cancelled|Disabled|TimedOut)$" {
                Write-Host $statusResponse
                exit 1
            }
            "^(NotStarted|InProgress|Unknown)$" {
                # Continue polling
            }
            default {
                Write-Host $statusResponse
                exit 1
            }
        }
    }
    ```

=== "Bash"
    ```bash
    #!/bin/bash
    
    # Configuration
    WORKSPACE_ID="{WORKSPACE_ID}"
    SEMANTIC_MODEL_ID="{SEMANTIC_MODEL_ID}"
    POLLING_INTERVAL={POLLING_INTERVAL}  # seconds
      
    # Customize the request body according to your needs
    REQUEST_BODY='{"retryCount":"1"}'
    
    REFRESH_RESPONSE=$(fab api -A powerbi -X post "groups/$WORKSPACE_ID/datasets/$SEMANTIC_MODEL_ID/refreshes" --show_headers -i "$REQUEST_BODY")
    
    # Parse the response as JSON and check status code

    REFRESH_JSON=$(echo "$REFRESH_RESPONSE" | jq '.')
    STATUS_CODE=$(echo "$REFRESH_JSON" | jq -r '.status_code')
        
    # Check POST response status (expecting 202 Accepted)
    if [ "$STATUS_CODE" != "202" ]; then
        exit 1
    fi
    
    POLLING_ENDPOINT=""
    
    # Try to extract Location header first (preferred method)
    LOCATION=$(echo "$REFRESH_JSON" | jq -r '.headers.Location // empty')
    if [ -n "$LOCATION" ]; then
        POLLING_ENDPOINT=$(echo "$LOCATION" | sed -n 's|.*https\?://[^/]*/v1\.0/myorg/\(.*\)|\1|p' | xargs)
    fi
    
    # Fallback to RequestId header if Location not present
    if [ -z "$POLLING_ENDPOINT" ]; then
        REFRESH_ID=$(echo "$REFRESH_JSON" | jq -r '.headers.RequestId // empty')
        if [ -n "$REFRESH_ID" ]; then
            POLLING_ENDPOINT="groups/$WORKSPACE_ID/datasets/$SEMANTIC_MODEL_ID/refreshes/$REFRESH_ID"
        fi
    fi
    
    if [ -z "$POLLING_ENDPOINT" ]; then
        exit 1
    fi
        
    STATUS=""
    
    while true; do
        sleep "$POLLING_INTERVAL"
        
        STATUS_RESPONSE=$(fab api -A powerbi "$POLLING_ENDPOINT" --show_headers)
        
        STATUS_RESPONSE_JSON=$(echo "$STATUS_RESPONSE" | jq '.')
        GET_STATUS_CODE=$(echo "$STATUS_RESPONSE_JSON" | jq -r '.status_code')
        
        # Check GET response status (expecting 200 or 202)
        if [ "$GET_STATUS_CODE" != "200" ] && [ "$GET_STATUS_CODE" != "202" ]; then
            echo "$STATUS_RESPONSE"
        fi
        
        STATUS_JSON=$(echo "$STATUS_RESPONSE_JSON" | jq -r '.text')
        
        EXTENDED_STATUS=$(echo "$STATUS_JSON" | jq -r '.extendedStatus // empty')
        if [ -n "$EXTENDED_STATUS" ]; then
            STATUS="$EXTENDED_STATUS"
        else
            STATUS=$(echo "$STATUS_JSON" | jq -r '.status')
        fi
        
        echo "  Refresh Status: $STATUS"
        
        # Then handle completion states
        case "$STATUS" in
            "Completed")
                exit 0
                ;;
            "Failed"|"Cancelled"|"Disabled"|"TimedOut")
                echo "$STATUS_RESPONSE"
                exit 1
                ;;
            "NotStarted"|"InProgress"|"Unknown")
                # Continue polling
                ;;
            *)
                echo "$STATUS_RESPONSE"
                exit 1
                ;;
        esac
    done
    ```
