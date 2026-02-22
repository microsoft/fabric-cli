# Gateway Operations

Manage on-premises data gateways and data sources using Fabric CLI.

## List Gateways

Gateways are tenant-level hidden entities.

```bash
# List all gateways (requires admin or gateway permissions)
fab ls .gateways

# List with details
fab ls .gateways -v
```

## Get Gateway Info

```bash
# Get gateway by name
fab get ".gateways/MyGateway.Gateway"

# Get gateway ID
GATEWAY_ID=$(fab get ".gateways/MyGateway.Gateway" -q "id" | tr -d '"')

# Get gateway via API
fab api -A powerbi "gateways/$GATEWAY_ID"
```

## Gateway Cluster Status

```bash
# Check gateway cluster members
fab api -A powerbi "gateways/$GATEWAY_ID" -q "gatewayAnnotation"

# Parse status
fab api -A powerbi "gateways/$GATEWAY_ID" | jq '.gatewayStatus'
```

## Data Sources

### List Data Sources on Gateway

```bash
fab api -A powerbi "gateways/$GATEWAY_ID/datasources"
```

### Get Data Source Details

```bash
DATASOURCE_ID="<datasource-id>"
fab api -A powerbi "gateways/$GATEWAY_ID/datasources/$DATASOURCE_ID"
```

### Create Data Source

```bash
# SQL Server example
fab api -A powerbi "gateways/$GATEWAY_ID/datasources" -X post -i '{
  "dataSourceType": "Sql",
  "connectionDetails": "{\"server\":\"myserver.database.windows.net\",\"database\":\"mydb\"}",
  "datasourceName": "MyDatabase",
  "credentialDetails": {
    "credentialType": "Basic",
    "credentials": "{\"credentialData\":[{\"name\":\"username\",\"value\":\"user\"},{\"name\":\"password\",\"value\":\"pass\"}]}",
    "encryptedConnection": "Encrypted",
    "encryptionAlgorithm": "None",
    "privacyLevel": "Organizational"
  }
}'
```

### Update Data Source Credentials

```bash
# Update with basic auth
fab api -A powerbi "gateways/$GATEWAY_ID/datasources/$DATASOURCE_ID" -X patch -i '{
  "credentialDetails": {
    "credentialType": "Basic",
    "credentials": "{\"credentialData\":[{\"name\":\"username\",\"value\":\"newuser\"},{\"name\":\"password\",\"value\":\"newpass\"}]}",
    "encryptedConnection": "Encrypted",
    "encryptionAlgorithm": "None",
    "privacyLevel": "Organizational"
  }
}'

# Update with OAuth2
fab api -A powerbi "gateways/$GATEWAY_ID/datasources/$DATASOURCE_ID" -X patch -i '{
  "credentialDetails": {
    "credentialType": "OAuth2",
    "credentials": "{\"credentialData\":[{\"name\":\"accessToken\",\"value\":\"<token>\"}]}",
    "encryptedConnection": "Encrypted",
    "encryptionAlgorithm": "None",
    "privacyLevel": "Organizational"
  }
}'
```

### Delete Data Source

```bash
fab api -A powerbi "gateways/$GATEWAY_ID/datasources/$DATASOURCE_ID" -X delete
```

## Semantic Model Data Sources

### Get Bound Data Sources

```bash
MODEL_ID=$(fab get "ws.Workspace/Model.SemanticModel" -q "id" | tr -d '"')

# Get data sources bound to model
fab api -A powerbi "datasets/$MODEL_ID/Default.GetBoundGatewayDatasources"
```

### Bind to Gateway

```bash
WS_ID=$(fab get "ws.Workspace" -q "id" | tr -d '"')

fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/Default.BindToGateway" -X post -i '{
  "gatewayObjectId": "<gateway-id>",
  "datasourceObjectIds": ["<datasource-id-1>", "<datasource-id-2>"]
}'
```

### Take Over Data Source

When original owner leaves:

```bash
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/Default.TakeOver" -X post
```

## Gateway Users

### List Gateway Users

```bash
fab api -A powerbi "gateways/$GATEWAY_ID/users"
```

### Add Gateway User

```bash
fab api -A powerbi "gateways/$GATEWAY_ID/users" -X post -i '{
  "emailAddress": "user@contoso.com",
  "datasourceAccessRight": "Read"
}'
```

### Remove Gateway User

```bash
fab api -A powerbi "gateways/$GATEWAY_ID/users/$USER_ID" -X delete
```

## Troubleshooting

### Gateway Not Reachable

1. Check gateway service is running on gateway machine
2. Verify network connectivity
3. Check firewall rules
4. Review gateway logs

### Data Source Connection Failed

1. Test connection string manually
2. Verify credentials are current
3. Check if source database is accessible from gateway machine
4. Review gateway data source configuration

### Gateway Commands Summary

| Operation | Command |
|-----------|---------|
| List gateways | `fab ls .gateways` |
| Get gateway | `fab api -A powerbi "gateways/$GW_ID"` |
| List data sources | `fab api -A powerbi "gateways/$GW_ID/datasources"` |
| Update credentials | `fab api -A powerbi "gateways/$GW_ID/datasources/$DS_ID" -X patch -i '...'` |
| Bind model to gateway | `fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/Default.BindToGateway" -X post -i '...'` |
