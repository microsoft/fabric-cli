---
name: fabric-cli-dataengineering
description: Use Fabric CLI for data engineering — lakehouses, warehouses, shortcuts, table optimization, medallion architecture, and Spark jobs. Activate when users work with data storage, ETL patterns, Delta tables, or data pipeline orchestration.
---

# Fabric CLI Data Engineering

Expert guidance for data engineering operations in Microsoft Fabric using the `fab` CLI.

## When to Use This Skill

Activate automatically when tasks involve:

- Creating and managing Lakehouses or Warehouses
- Building medallion architecture (bronze/silver/gold layers)
- Creating and managing OneLake shortcuts
- Table operations (load, optimize, vacuum)
- Spark job configuration and execution
- Data pipeline orchestration
- Delta table management

## Prerequisites

- Load `fabric-cli-core` skill first for foundational CLI guidance
- User must be authenticated: `fab auth status`
- Contributor or higher role for data operations

## Automation Scripts

Ready-to-use Python scripts for data engineering tasks. Run any script with `--help` for full options.

| Script | Purpose | Usage |
|--------|---------|-------|
| `setup_medallion.py` | Create medallion architecture (bronze/silver/gold) | `python scripts/setup_medallion.py <workspace> [--prefix NAME]` |
| `optimize_tables.py` | Run optimization on lakehouse tables | `python scripts/optimize_tables.py <lakehouse> [--vorder]` |
| `validate_shortcuts.py` | Verify all shortcuts are accessible | `python scripts/validate_shortcuts.py <lakehouse>` |

Scripts are located in the `scripts/` folder of this skill.

## 1 - Lakehouse Operations

### Create Lakehouse

```bash
# Create basic lakehouse
fab mkdir "DataPlatform.Workspace/Bronze.Lakehouse"

# Create with schema support (preview)
fab mkdir "DataPlatform.Workspace/SchemaSilver.Lakehouse" -P enableSchemas=true

# Check available parameters
fab mkdir "Item.Lakehouse" -P
```

### Lakehouse Structure

```
Lakehouse/
├── Tables/           # Delta tables (managed)
│   ├── dbo/         # Default schema
│   │   ├── customers
│   │   └── orders
│   └── staging/     # Custom schema (if enabled)
└── Files/           # Unmanaged files
    ├── raw/
    ├── staging/
    └── exports/
```

### List Lakehouse Contents

```bash
# List lakehouse root
fab ls "DataPlatform.Workspace/Bronze.Lakehouse"

# List tables
fab ls "DataPlatform.Workspace/Bronze.Lakehouse/Tables"

# List tables in schema
fab ls "DataPlatform.Workspace/Bronze.Lakehouse/Tables/dbo"

# List files
fab ls "DataPlatform.Workspace/Bronze.Lakehouse/Files"
fab ls "DataPlatform.Workspace/Bronze.Lakehouse/Files/raw" -l
```

### Get Lakehouse Properties

```bash
# Get lakehouse details
fab get "DataPlatform.Workspace/Bronze.Lakehouse" -v

# Get SQL endpoint connection string
fab get "DataPlatform.Workspace/Bronze.Lakehouse" -q "properties.sqlEndpointProperties"

# Get OneLake path
fab get "DataPlatform.Workspace/Bronze.Lakehouse" -q "properties.oneLakeFilesPath"
```

## 2 - Warehouse Operations

### Create Warehouse

```bash
# Create basic warehouse
fab mkdir "DataPlatform.Workspace/SalesDW.Warehouse"

# Create with case-insensitive collation
fab mkdir "DataPlatform.Workspace/AnalyticsDW.Warehouse" -P enableCaseInsensitive=true
```

### Warehouse vs Lakehouse

| Feature | Lakehouse | Warehouse |
|---------|-----------|-----------|
| Query Engine | Spark + SQL | T-SQL |
| Best For | Data engineering | BI/Analytics |
| Storage Format | Delta | Delta |
| Schema Support | Optional | Built-in |
| Direct Lake | Yes | Yes |

## 3 - File Operations

### Upload Files to Lakehouse

```bash
# Upload single file
fab cp ./data/sales.csv "DataPlatform.Workspace/Bronze.Lakehouse/Files/raw/sales.csv"

# Upload directory
fab cp ./data/customers/ "DataPlatform.Workspace/Bronze.Lakehouse/Files/raw/customers/"

# Upload with force (overwrite)
fab cp ./data/daily.parquet "DataPlatform.Workspace/Bronze.Lakehouse/Files/staging/daily.parquet" -f
```

