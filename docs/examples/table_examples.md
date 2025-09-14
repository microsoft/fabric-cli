# Table Management Examples

This page demonstrates how to manage tables in Microsoft Fabric using the CLI. Table operations enable schema inspection, data loading, optimization, and maintenance across various Fabric item types.

To explore all table commands and their parameters, run:

```
fab table -h
```

---

## Table Schema Operations

### Check Delta Table Schema

**Items Supporting OneLake Schema:**

- `.Lakehouse`
- `.Warehouse`
- `.MirroredDatabase`
- `.SQLDatabase`
- `.SemanticModel`[^1]
- `.KQLDatabase`[^1]

[^1]: Requires explicit enablement

View the complete schema structure of a Delta table in a Lakehouse.

```
fab table schema ws1.Workspace/lh1.Lakehouse/Tables/dbo/customer_data
```


## Data Loading

!!! info "Not supported in schema-enabled Lakehouses"

### Load CSV Data

#### Load from Folder

Load all CSV files from a folder into a Delta table.

```
fab table load ws1.Workspace/lh1.Lakehouse/Tables/customer_data --file ws1.Workspace/lh1.Lakehouse/Files/csv/customers
```

#### Load Specific File with Append Mode

Load a specific CSV file and append to existing table data.

```
fab table load ws1.Workspace/lh1.Lakehouse/Tables/sales_data --file ws1.Workspace/lh1.Lakehouse/Files/csv/daily_sales.csv --mode append
```

#### Load CSV with Custom Format Options

Load CSV data with specific delimiter and header configuration.

```
fab table load ws1.Workspace/lh1.Lakehouse/Tables/product_catalog --file ws1.Workspace/lh1.Lakehouse/Files/custom_csv --format format=csv,header=false,delimiter=';'
```

### Load Parquet Data

#### Load Parquet Files

Load Parquet files into a Delta table with append mode.

```
fab table load ws1.Workspace/lh1.Lakehouse/Tables/analytics_data --file ws1.Workspace/lh1.Lakehouse/Files/parquet/events --format format=parquet --mode append
```

#### Load with File Extension Filter

Load only specific Parquet files using extension filtering.

```
fab table load ws1.Workspace/lh1.Lakehouse/Tables/processed_data --file ws1.Workspace/lh1.Lakehouse/Files/parquet/processed --format format=parquet --extension '.parquet'
```

## Table Optimization

!!! info "Supported only in Lakehouse"

### Basic Table Optimization

Perform basic Delta table optimization to improve query performance.

```
fab table optimize ws1.Workspace/lh1.Lakehouse/Tables/sales_data
```

### Optimize with V-Order and Z-Order

Run comprehensive optimization with both V-Order and Z-Order for maximum performance.

```
fab table optimize ws1.Workspace/lh1.Lakehouse/Tables/customer_transactions --vorder --zorder customer_id,transaction_date
```


## Vacuum Operations

!!! info "Supported only in Lakehouse"

### Default Vacuum Operation

Remove old files using the default retention period (7 days).

```
fab table vacuum ws1.Workspace/lh1.Lakehouse/Tables/transaction_history
```

### Vacuum with Custom Retention

Specify a custom retention period in hours for more aggressive cleanup.

```
fab table vacuum ws1.Workspace/lh1.Lakehouse/Tables/temp_processing_data --retain_n_hours 48
```
