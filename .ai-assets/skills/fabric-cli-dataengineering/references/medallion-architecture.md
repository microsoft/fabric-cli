# Medallion Architecture Reference

Guide to implementing bronze/silver/gold data layers using the Fabric CLI.

## Architecture Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   BRONZE    │ -> │   SILVER    │ -> │    GOLD     │
│  Raw Data   │    │  Cleansed   │    │  Business   │
│  As-Is     │    │  Conformed  │    │   Ready     │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Layer Purposes

| Layer | Purpose | Data Quality | Consumers |
|-------|---------|--------------|-----------|
| Bronze | Raw ingestion | As-is from source | Data engineers |
| Silver | Cleansed, validated | Standardized types, deduped | Data scientists, analysts |
| Gold | Business-ready | Aggregated, denormalized | Business users, reports |

## Creating the Architecture

### Full Setup Script

```bash
#!/bin/bash
WORKSPACE="DataPlatform"
CAPACITY="FabricProd"

# Create workspace on capacity
fab mkdir "$WORKSPACE.Workspace" -P capacityname=$CAPACITY

# Create medallion lakehouses
fab mkdir "$WORKSPACE.Workspace/Bronze.Lakehouse"
fab mkdir "$WORKSPACE.Workspace/Silver.Lakehouse"
fab mkdir "$WORKSPACE.Workspace/Gold.Lakehouse"

# Create file landing zones in Bronze
fab mkdir "$WORKSPACE.Workspace/Bronze.Lakehouse/Files/landing"
fab mkdir "$WORKSPACE.Workspace/Bronze.Lakehouse/Files/processing"
fab mkdir "$WORKSPACE.Workspace/Bronze.Lakehouse/Files/archive"
fab mkdir "$WORKSPACE.Workspace/Bronze.Lakehouse/Files/error"

# Optionally create staging area
fab mkdir "$WORKSPACE.Workspace/Staging.Lakehouse"

# Create warehouse for SQL-based gold access
fab mkdir "$WORKSPACE.Workspace/Analytics.Warehouse"

echo "Medallion architecture created in $WORKSPACE"
```

## Bronze Layer Patterns

### Purpose

- Store raw data exactly as received
- Preserve original schema and format
- Enable data replay/reprocessing
- Audit trail of source data

### Structure

```
Bronze.Lakehouse/
├── Tables/
│   └── dbo/
│       ├── raw_customers       # CDC from source
│       ├── raw_orders          # Daily extract
│       ├── raw_products        # API feed
│       └── raw_events          # Streaming data
└── Files/
    ├── landing/
    │   ├── crm/               # Source system folders
    │   │   └── 2024-01-15/
    │   ├── erp/
    │   └── web/
    ├── processing/            # Active work
    ├── archive/               # Processed files
    └── error/                 # Failed files
```

### Bronze Ingestion Pattern

```bash
#!/bin/bash
WORKSPACE="DataPlatform.Workspace"
DATE=$(date +%Y-%m-%d)
SOURCE="crm"

# 1. Upload raw files to landing
fab cp ./incoming/$SOURCE/* \
  "$WORKSPACE/Bronze.Lakehouse/Files/landing/$SOURCE/$DATE/"

# 2. Load into raw table (append)
fab table load "$WORKSPACE/Bronze.Lakehouse/Tables/raw_customers" \
  --file "$WORKSPACE/Bronze.Lakehouse/Files/landing/$SOURCE/$DATE/" \
  --mode append \
  --format format=parquet

# 3. Archive processed files
fab mv "$WORKSPACE/Bronze.Lakehouse/Files/landing/$SOURCE/$DATE/" \
       "$WORKSPACE/Bronze.Lakehouse/Files/archive/$SOURCE/$DATE/"

echo "Bronze ingestion complete for $SOURCE on $DATE"
```

### Bronze Table Naming

```bash
# Prefix: raw_
# Include source system if multiple
raw_crm_customers
raw_erp_orders
raw_web_events
raw_api_products
```

## Silver Layer Patterns

### Purpose

- Clean and validate data
- Apply business rules
- Standardize data types
- Deduplicate records
- Create conformed dimensions

### Structure

```
Silver.Lakehouse/
├── Tables/
│   └── dbo/
│       ├── dim_customer       # Cleansed dimension
│       ├── dim_product
│       ├── dim_date
│       ├── fact_orders        # Validated facts
│       └── fact_inventory
└── Files/
    └── temp/                  # Processing workspace
```

### Bronze to Silver Transformation

```bash
#!/bin/bash
WORKSPACE="DataPlatform.Workspace"

# Run transformation notebook
fab job run "$WORKSPACE/BronzeToSilver.Notebook" \
  -P source_table:string=raw_customers,target_table:string=dim_customer \
  --timeout 600

# Optimize silver table
fab table optimize "$WORKSPACE/Silver.Lakehouse/Tables/dbo/dim_customer" --vorder
```

### Silver Table Naming

```bash
# Dimensions: dim_
dim_customer
dim_product
dim_date
dim_location

# Facts: fact_
fact_orders
fact_inventory
fact_shipments

# Staging: stg_
stg_customer_dedup
stg_orders_validated
```

## Gold Layer Patterns

### Purpose

- Business-ready aggregations
- Denormalized for reporting
- Pre-computed metrics
- Domain-specific views

### Structure

```
Gold.Lakehouse/
└── Tables/
    └── dbo/
        ├── sales_summary          # Daily/weekly aggregates
        ├── customer_360           # Customer analytics
        ├── product_performance    # Product metrics
        └── executive_dashboard    # KPI aggregates
```