### Download Files

```bash
# Download single file
fab cp "DataPlatform.Workspace/Bronze.Lakehouse/Files/exports/report.csv" ./downloads/

# Download directory
fab cp "DataPlatform.Workspace/Bronze.Lakehouse/Files/raw/" ./backup/raw/
```

### Move and Delete Files

```bash
# Move file
fab mv "DataPlatform.Workspace/Bronze.Lakehouse/Files/staging/data.parquet" \
       "DataPlatform.Workspace/Bronze.Lakehouse/Files/processed/"

# Delete file
fab rm "DataPlatform.Workspace/Bronze.Lakehouse/Files/temp/old-data.csv" -f

# Delete directory
fab rm "DataPlatform.Workspace/Bronze.Lakehouse/Files/archive/" -f
```

## 4 - Table Operations

### View Table Schema

```bash
# Get table schema
fab table schema "DataPlatform.Workspace/Bronze.Lakehouse/Tables/dbo/customers"

# View warehouse table schema
fab table schema "DataPlatform.Workspace/SalesDW.Warehouse/Tables/sales/orders"
```

### Load Data into Table

```bash
# Load CSV files into table
fab table load "DataPlatform.Workspace/Bronze.Lakehouse/Tables/customers" \
  --file "DataPlatform.Workspace/Bronze.Lakehouse/Files/raw/customers"

# Load with append mode
fab table load "DataPlatform.Workspace/Bronze.Lakehouse/Tables/sales" \
  --file "DataPlatform.Workspace/Bronze.Lakehouse/Files/daily_sales.csv" \
  --mode append

# Load with overwrite
fab table load "DataPlatform.Workspace/Bronze.Lakehouse/Tables/dim_date" \
  --file "DataPlatform.Workspace/Bronze.Lakehouse/Files/dimensions/date.parquet" \
  --mode overwrite

# Load with custom CSV format
fab table load "DataPlatform.Workspace/Bronze.Lakehouse/Tables/products" \
  --file "DataPlatform.Workspace/Bronze.Lakehouse/Files/csv/products" \
  --format "format=csv,header=true,delimiter=|"

# Load Parquet files
fab table load "DataPlatform.Workspace/Bronze.Lakehouse/Tables/events" \
  --file "DataPlatform.Workspace/Bronze.Lakehouse/Files/parquet/" \
  --format format=parquet
```

### Optimize Table

```bash
# Basic optimization (compaction)
fab table optimize "DataPlatform.Workspace/Bronze.Lakehouse/Tables/transactions"

# V-Order optimization (better compression)
fab table optimize "DataPlatform.Workspace/Bronze.Lakehouse/Tables/sales" --vorder

# Z-Order optimization (query performance)
fab table optimize "DataPlatform.Workspace/Bronze.Lakehouse/Tables/customers" \
  --vorder --zorder customer_id,region

# Optimize with multiple Z-Order columns
fab table optimize "DataPlatform.Workspace/Bronze.Lakehouse/Tables/orders" \
  --vorder --zorder order_date,customer_id,product_id
```

### Vacuum Table

```bash
# Vacuum with default retention (7 days)
fab table vacuum "DataPlatform.Workspace/Bronze.Lakehouse/Tables/transactions"

# Vacuum with custom retention (48 hours)
fab table vacuum "DataPlatform.Workspace/Bronze.Lakehouse/Tables/temp_data" \
  --retain_n_hours 48

# Vacuum with minimum retention (for testing)
fab table vacuum "DataPlatform.Workspace/Bronze.Lakehouse/Tables/dev_table" \
  --retain_n_hours 0
```

## 5 - Shortcuts (Data Federation)

### Create Shortcuts

Shortcuts enable data federation without copying data.

```bash
# List existing shortcuts
fab ls "DataPlatform.Workspace/Bronze.Lakehouse/Files/shortcuts"

# Create shortcut to another lakehouse
fab ln "Source.Workspace/SourceLH.Lakehouse/Tables/customers" \
       "DataPlatform.Workspace/Bronze.Lakehouse/Tables/customers_ref"
```

### Shortcut Types

| Source | Use Case |
|--------|----------|
| OneLake (another lakehouse) | Cross-workspace data sharing |
| ADLS Gen2 | Azure Data Lake integration |
| Amazon S3 | AWS data federation |
| Google Cloud Storage | GCP data federation |
| Dataverse | Power Platform integration |

