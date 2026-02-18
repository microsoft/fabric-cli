# Shortcuts Reference

Guide to creating and managing OneLake shortcuts for data federation.

## Understanding Shortcuts

Shortcuts provide virtualized access to data without copying:

- **Zero data movement** — Reference data in place
- **Real-time access** — Always see current data
- **Cross-cloud** — Connect ADLS, S3, GCS
- **Cross-workspace** — Share data across Fabric

## Shortcut Types

| Source | Type | Use Case |
|--------|------|----------|
| OneLake | Internal | Cross-workspace sharing |
| ADLS Gen2 | External | Azure Data Lake integration |
| Amazon S3 | External | AWS data federation |
| Google Cloud Storage | External | GCP data federation |
| Dataverse | External | Power Platform data |
| On-premises | Via Gateway | Legacy systems |

## Creating Shortcuts

### OneLake Shortcut (CLI)

```bash
# Create shortcut to another lakehouse table
fab ln "Source.Workspace/SourceLH.Lakehouse/Tables/customers" \
       "Target.Workspace/TargetLH.Lakehouse/Tables/customers_ref"

# Create shortcut to files
fab ln "Source.Workspace/SourceLH.Lakehouse/Files/data" \
       "Target.Workspace/TargetLH.Lakehouse/Files/external_data"
```

### OneLake Shortcut (API)

```bash
WS_ID=$(fab get "Target.Workspace" -q "id" | tr -d '"')
LH_ID=$(fab get "Target.Workspace/Target.Lakehouse" -q "id" | tr -d '"')

# Get source IDs
SOURCE_WS_ID=$(fab get "Source.Workspace" -q "id" | tr -d '"')
SOURCE_LH_ID=$(fab get "Source.Workspace/Source.Lakehouse" -q "id" | tr -d '"')

fab api -X post "workspaces/$WS_ID/items/$LH_ID/shortcuts" -i "{
  \"name\": \"customer_data\",
  \"path\": \"Tables/customer_data\",
  \"target\": {
    \"type\": \"OneLake\",
    \"oneLake\": {
      \"workspaceId\": \"$SOURCE_WS_ID\",
      \"itemId\": \"$SOURCE_LH_ID\",
      \"path\": \"Tables/customers\"
    }
  }
}"
```

### ADLS Gen2 Shortcut

```bash
fab api -X post "workspaces/$WS_ID/items/$LH_ID/shortcuts" -i '{
  "name": "azure_storage",
  "path": "Files/azure_data",
  "target": {
    "type": "AdlsGen2",
    "adlsGen2": {
      "location": "https://mystorageaccount.dfs.core.windows.net/container",
      "subpath": "/data/sales",
      "connectionId": "<connection-id>"
    }
  }
}'
```

### Amazon S3 Shortcut

```bash
fab api -X post "workspaces/$WS_ID/items/$LH_ID/shortcuts" -i '{
  "name": "s3_data",
  "path": "Files/aws_data",
  "target": {
    "type": "AmazonS3",
    "amazonS3": {
      "location": "https://mybucket.s3.amazonaws.com",
      "subpath": "/data/analytics",
      "connectionId": "<s3-connection-id>"
    }
  }
}'
```

### Google Cloud Storage Shortcut

```bash
fab api -X post "workspaces/$WS_ID/items/$LH_ID/shortcuts" -i '{
  "name": "gcs_data",
  "path": "Files/gcp_data",
  "target": {
    "type": "GoogleCloudStorage",
    "googleCloudStorage": {
      "location": "https://storage.cloud.google.com/my-bucket",
      "subpath": "/data",
      "connectionId": "<gcs-connection-id>"
    }
  }
}'
```

## Managing Shortcuts

### List Shortcuts

```bash
# List all shortcuts in lakehouse
fab api "workspaces/$WS_ID/items/$LH_ID/shortcuts"

# List with details
fab api "workspaces/$WS_ID/items/$LH_ID/shortcuts" -q "value[].{name: name, path: path, type: target.type}"
```

### Get Shortcut Details

```bash
# Get specific shortcut
fab api "workspaces/$WS_ID/items/$LH_ID/shortcuts/customer_data"
```

### Delete Shortcut

```bash
# Delete by name
fab api -X delete "workspaces/$WS_ID/items/$LH_ID/shortcuts/customer_data"
```

### Update Shortcut

```bash
# Shortcuts cannot be updated - delete and recreate
fab api -X delete "workspaces/$WS_ID/items/$LH_ID/shortcuts/old_shortcut"

fab api -X post "workspaces/$WS_ID/items/$LH_ID/shortcuts" -i '{
  "name": "new_shortcut",
  "path": "...",
  "target": {...}
}'
```

## Connection Management

### List Connections

```bash
# List all connections (for shortcut targets)
fab ls .connections -l

# Get connection details
fab get ".connections/AzureStorageConn.Connection"

# Get connection ID for shortcut
CONNECTION_ID=$(fab get ".connections/AzureStorageConn.Connection" -q "id" | tr -d '"')
```

### Create Connection for ADLS

```bash
fab api -X post "connections" -i '{
  "displayName": "AzureStorageConn",
  "connectionDetails": {
    "type": "AzureDataLakeStorageGen2",
    "parameters": {
      "server": "mystorageaccount.dfs.core.windows.net",
      "path": "container"
    }
  },
  "credentialDetails": {
    "credentialType": "ManagedIdentity"
  }
}'
```

