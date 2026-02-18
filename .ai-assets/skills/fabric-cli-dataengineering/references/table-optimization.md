# Table Optimization Reference

Guide to Delta Lake table optimization in Fabric using CLI.

## Optimization Fundamentals

Delta Lake tables in Fabric support advanced optimization:

| Feature | Purpose | When to Use |
|---------|---------|-------------|
| OPTIMIZE | Compact small files | After many small writes |
| V-Order | Read optimization | Always for analytics |
| Z-Order | Cluster by columns | Multi-column filtering |
| VACUUM | Remove old versions | After maintenance windows |

## Running Table Maintenance

### Via Notebook Jobs

```bash
# Trigger optimization via Spark notebook
NOTEBOOK_ID=$(fab get "Workspace/Maintenance.Notebook" -q "id" | tr -d '"')

fab job run "Workspace/Maintenance.Notebook" --timeout 3600
```

### Notebook Content for Optimization

```python
# Maintenance notebook template
from delta.tables import DeltaTable

def optimize_table(lakehouse_name, table_name, z_order_cols=None):
    """Run OPTIMIZE with optional Z-Order"""
    spark.sql(f"USE {lakehouse_name}")
    
    if z_order_cols:
        cols = ", ".join(z_order_cols)
        spark.sql(f"OPTIMIZE {table_name} ZORDER BY ({cols})")
    else:
        spark.sql(f"OPTIMIZE {table_name}")
    
    print(f"Optimized {table_name}")

def vacuum_table(lakehouse_name, table_name, hours=168):
    """Remove old versions (default 7 days)"""
    spark.sql(f"USE {lakehouse_name}")
    spark.sql(f"VACUUM {table_name} RETAIN {hours} HOURS")
    print(f"Vacuumed {table_name}")

# Execute maintenance
tables = [
    ("Bronze_LH", "raw_orders", None),
    ("Silver_LH", "clean_orders", ["order_date"]),
    ("Gold_LH", "sales_summary", ["region", "order_date"])
]

for lh, table, z_cols in tables:
    optimize_table(lh, table, z_cols)
    vacuum_table(lh, table)
```

## V-Order Optimization

V-Order is Fabric's default write optimization:

### Enable V-Order (Default)

V-Order is enabled by default in Fabric lakehouses:

```python
# V-Order is automatic for Delta writes
df.write.format("delta").mode("overwrite").save("Tables/optimized_table")

# Check V-Order status in table properties
spark.sql("DESCRIBE EXTENDED table_name").filter("col_name == 'Table Properties'").show(truncate=False)
```

### V-Order Benefits

- 15% average compression improvement
- Up to 50% faster reads for Power BI
- Automatic during write operations
- No additional configuration needed

## Z-Order Optimization

### Single Column Z-Order

```python
# Z-Order by frequently filtered column
spark.sql("""
    OPTIMIZE Gold_LH.fact_sales
    ZORDER BY (order_date)
""")
```

### Multi-Column Z-Order

```python
# Z-Order by multiple columns (max 4 recommended)
spark.sql("""
    OPTIMIZE Gold_LH.fact_sales
    ZORDER BY (region, order_date)
""")
```

### When to Use Z-Order

| Use Z-Order When | Avoid Z-Order When |
|------------------|-------------------|
| Point lookups on columns | Full table scans |
| Range queries | Few distinct values |
| Join key columns | Frequently changing data |
| Filter predicates | High cardinality only |

## File Compaction

### Standard Compaction

```python
# Compact small files
spark.sql("OPTIMIZE lakehouse.table_name")

# View file statistics before/after
spark.sql("""
    DESCRIBE DETAIL lakehouse.table_name
""").select("numFiles", "sizeInBytes").show()
```

### Partition-Level Compaction

```python
# Optimize specific partition
spark.sql("""
    OPTIMIZE lakehouse.fact_sales
    WHERE order_date >= '2024-01-01'
""")
```

## VACUUM Operations

### Standard VACUUM

```python
# Remove files older than 7 days (default)
spark.sql("VACUUM lakehouse.table_name")

# Specify retention period
spark.sql("VACUUM lakehouse.table_name RETAIN 168 HOURS")
```

### Dry Run VACUUM

```python
# Preview files to be deleted
spark.sql("VACUUM lakehouse.table_name DRY RUN")
```

### VACUUM Considerations

- Default retention: 7 days (168 hours)
- Minimum retention: 0 hours (not recommended)
- Time travel disabled after VACUUM
- Run during low-activity periods

## Automated Maintenance

### Schedule via Pipeline