### Silver to Gold Aggregation

```bash
#!/bin/bash
WORKSPACE="DataPlatform.Workspace"

# Run aggregation notebook
fab job run "$WORKSPACE/SilverToGold.Notebook" --timeout 300

# Optimize gold tables for queries
fab table optimize "$WORKSPACE/Gold.Lakehouse/Tables/sales_summary" \
  --vorder --zorder report_date,region
```

### Gold Table Naming

```bash
# Aggregated: agg_
agg_daily_sales
agg_monthly_revenue

# Reports: rpt_
rpt_customer_summary
rpt_product_performance

# Analytics: anlyt_
anlyt_customer_360
anlyt_churn_prediction
```

## Cross-Layer Data Flow

### Using Shortcuts for Reference

```bash
# Share silver dimensions with gold layer
fab ln "$WORKSPACE/Silver.Lakehouse/Tables/dbo/dim_customer" \
       "$WORKSPACE/Gold.Lakehouse/Tables/dbo/dim_customer"

fab ln "$WORKSPACE/Silver.Lakehouse/Tables/dbo/dim_product" \
       "$WORKSPACE/Gold.Lakehouse/Tables/dbo/dim_product"

fab ln "$WORKSPACE/Silver.Lakehouse/Tables/dbo/dim_date" \
       "$WORKSPACE/Gold.Lakehouse/Tables/dbo/dim_date"
```

### End-to-End Pipeline

```bash
#!/bin/bash
WORKSPACE="DataPlatform.Workspace"
DATE=$(date +%Y-%m-%d)

echo "=== Starting ETL Pipeline for $DATE ==="

# Step 1: Ingest to Bronze
echo "Step 1: Bronze Ingestion"
fab job run "$WORKSPACE/IngestToBronze.DataPipeline" \
  -P process_date:string=$DATE --timeout 600
echo "Bronze complete"

# Step 2: Transform to Silver
echo "Step 2: Silver Transformation"
fab job run "$WORKSPACE/BronzeToSilver.Notebook" \
  -P process_date:string=$DATE --timeout 900
echo "Silver complete"

# Step 3: Aggregate to Gold
echo "Step 3: Gold Aggregation"
fab job run "$WORKSPACE/SilverToGold.Notebook" \
  -P process_date:string=$DATE --timeout 300
echo "Gold complete"

# Step 4: Optimize tables
echo "Step 4: Table Optimization"
for LAYER in Bronze Silver Gold; do
  fab job run "$WORKSPACE/$LAYER.Lakehouse" --timeout 600
done
echo "Optimization complete"

echo "=== ETL Pipeline Complete ==="
```

## Best Practices

### Layer Isolation

```bash
# Separate permissions per layer
# Bronze: Data Engineers only
fab acl set "$WORKSPACE/Bronze.Lakehouse" -P principal=DataEngineers@company.com,role=Contributor

# Silver: Data Engineers + Scientists
fab acl set "$WORKSPACE/Silver.Lakehouse" -P principal=DataScientists@company.com,role=Viewer

# Gold: All analysts
fab acl set "$WORKSPACE/Gold.Lakehouse" -P principal=AllAnalysts@company.com,role=Viewer
```

### Data Quality Checkpoints

```bash
# Add validation between layers
# Run quality checks notebook
fab job run "$WORKSPACE/DataQuality.Notebook" \
  -P layer:string=bronze,tables:array=["raw_customers","raw_orders"]
```

### Retention Policies

```bash
# Bronze: Keep all data (history)
# No vacuum or aggressive retention

# Silver: Moderate retention
fab table vacuum "$WORKSPACE/Silver.Lakehouse/Tables/dbo/dim_customer" \
  --retain_n_hours 720  # 30 days

# Gold: Short retention (current data)
fab table vacuum "$WORKSPACE/Gold.Lakehouse/Tables/agg_daily_sales" \
  --retain_n_hours 168  # 7 days
```

## Multi-Workspace Pattern

For large organizations, consider separate workspaces:

```bash
# Create workspace per layer
fab mkdir "DataPlatform-Bronze.Workspace" -P capacityname=FabricProd
fab mkdir "DataPlatform-Silver.Workspace" -P capacityname=FabricProd
fab mkdir "DataPlatform-Gold.Workspace" -P capacityname=FabricProd

# Create lakehouses in each
fab mkdir "DataPlatform-Bronze.Workspace/Bronze.Lakehouse"
fab mkdir "DataPlatform-Silver.Workspace/Silver.Lakehouse"
fab mkdir "DataPlatform-Gold.Workspace/Gold.Lakehouse"

# Use shortcuts for cross-workspace access
fab ln "DataPlatform-Silver.Workspace/Silver.Lakehouse/Tables/dbo/dim_customer" \
       "DataPlatform-Gold.Workspace/Gold.Lakehouse/Tables/dbo/dim_customer"
```

## Troubleshooting

### Data Freshness Issues

```bash
# Check last load time for tables
fab get "$WORKSPACE/Silver.Lakehouse" -q "properties.lastModifiedDateTime"

# Check job history
fab job run-list "$WORKSPACE/BronzeToSilver.Notebook"
```

### Schema Drift

```bash
# Compare schemas between layers
fab table schema "$WORKSPACE/Bronze.Lakehouse/Tables/raw_customers"
fab table schema "$WORKSPACE/Silver.Lakehouse/Tables/dim_customer"

# Run schema evolution notebook
fab job run "$WORKSPACE/SchemaEvolution.Notebook" -P table:string=customers
```