### Create ADLS Shortcut via API

```bash
WS_ID=$(fab get "DataPlatform.Workspace" -q "id" | tr -d '"')
LH_ID=$(fab get "DataPlatform.Workspace/Bronze.Lakehouse" -q "id" | tr -d '"')

fab api -X post "workspaces/$WS_ID/items/$LH_ID/shortcuts" -i '{
  "name": "external-data",
  "path": "Files/external",
  "target": {
    "type": "AdlsGen2",
    "adlsGen2": {
      "location": "https://storageaccount.dfs.core.windows.net/container/path",
      "subpath": "/data"
    }
  }
}'
```

### List Shortcuts

```bash
# List all shortcuts in lakehouse
fab api "workspaces/$WS_ID/items/$LH_ID/shortcuts"
```

### Delete Shortcut

```bash
fab api -X delete "workspaces/$WS_ID/items/$LH_ID/shortcuts/shortcut-name"
```

## 6 - Medallion Architecture

### Standard Structure

```
Workspace/
├── Bronze.Lakehouse       # Raw data
│   ├── Tables/
│   │   └── raw_customers
│   │   └── raw_orders
│   └── Files/
│       └── landing/
├── Silver.Lakehouse       # Cleansed/conformed
│   └── Tables/
│       └── dim_customers
│       └── fact_orders
└── Gold.Lakehouse         # Business-ready
    └── Tables/
        └── sales_summary
        └── customer_360
```

### Create Medallion Layers

```bash
#!/bin/bash
WORKSPACE="DataPlatform"

# Create workspace
fab mkdir "$WORKSPACE.Workspace" -P capacityname=FabricProd

# Create medallion lakehouses
fab mkdir "$WORKSPACE.Workspace/Bronze.Lakehouse"
fab mkdir "$WORKSPACE.Workspace/Silver.Lakehouse"
fab mkdir "$WORKSPACE.Workspace/Gold.Lakehouse"

# Create file landing zone in Bronze
fab mkdir "$WORKSPACE.Workspace/Bronze.Lakehouse/Files/landing"
fab mkdir "$WORKSPACE.Workspace/Bronze.Lakehouse/Files/archive"

echo "Medallion architecture created"
```

### Cross-Layer Shortcuts

```bash
# Create shortcut from Gold to Silver for lineage
fab ln "DataPlatform.Workspace/Silver.Lakehouse/Tables/dim_customers" \
       "DataPlatform.Workspace/Gold.Lakehouse/Tables/dim_customers"
```

## 7 - Spark Job Execution

### Run Notebook

```bash
# Run notebook synchronously
fab job run "DataPlatform.Workspace/ETL.Notebook" --timeout 600

# Run with parameters
fab job run "DataPlatform.Workspace/ETL.Notebook" \
  -P source_date:string=2024-01-15,batch_size:int=10000

# Run with Spark configuration
fab job run "DataPlatform.Workspace/LargeETL.Notebook" \
  -C '{"conf": {"spark.executor.memory": "8g", "spark.executor.cores": "4"}}'

# Run with specific lakehouse
fab job run "DataPlatform.Workspace/Transform.Notebook" \
  -C '{"defaultLakehouse": {"name": "Silver", "id": "<lakehouse-id>"}}'
```

### Run Spark Job Definition

```bash
# Run Spark job
fab job run "DataPlatform.Workspace/DailyETL.SparkJobDefinition" --timeout 1800

# Run with parameters
fab job run "DataPlatform.Workspace/DailyETL.SparkJobDefinition" \
  -P input_path:string=/data/raw,output_path:string=/data/processed
```

### Run Pipeline

```bash
# Run data pipeline
fab job run "DataPlatform.Workspace/MasterPipeline.DataPipeline"

# Run with complex parameters
fab job run "DataPlatform.Workspace/ETLPipeline.DataPipeline" \
  -P 'config:object={"source":"sql","target":"lakehouse"},tables:array=["customers","orders"]'
```

## 8 - Lakehouse Maintenance

### Run Lakehouse Maintenance

```bash
# Trigger maintenance job (optimize + vacuum)
fab job run "DataPlatform.Workspace/Bronze.Lakehouse" --timeout 1200
```

### Automated Maintenance Script