```bash
# Create pipeline with maintenance activities
fab import -p "Workspace" \
  -d ".ai-assets/templates/maintenance_pipeline.json" \
  -t Pipeline

# Schedule the pipeline
fab api -X post "workspaces/$WS_ID/items/$PIPE_ID/schedules" -i '{
  "enabled": true,
  "configuration": {
    "type": "Daily",
    "startTime": "2024-01-01T02:00:00",
    "timeZone": "UTC",
    "weekdays": ["Sunday"]
  }
}'
```

### Maintenance Script

```bash
#!/bin/bash
# Weekly table maintenance automation

WORKSPACE="DataPlatform.Workspace"
MAINTENANCE_NOTEBOOK="Maintenance.Notebook"

# Run maintenance notebook
echo "Starting weekly maintenance..."
fab job run "$WORKSPACE/$MAINTENANCE_NOTEBOOK" --timeout 7200

# Monitor job completion
JOB_ID=$(fab job list "$WORKSPACE/$MAINTENANCE_NOTEBOOK" -q "[0].id" | tr -d '"')
STATUS=$(fab job get "$WORKSPACE/$MAINTENANCE_NOTEBOOK" "$JOB_ID" -q "status")

while [[ "$STATUS" == "InProgress" || "$STATUS" == "NotStarted" ]]; do
  sleep 60
  STATUS=$(fab job get "$WORKSPACE/$MAINTENANCE_NOTEBOOK" "$JOB_ID" -q "status")
  echo "Status: $STATUS"
done

echo "Maintenance completed with status: $STATUS"
```

## Table Statistics

### Analyze Table Statistics

```python
# Update table statistics
spark.sql("ANALYZE TABLE lakehouse.table_name COMPUTE STATISTICS")

# Update statistics for specific columns
spark.sql("""
    ANALYZE TABLE lakehouse.table_name
    COMPUTE STATISTICS FOR COLUMNS col1, col2, col3
""")
```

### View Statistics

```python
# View table details including statistics
spark.sql("DESCRIBE EXTENDED lakehouse.table_name").show(truncate=False)

# View column statistics
spark.sql("DESCRIBE EXTENDED lakehouse.table_name column_name").show()
```

## Best Practices

### Optimization Schedule

| Layer | Frequency | Operations |
|-------|-----------|------------|
| Bronze | Weekly | OPTIMIZE, VACUUM |
| Silver | Weekly | OPTIMIZE, VACUUM |
| Gold | Daily | OPTIMIZE, VACUUM |
| Aggregate | Daily | OPTIMIZE |

### File Size Targets

- Target file size: 128 MB - 1 GB
- Small file threshold: < 64 MB
- Large file threshold: > 2 GB
- Compaction reduces file count

### Z-Order Selection

```python
# Profile queries to identify Z-Order candidates
# Good candidates: frequently filtered columns
z_order_candidates = {
    "fact_sales": ["customer_id", "order_date"],
    "fact_inventory": ["product_id", "warehouse_id"],
    "dim_customer": ["customer_segment", "region"]
}
```

## Monitoring Table Health

### Check File Distribution

```python
# View file statistics
df = spark.sql("DESCRIBE DETAIL lakehouse.table_name")
df.select(
    "name",
    "numFiles",
    "sizeInBytes",
    "lastModified"
).show()

# Calculate average file size
df.selectExpr(
    "numFiles",
    "sizeInBytes",
    "sizeInBytes / numFiles as avgFileSize"
).show()
```

### History and Auditing

```python
# View table history
spark.sql("DESCRIBE HISTORY lakehouse.table_name LIMIT 20").show(truncate=False)

# View operations timeline
spark.sql("""
    DESCRIBE HISTORY lakehouse.table_name
""").select("version", "timestamp", "operation", "operationMetrics").show()
```

## Troubleshooting

### Small File Problem

```python
# Identify small file issue
stats = spark.sql("DESCRIBE DETAIL lakehouse.table_name")
avg_size = stats.select("sizeInBytes").first()[0] / stats.select("numFiles").first()[0]

if avg_size < 64 * 1024 * 1024:  # < 64 MB
    print("Small file issue detected - run OPTIMIZE")
    spark.sql("OPTIMIZE lakehouse.table_name")
```

### Slow Queries After VACUUM

```python
# Rebuild statistics after VACUUM
spark.sql("ANALYZE TABLE lakehouse.table_name COMPUTE STATISTICS")

# Re-optimize if needed
spark.sql("OPTIMIZE lakehouse.table_name")
```

### Z-Order Not Effective

```python
# Check if Z-Order columns match query patterns
# Verify column cardinality
spark.sql("""
    SELECT 
        COUNT(DISTINCT z_order_col) as cardinality,
        COUNT(*) as total_rows
    FROM lakehouse.table_name
""").show()

# High cardinality (>1000 distinct) benefits more from Z-Order
```