## Use Cases

### Cross-Workspace Data Sharing

```bash
#!/bin/bash
# Share gold layer tables with consumer workspaces

SOURCE_WS="DataPlatform.Workspace"
SOURCE_LH="Gold.Lakehouse"

# Consumer workspace setup
for CONSUMER in "Marketing" "Sales" "Finance"; do
  TARGET_WS="$CONSUMER.Workspace"
  TARGET_LH="Analytics.Lakehouse"
  
  WS_ID=$(fab get "$TARGET_WS" -q "id" | tr -d '"')
  LH_ID=$(fab get "$TARGET_WS/$TARGET_LH" -q "id" | tr -d '"')
  SOURCE_WS_ID=$(fab get "$SOURCE_WS" -q "id" | tr -d '"')
  SOURCE_LH_ID=$(fab get "$SOURCE_WS/$SOURCE_LH" -q "id" | tr -d '"')
  
  # Create shortcuts to gold tables
  for TABLE in "sales_summary" "customer_360" "product_metrics"; do
    fab api -X post "workspaces/$WS_ID/items/$LH_ID/shortcuts" -i "{
      \"name\": \"$TABLE\",
      \"path\": \"Tables/$TABLE\",
      \"target\": {
        \"type\": \"OneLake\",
        \"oneLake\": {
          \"workspaceId\": \"$SOURCE_WS_ID\",
          \"itemId\": \"$SOURCE_LH_ID\",
          \"path\": \"Tables/$TABLE\"
        }
      }
    }"
    echo "Created shortcut to $TABLE in $CONSUMER workspace"
  done
done
```

### Multi-Cloud Data Lake

```bash
#!/bin/bash
# Federate data from multiple clouds

WS_ID=$(fab get "DataHub.Workspace" -q "id" | tr -d '"')
LH_ID=$(fab get "DataHub.Workspace/Federation.Lakehouse" -q "id" | tr -d '"')

# Azure Data Lake
fab api -X post "workspaces/$WS_ID/items/$LH_ID/shortcuts" -i '{
  "name": "azure_data",
  "path": "Files/azure",
  "target": {
    "type": "AdlsGen2",
    "adlsGen2": {
      "location": "https://azurestorage.dfs.core.windows.net/datalake",
      "subpath": "/production",
      "connectionId": "<azure-conn-id>"
    }
  }
}'

# AWS S3
fab api -X post "workspaces/$WS_ID/items/$LH_ID/shortcuts" -i '{
  "name": "aws_data",
  "path": "Files/aws",
  "target": {
    "type": "AmazonS3",
    "amazonS3": {
      "location": "https://company-bucket.s3.amazonaws.com",
      "subpath": "/analytics",
      "connectionId": "<s3-conn-id>"
    }
  }
}'

# Google Cloud Storage
fab api -X post "workspaces/$WS_ID/items/$LH_ID/shortcuts" -i '{
  "name": "gcp_data",
  "path": "Files/gcp",
  "target": {
    "type": "GoogleCloudStorage",
    "googleCloudStorage": {
      "location": "https://storage.cloud.google.com/company-bucket",
      "subpath": "/data",
      "connectionId": "<gcs-conn-id>"
    }
  }
}'
```

### Medallion Layer References

```bash
# Silver layer references bronze shortcuts for lineage
fab ln "DataPlatform.Workspace/Bronze.Lakehouse/Tables/raw_customers" \
       "DataPlatform.Workspace/Silver.Lakehouse/Tables/source_customers"

# Gold layer references silver dimensions
fab ln "DataPlatform.Workspace/Silver.Lakehouse/Tables/dim_customer" \
       "DataPlatform.Workspace/Gold.Lakehouse/Tables/dim_customer"

fab ln "DataPlatform.Workspace/Silver.Lakehouse/Tables/dim_product" \
       "DataPlatform.Workspace/Gold.Lakehouse/Tables/dim_product"
```

## Best Practices

### Naming Conventions

```bash
# Prefix by source type
ext_azure_sales       # External Azure shortcut
ext_s3_events         # External S3 shortcut
ref_silver_customers  # Reference to silver layer
shared_gold_summary   # Shared from gold layer
```

### Security Considerations

- Shortcuts inherit permissions from target
- Users need both shortcut and target access
- Use workspace roles for access control
- Connection credentials are managed separately

### Performance Tips

- Shortcuts add minimal latency
- External shortcuts depend on network
- Use OneLake shortcuts for best performance
- Consider data locality for external sources

## Troubleshooting

### Shortcut Not Accessible

```bash
# Check shortcut exists
fab api "workspaces/$WS_ID/items/$LH_ID/shortcuts/shortcut_name"

# Verify connection is valid
fab get ".connections/ConnectionName.Connection"

# Check permissions on source
fab acl get "Source.Workspace/Source.Lakehouse"
```

### Data Not Visible

```bash
# Verify source path exists
fab ls "Source.Workspace/Source.Lakehouse/Tables/tablename"

# Check shortcut path
fab api "workspaces/$WS_ID/items/$LH_ID/shortcuts/shortcut_name" -q "target.path"
```

### External Source Errors

```bash
# Verify connection credentials
fab get ".connections/AzureConn.Connection" -q "credentialDetails"

# Check network connectivity
# For ADLS: Verify storage account firewall settings
# For S3: Verify IAM permissions and bucket policy
```
