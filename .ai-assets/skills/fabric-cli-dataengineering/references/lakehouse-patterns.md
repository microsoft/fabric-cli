# Lakehouse Patterns Reference

Comprehensive guide to lakehouse creation, management, and best practices.

## Creating Lakehouses

### Basic Creation

```bash
# Create lakehouse
fab mkdir "DataPlatform.Workspace/Analytics.Lakehouse"

# Verify creation
fab exists "DataPlatform.Workspace/Analytics.Lakehouse"
fab get "DataPlatform.Workspace/Analytics.Lakehouse" -v
```

### Schema-Enabled Lakehouse

```bash
# Enable schemas for better organization (preview)
fab mkdir "DataPlatform.Workspace/Enterprise.Lakehouse" -P enableSchemas=true

# With schemas, you can organize tables:
# Tables/sales/orders
# Tables/sales/customers
# Tables/finance/invoices
```

### Check Creation Parameters

```bash
# See available parameters
fab mkdir "Item.Lakehouse" -P
```

## Lakehouse Structure

### Default Layout

```
Lakehouse/
├── Tables/           # Delta tables
│   └── dbo/         # Default schema
│       ├── customers
│       └── orders
└── Files/           # Raw/unmanaged files
    ├── raw/
    ├── staging/
    └── processed/
```

### With Schemas Enabled

```
Lakehouse/
├── Tables/
│   ├── sales/
│   │   ├── customers
│   │   └── orders
│   ├── finance/
│   │   ├── invoices
│   │   └── payments
│   └── staging/
│       └── temp_data
└── Files/
```

## File Operations

### Upload Files

```bash
# Single file
fab cp ./data/customers.csv "DataPlatform.Workspace/Bronze.Lakehouse/Files/raw/customers.csv"

# Directory (recursive)
fab cp ./data/sales/ "DataPlatform.Workspace/Bronze.Lakehouse/Files/raw/sales/"

# Overwrite existing
fab cp ./data/updated.parquet "DataPlatform.Workspace/Bronze.Lakehouse/Files/raw/data.parquet" -f
```

### Download Files

```bash
# Download single file
fab cp "DataPlatform.Workspace/Bronze.Lakehouse/Files/exports/report.csv" ./local/

# Download directory
fab cp "DataPlatform.Workspace/Bronze.Lakehouse/Files/raw/" ./backup/
```

### List Files

```bash
# List lakehouse root
fab ls "DataPlatform.Workspace/Bronze.Lakehouse"

# List files with details
fab ls "DataPlatform.Workspace/Bronze.Lakehouse/Files" -l

# List nested directory
fab ls "DataPlatform.Workspace/Bronze.Lakehouse/Files/raw/sales" -l
```

### Organize Files

```bash
# Create directory structure
fab mkdir "DataPlatform.Workspace/Bronze.Lakehouse/Files/landing"
fab mkdir "DataPlatform.Workspace/Bronze.Lakehouse/Files/processing"
fab mkdir "DataPlatform.Workspace/Bronze.Lakehouse/Files/archive"
fab mkdir "DataPlatform.Workspace/Bronze.Lakehouse/Files/error"

# Move processed files
fab mv "DataPlatform.Workspace/Bronze.Lakehouse/Files/landing/2024-01-15/" \
       "DataPlatform.Workspace/Bronze.Lakehouse/Files/archive/"

# Delete old files
fab rm "DataPlatform.Workspace/Bronze.Lakehouse/Files/archive/2023-*" -f
```

## Table Management

### List Tables

```bash
# List all tables
fab ls "DataPlatform.Workspace/Bronze.Lakehouse/Tables"

# List tables in schema
fab ls "DataPlatform.Workspace/Bronze.Lakehouse/Tables/dbo"
fab ls "DataPlatform.Workspace/Bronze.Lakehouse/Tables/sales"
```

### Get Table Schema

```bash
# View table columns and types
fab table schema "DataPlatform.Workspace/Bronze.Lakehouse/Tables/dbo/customers"
```

### Load Data into Tables

```bash
# From CSV folder
fab table load "DataPlatform.Workspace/Bronze.Lakehouse/Tables/customers" \
  --file "DataPlatform.Workspace/Bronze.Lakehouse/Files/raw/customers"

# From Parquet files
fab table load "DataPlatform.Workspace/Bronze.Lakehouse/Tables/events" \
  --file "DataPlatform.Workspace/Bronze.Lakehouse/Files/raw/events" \
  --format format=parquet

# Append mode
fab table load "DataPlatform.Workspace/Bronze.Lakehouse/Tables/transactions" \
  --file "DataPlatform.Workspace/Bronze.Lakehouse/Files/daily/2024-01-15.parquet" \
  --mode append

# Overwrite mode
fab table load "DataPlatform.Workspace/Bronze.Lakehouse/Tables/dim_date" \
  --file "DataPlatform.Workspace/Bronze.Lakehouse/Files/dimensions/date.csv" \
  --mode overwrite

# Custom CSV format
fab table load "DataPlatform.Workspace/Bronze.Lakehouse/Tables/legacy_data" \
  --file "DataPlatform.Workspace/Bronze.Lakehouse/Files/legacy/" \
  --format "format=csv,header=false,delimiter=|,encoding=UTF-8"
```

