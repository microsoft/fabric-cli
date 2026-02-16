# Dataset Refresh Using API Command

This guide shows how to trigger and monitor Power BI semantic model (dataset) refresh using the Fabric CLI `api` command with polling implementation.

## APIs Used

This script demonstrates two Power BI REST API endpoints:

### Refresh Dataset In Group

**[Refresh Dataset In Group](https://learn.microsoft.com/rest/api/power-bi/datasets/refresh-dataset-in-group)** - Triggers an on-demand dataset refresh operation

- Method: `POST`
- Endpoint: `groups/{workspaceId}/datasets/{datasetId}/refreshes`

### Get Refresh Execution Details In Group

**[Get Refresh Execution Details In Group](https://learn.microsoft.com/rest/api/power-bi/datasets/get-refresh-execution-details-in-group)** - Retrieves the status of a specific refresh operation

- Method: `GET`
- Endpoint: `groups/{workspaceId}/datasets/{datasetId}/refreshes/{refreshId}`

The POST response includes a `Location` header containing the polling URL, or a `RequestId` header that can be used to construct the polling endpoint for the GET request.

## Script Examples

This script triggers a dataset refresh, extracts the polling endpoint from the response headers, and continuously polls the refresh status until it completes (successfully or with an error).

Replace the following placeholders before running:

- **`{WORKSPACE_ID}`** - Your workspace ID
- **`{DATASET_ID}`** - Your dataset ID
- **`{POLLING_INTERVAL}`** - Polling interval in seconds

=== "PowerShell"
    ```powershell
    # Configuration
    $WorkspaceId = "{WORKSPACE_ID}"
    $DatasetId = "{DATASET_ID}"
    $PollingInterval = {POLLING_INTERVAL}  # seconds
    
    # Step 1: Trigger refresh with Transactional commit mode
    Write-Host "Triggering dataset refresh..." -ForegroundColor Cyan
    
    # Customize the request body according to your needs
    # See: https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/refresh-dataset-in-group#request-body
    # Note: The -i flag uses nargs="+", so the JSON must be passed as a single quoted string with escaped quotes
    $requestBody = '{\"retryCount\":\"1\",\"timeout\":\"00:20:00\"}'
    
    $refreshResponse = fab api -A powerbi -X post "groups/$WorkspaceId/datasets/$DatasetId/refreshes" --show_headers -i $requestBody
    
    # Parse the response as JSON and check status code
    try {
        $refreshJson = $refreshResponse | ConvertFrom-Json
        $statusCode = $refreshJson.status_code
        
        # Check POST response status (expecting 202 Accepted)
        if ($statusCode -ne 202) {
            Write-Host "Error: Expected status code 202, but received $statusCode" -ForegroundColor Red
            Write-Host "Response:" -ForegroundColor Yellow
            Write-Host $refreshResponse
            exit 1
        }
    } catch {
        Write-Host "Warning: Could not parse response as JSON" -ForegroundColor Yellow
        Write-Host "Response: $refreshResponse" -ForegroundColor Gray
    }
    
    # Step 2: Extract polling URL from Location header or build from RequestId
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
            # Build the polling endpoint manually
            $pollingEndpoint = "groups/$WorkspaceId/datasets/$DatasetId/refreshes/$refreshId"
        }
    }
    
    if (-not $pollingEndpoint) {
        Write-Host "Error: Could not extract polling endpoint from response headers" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Polling endpoint: $pollingEndpoint`n" -ForegroundColor Cyan
    
    # Step 3: Poll for completion
    $status = ""
    
    while ($true) {
        Start-Sleep -Seconds $PollingInterval
        
        # Get refresh status using the polling endpoint
        $statusResponse = fab api -A powerbi $pollingEndpoint --show_headers
        
        # Parse JSON response and check status code
        try {
            $statusResponseJson = $statusResponse | ConvertFrom-Json
            $getStatusCode = $statusResponseJson.status_code
            
            # Check GET response status (expecting 200 or 202)
            if ($getStatusCode -ne 200 -and $getStatusCode -ne 202) {
                Write-Host "  Warning: Expected status code 200 or 202, but received $getStatusCode" -ForegroundColor Yellow
                Write-Host "  Response:" -ForegroundColor Yellow
                Write-Host $statusResponse
            }
            
            # Extract the actual status from the response body (text field is already an object)
            $statusJson = $statusResponseJson.text
            
            # Use extendedStatus if available, otherwise fallback to status
            $status = if ($statusJson.extendedStatus) { $statusJson.extendedStatus } else { $statusJson.status }
            
            # Always print the status first
            Write-Host "  Refresh Status: $status" -ForegroundColor Cyan
            
            # Then handle completion states
            switch -Regex ($status) {
                "^Completed$" {
                    Write-Host "`nRefresh completed successfully" -ForegroundColor Green
                    exit 0
                }
                "^(Failed|Cancelled|Disabled|TimedOut)$" {
                    Write-Host "`nRefresh failed" -ForegroundColor Red
                    Write-Host $statusResponse
                    exit 1
                }
                "^(NotStarted|InProgress|Unknown)$" {
                    # Continue polling
                }
                default {
                    Write-Host "`nUnknown status encountered" -ForegroundColor Magenta
                    Write-Host $statusResponse
                    exit 1
                }
            }
        } catch {
            Write-Host "  Error parsing response: $_" -ForegroundColor Red
            Write-Host "  Raw response: $statusResponse" -ForegroundColor Gray
        }
    }
    ```

=== "Bash"
    ```bash
    #!/bin/bash
    
    # Configuration
    WORKSPACE_ID="{WORKSPACE_ID}"
    DATASET_ID="{DATASET_ID}"
    POLLING_INTERVAL={POLLING_INTERVAL}  # seconds
    
    # Step 1: Trigger refresh with Transactional commit mode
    echo -e "\033[0;36mTriggering dataset refresh...\033[0m"
    
    # Customize the request body according to your needs
    # See: https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/refresh-dataset-in-group#request-body
    REQUEST_BODY='{"retryCount":"1","timeout":"00:20:00"}'
    
    REFRESH_RESPONSE=$(fab api -A powerbi -X post "groups/$WORKSPACE_ID/datasets/$DATASET_ID/refreshes" --show_headers -i "$REQUEST_BODY")
    
    # Parse the response as JSON and check status code
    STATUS_CODE=$(echo "$REFRESH_RESPONSE" | jq -r '.status_code // empty')
    
    # Check POST response status (expecting 202 Accepted)
    if [ "$STATUS_CODE" != "202" ]; then
        echo -e "\033[0;31mError: Expected status code 202, but received $STATUS_CODE\033[0m"
        echo -e "\033[0;33mResponse:\033[0m"
        echo "$REFRESH_RESPONSE"
        exit 1
    fi
    
    # Step 2: Extract polling URL from Location header or build from RequestId
    POLLING_ENDPOINT=""
    
    # Try to extract Location header first (preferred method)
    LOCATION=$(echo "$REFRESH_RESPONSE" | jq -r '.headers.Location // empty')
    if [ -n "$LOCATION" ]; then
        # Extract the endpoint path after /v1.0/myorg/
        POLLING_ENDPOINT=$(echo "$LOCATION" | sed -n 's|.*https\?://[^/]*/v1\.0/myorg/\(.*\)|\1|p' | xargs)
    fi
    
    # Fallback to RequestId header if Location not present
    if [ -z "$POLLING_ENDPOINT" ]; then
        REQUEST_ID=$(echo "$REFRESH_RESPONSE" | jq -r '.headers.RequestId // empty')
        if [ -n "$REQUEST_ID" ]; then
            # Build the polling endpoint manually
            POLLING_ENDPOINT="groups/$WORKSPACE_ID/datasets/$DATASET_ID/refreshes/$REQUEST_ID"
        fi
    fi
    
    if [ -z "$POLLING_ENDPOINT" ]; then
        echo -e "\033[0;31mError: Could not extract polling endpoint from response headers\033[0m"
        exit 1
    fi
    
    echo -e "\033[0;36mPolling endpoint: $POLLING_ENDPOINT\033[0m\n"
    
    # Step 3: Poll for completion
    while true; do
        sleep "$POLLING_INTERVAL"
        
        # Get refresh status using the polling endpoint
        STATUS_RESPONSE=$(fab api -A powerbi "$POLLING_ENDPOINT" --show_headers)
        
        # Parse JSON response and check status code
        GET_STATUS_CODE=$(echo "$STATUS_RESPONSE" | jq -r '.status_code // empty')
        
        # Check GET response status (expecting 200 or 202)
        if [ "$GET_STATUS_CODE" != "200" ] && [ "$GET_STATUS_CODE" != "202" ]; then
            echo -e "  \033[0;33mWarning: Expected status code 200 or 202, but received $GET_STATUS_CODE\033[0m"
            echo -e "  \033[0;33mResponse:\033[0m"
            echo "$STATUS_RESPONSE"
        fi
        
        # Extract the actual status from the response body
        # Use extendedStatus if available, otherwise fallback to status
        EXTENDED_STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.text.extendedStatus // empty')
        if [ -n "$EXTENDED_STATUS" ]; then
            STATUS="$EXTENDED_STATUS"
        else
            STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.text.status // empty')
        fi
        
        # Always print the status first
        echo -e "  \033[0;36mRefresh Status: $STATUS\033[0m"
        
        # Then handle completion states
        case "$STATUS" in
            "Completed")
                echo -e "\n\033[0;32mRefresh completed successfully\033[0m"
                exit 0
                ;;
            "Failed"|"Cancelled"|"Disabled"|"TimedOut")
                echo -e "\n\033[0;31mRefresh failed\033[0m"
                echo "$STATUS_RESPONSE"
                exit 1
                ;;
            "NotStarted"|"InProgress"|"Unknown")
                # Continue polling
                ;;
            *)
                echo -e "\n\033[0;35mUnknown status encountered\033[0m"
                echo "$STATUS_RESPONSE"
                exit 1
                ;;
        esac
    done
    ```