```bash
#!/bin/bash
WORKSPACE="DataPlatform.Workspace"
LAKEHOUSES=("Bronze" "Silver" "Gold")

for LH in "${LAKEHOUSES[@]}"; do
  echo "Optimizing $LH..."
  
  # Get all tables
  TABLES=$(fab ls "$WORKSPACE/$LH.Lakehouse/Tables/dbo" -q "value[].name")
  
  for TABLE in $TABLES; do
    echo "  Optimizing table: $TABLE"
    fab table optimize "$WORKSPACE/$LH.Lakehouse/Tables/dbo/$TABLE" --vorder
    fab table vacuum "$WORKSPACE/$LH.Lakehouse/Tables/dbo/$TABLE"
  done
done
```

## 9 - Environment Management

### Spark Pool Configuration

```bash
# List workspace spark pools
fab ls "DataPlatform.Workspace/.sparkpools"

# Get spark pool details
fab get "DataPlatform.Workspace/.sparkpools/HighMemory.SparkPool"
```

### Run Job with Workspace Pool

```bash
fab job run "DataPlatform.Workspace/HeavyETL.Notebook" \
  -C '{"useStarterPool": false, "useWorkspacePool": "HighMemoryPool"}'
```

### Environment Configuration

```bash
# Get workspace environment settings
fab get "DataPlatform.Workspace" -q "sparkSettings"

# Update default Spark runtime
fab set "DataPlatform.Workspace" -q sparkSettings.environment.runtimeVersion -i 1.3
```

## 10 - Data Pipeline Patterns

### Daily ETL Pattern

```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d)
WORKSPACE="DataPlatform.Workspace"

# 1. Load raw data
fab cp ./daily-data/$DATE/ "$WORKSPACE/Bronze.Lakehouse/Files/landing/$DATE/"

# 2. Run bronze to silver transformation
fab job run "$WORKSPACE/BronzeToSilver.Notebook" \
  -P process_date:string=$DATE --timeout 600

# 3. Run silver to gold aggregation
fab job run "$WORKSPACE/SilverToGold.Notebook" \
  -P process_date:string=$DATE --timeout 300

# 4. Optimize tables
fab table optimize "$WORKSPACE/Gold.Lakehouse/Tables/daily_summary" --vorder

echo "Daily ETL completed for $DATE"
```

### Incremental Load Pattern

```bash
#!/bin/bash
# Get last processed watermark
WATERMARK=$(fab api "workspaces/$WS_ID/lakehouses/$LH_ID/metadata" \
  -q "properties.lastWatermark" | tr -d '"')

# Run incremental notebook
fab job run "DataPlatform.Workspace/IncrementalLoad.Notebook" \
  -P watermark:string=$WATERMARK --timeout 600

# Update watermark after success
NEW_WATERMARK=$(date -u +%Y-%m-%dT%H:%M:%SZ)
# Store new watermark for next run
```

## 11 - Best Practices

### Table Optimization Guidelines

| Scenario | Recommendation |
|----------|---------------|
| Frequent small writes | V-Order optimization |
| Point lookups | Z-Order on lookup columns |
| Time-series data | Z-Order on date + partition columns |
| Large aggregations | V-Order for compression |

### File Organization

```bash
# Recommended file structure
Bronze.Lakehouse/
├── Files/
│   ├── landing/          # Incoming raw data
│   │   └── YYYY-MM-DD/   # Date partitioned
│   ├── processing/       # In-progress transformations
│   ├── archive/          # Processed files (compressed)
│   └── error/            # Failed processing
└── Tables/
    └── raw_*             # Delta tables from loaded data
```

### Naming Conventions

```bash
# Lakehouses: Function-based
fab mkdir "DataPlatform.Workspace/Bronze.Lakehouse"
fab mkdir "DataPlatform.Workspace/Silver.Lakehouse"
fab mkdir "DataPlatform.Workspace/Gold.Lakehouse"

# Tables: Prefix with layer
# bronze: raw_customers, raw_orders
# silver: dim_customers, fact_orders
# gold: agg_sales, rpt_customer_summary
```

## 12 - References

For detailed patterns, see:

- [references/lakehouse-patterns.md](./references/lakehouse-patterns.md) — Lakehouse management
- [references/medallion-architecture.md](./references/medallion-architecture.md) — Layer design patterns
- [references/shortcuts.md](./references/shortcuts.md) — Data federation
- [references/table-optimization.md](./references/table-optimization.md) — Performance tuning
- [references/spark-configuration.md](./references/spark-configuration.md) — Spark settings