## SQL Analytics Endpoint

### Get Connection Info

```bash
# Get SQL endpoint details
fab get "DataPlatform.Workspace/Bronze.Lakehouse" -q "properties.sqlEndpointProperties"

# Get connection string
fab get "DataPlatform.Workspace/Bronze.Lakehouse" -q "properties.sqlEndpointProperties.connectionString"
```

### Query via API

```bash
WS_ID=$(fab get "DataPlatform.Workspace" -q "id" | tr -d '"')
LH_ID=$(fab get "DataPlatform.Workspace/Bronze.Lakehouse" -q "id" | tr -d '"')

# Execute SQL query
fab api -X post "workspaces/$WS_ID/lakehouses/$LH_ID/jobs/instances?jobType=TableMaintenance" -i '{}'
```

## Lakehouse Properties

### Get All Properties

```bash
fab get "DataPlatform.Workspace/Bronze.Lakehouse" -v
```

### Important Properties

```bash
# OneLake paths
fab get "DataPlatform.Workspace/Bronze.Lakehouse" -q "properties.oneLakeFilesPath"
fab get "DataPlatform.Workspace/Bronze.Lakehouse" -q "properties.oneLakeTablesPath"

# SQL endpoint
fab get "DataPlatform.Workspace/Bronze.Lakehouse" -q "properties.sqlEndpointProperties.id"

# Default schema
fab get "DataPlatform.Workspace/Bronze.Lakehouse" -q "properties.defaultSchema"
```

## Cross-Lakehouse Operations

### Copy Between Lakehouses

```bash
# Copy file
fab cp "Source.Workspace/SourceLH.Lakehouse/Files/data.parquet" \
       "Target.Workspace/TargetLH.Lakehouse/Files/imported/"

# Note: For tables, use export/import or shortcuts
```

### Export Lakehouse

```bash
# Export lakehouse definition
fab export "DataPlatform.Workspace/Bronze.Lakehouse" -o ./backup/ -f
```

## Best Practices

### File Organization

```bash
# Recommended structure
Files/
├── landing/              # Incoming raw data
│   └── source_system/
│       └── YYYY-MM-DD/
├── processing/           # Active transformation work
├── staging/              # Intermediate results
├── archive/              # Processed files (compressed)
│   └── YYYY/
│       └── MM/
└── error/                # Failed processing
```

### Table Naming

```bash
# Use consistent prefixes
# raw_* for raw data tables
# stg_* for staging tables
# dim_* for dimension tables
# fact_* for fact tables
# agg_* for aggregated tables
```

### Maintenance Schedule

```bash
#!/bin/bash
# Weekly maintenance script
WORKSPACE="DataPlatform.Workspace"
LAKEHOUSE="Bronze.Lakehouse"

# Optimize all tables
for TABLE in $(fab ls "$WORKSPACE/$LAKEHOUSE/Tables/dbo" -q "value[].name"); do
  echo "Maintaining $TABLE..."
  fab table optimize "$WORKSPACE/$LAKEHOUSE/Tables/dbo/$TABLE" --vorder
  fab table vacuum "$WORKSPACE/$LAKEHOUSE/Tables/dbo/$TABLE" --retain_n_hours 168
done

# Archive old files
ARCHIVE_DATE=$(date -d "30 days ago" +%Y-%m-%d)
fab mv "$WORKSPACE/$LAKEHOUSE/Files/processed/*" \
       "$WORKSPACE/$LAKEHOUSE/Files/archive/"
```

## Troubleshooting

### Table Load Failures

```bash
# Check file format matches expected
fab ls "DataPlatform.Workspace/Bronze.Lakehouse/Files/raw/" -l

# Verify file is accessible
fab cp "DataPlatform.Workspace/Bronze.Lakehouse/Files/raw/test.csv" ./test.csv

# Check for schema conflicts
fab table schema "DataPlatform.Workspace/Bronze.Lakehouse/Tables/target"
```

### Permission Issues

```bash
# Verify workspace access
fab acl get "DataPlatform.Workspace"

# Need Contributor role for write operations
```

### SQL Endpoint Not Available

```bash
# SQL endpoint may take time to provision
# Check status
fab get "DataPlatform.Workspace/Bronze.Lakehouse" -q "properties.sqlEndpointProperties.provisioningStatus"
```
