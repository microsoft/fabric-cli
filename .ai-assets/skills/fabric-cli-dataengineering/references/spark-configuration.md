# Spark Configuration Reference

Guide to managing Spark pools, environments, and configurations in Fabric.

## Spark Pools Overview

Fabric Spark pools provide managed compute for notebooks and jobs:

| Pool Type | Use Case | Configuration |
|-----------|----------|---------------|
| Starter Pool | Development | Pre-warmed, shared |
| Custom Pool | Production | Dedicated, configurable |
| High Concurrency | Multi-user | Session sharing |

## Managing Spark Pools

### List Spark Pools

```bash
# List all Spark pools in workspace
fab ls "Workspace/.sparkpools"

# List with details
fab ls "Workspace/.sparkpools" -l

# Get pool configuration
fab get "Workspace/.sparkpools/MyPool.SparkPool"
```

### Create Spark Pool (via API)

```bash
WS_ID=$(fab get "Workspace" -q "id" | tr -d '"')

fab api -X post "workspaces/$WS_ID/sparkPools" -i '{
  "name": "DataEngineeringPool",
  "nodeFamily": "MemoryOptimized",
  "nodeSize": "Large",
  "autoScale": {
    "enabled": true,
    "minNodeCount": 1,
    "maxNodeCount": 10
  },
  "dynamicExecutorAllocation": {
    "enabled": true,
    "minExecutors": 1,
    "maxExecutors": 8
  }
}'
```

### Update Spark Pool

```bash
# Get pool ID
POOL_ID=$(fab get "Workspace/.sparkpools/MyPool.SparkPool" -q "id" | tr -d '"')

# Update auto-scale settings
fab api -X patch "workspaces/$WS_ID/sparkPools/$POOL_ID" -i '{
  "autoScale": {
    "enabled": true,
    "minNodeCount": 2,
    "maxNodeCount": 20
  }
}'
```

### Delete Spark Pool

```bash
fab api -X delete "workspaces/$WS_ID/sparkPools/$POOL_ID"
```

## Spark Environments

### List Environments

```bash
# List all environments
fab ls "Workspace/.environments"

# Get environment details
fab get "Workspace/.environments/DataEng.SparkEnvironment"
```

### Create Environment

```bash
fab api -X post "workspaces/$WS_ID/items" -i '{
  "displayName": "DataEngEnvironment",
  "type": "SparkEnvironment"
}'
```

### Configure Environment Libraries

```bash
# Get environment ID
ENV_ID=$(fab get "Workspace/.environments/DataEng.SparkEnvironment" -q "id" | tr -d '"')

# Add Python libraries via staging
fab api -X post "workspaces/$WS_ID/environments/$ENV_ID/staging/libraries" -i '{
  "pythonLibraries": {
    "packages": [
      {"name": "pandas", "version": "2.0.0"},
      {"name": "pyarrow", "version": "14.0.0"},
      {"name": "great-expectations", "version": "0.17.0"}
    ]
  }
}'

# Publish environment changes
fab api -X post "workspaces/$WS_ID/environments/$ENV_ID/staging/publish"
```

## Spark Configuration Properties

### Session-Level Configuration

```python
# Configure Spark session in notebook
spark.conf.set("spark.sql.shuffle.partitions", "200")
spark.conf.set("spark.sql.files.maxPartitionBytes", "134217728")
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
spark.conf.set("spark.databricks.delta.autoCompact.enabled", "true")
```

### Common Configuration Properties

| Property | Default | Description |
|----------|---------|-------------|
| `spark.sql.shuffle.partitions` | 200 | Shuffle partition count |
| `spark.sql.files.maxPartitionBytes` | 128 MB | Max partition size |
| `spark.databricks.delta.optimizeWrite.enabled` | false | Auto-optimize writes |
| `spark.databricks.delta.autoCompact.enabled` | false | Auto-compact small files |
| `spark.sql.adaptive.enabled` | true | Adaptive query execution |

### Environment-Level Configuration

```bash
# Add Spark properties to environment
fab api -X post "workspaces/$WS_ID/environments/$ENV_ID/staging/sparkSettings" -i '{
  "sparkProperties": {
    "spark.sql.shuffle.partitions": "400",
    "spark.sql.files.maxPartitionBytes": "268435456",
    "spark.databricks.delta.optimizeWrite.enabled": "true"
  }
}'

# Publish changes
fab api -X post "workspaces/$WS_ID/environments/$ENV_ID/staging/publish"
```

## Pool Sizing Guidelines

### Node Sizes

| Size | Memory | Cores | Use Case |
|------|--------|-------|----------|
| Small | 8 GB | 4 | Development |
| Medium | 16 GB | 8 | Standard workloads |
| Large | 32 GB | 16 | Large datasets |
| X-Large | 64 GB | 32 | Heavy processing |
| XX-Large | 128 GB | 64 | Memory-intensive |

### Right-Sizing Recommendations

```bash
# Check job history for sizing insights
fab job list "Workspace/Notebook" -l

# Review execution metrics
NOTEBOOK_ID=$(fab get "Workspace/Notebook" -q "id" | tr -d '"')
fab api "workspaces/$WS_ID/items/$NOTEBOOK_ID/jobs" -q "value[0].executionData"
```

## Attaching Pools and Environments

### Set Default Pool

```bash
# Update workspace default compute
fab api -X patch "workspaces/$WS_ID/sparkSettings" -i '{
  "defaultPool": {
    "type": "Workspace",
    "name": "DataEngineeringPool"
  }
}'
```

### Attach Environment to Notebook

```bash
# Via notebook definition update
NB_ID=$(fab get "Workspace/Notebook" -q "id" | tr -d '"')

fab api -X patch "workspaces/$WS_ID/items/$NB_ID" -i '{
  "definition": {
    "environmentId": "<env-id>"
  }
}'
```

## Dynamic Resource Allocation

### Enable Dynamic Allocation

```python
# In notebook
spark.conf.set("spark.dynamicAllocation.enabled", "true")
spark.conf.set("spark.dynamicAllocation.minExecutors", "1")
spark.conf.set("spark.dynamicAllocation.maxExecutors", "10")
spark.conf.set("spark.dynamicAllocation.initialExecutors", "2")
```

### Auto-Scale Configuration

```bash
# Create pool with auto-scale
fab api -X post "workspaces/$WS_ID/sparkPools" -i '{
  "name": "AutoScalePool",
  "nodeSize": "Medium",
  "autoScale": {
    "enabled": true,
    "minNodeCount": 1,
    "maxNodeCount": 50
  }
}'
```

## Library Management

### Python Libraries

```bash
# Add PyPI packages
fab api -X post "workspaces/$WS_ID/environments/$ENV_ID/staging/libraries" -i '{
  "pythonLibraries": {
    "packages": [
      {"name": "delta-spark", "version": "3.0.0"},
      {"name": "azure-storage-blob"},
      {"name": "pyspark-test"}
    ]
  }
}'
```

### Custom Wheels

```bash
# Upload custom wheel first
fab cp "./custom_lib-1.0.0-py3-none-any.whl" \
       "Workspace/.environments/MyEnv.SparkEnvironment/libraries/"

# Add to environment
fab api -X post "workspaces/$WS_ID/environments/$ENV_ID/staging/libraries" -i '{
  "pythonLibraries": {
    "wheelFiles": [
      {"path": "abfss://.../.environments/MyEnv/libraries/custom_lib-1.0.0-py3-none-any.whl"}
    ]
  }
}'
```

### JAR Libraries

```bash
# Add Spark/Scala libraries
fab api -X post "workspaces/$WS_ID/environments/$ENV_ID/staging/libraries" -i '{
  "jarLibraries": [
    {"path": "abfss://.../.environments/MyEnv/libraries/custom-udf.jar"}
  ]
}'
```

## Performance Optimization

### Adaptive Query Execution

```python
# Enable AQE features
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256MB")
```

### Broadcast Join Optimization

```python
# Configure broadcast threshold
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "104857600")  # 100 MB

# Force broadcast hint
df = spark.sql("""
    SELECT /*+ BROADCAST(dim_customer) */ 
           f.*, d.customer_name
    FROM fact_sales f
    JOIN dim_customer d ON f.customer_id = d.customer_id
""")
```

### Delta Lake Optimizations

```python
# Enable Delta optimizations
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
spark.conf.set("spark.databricks.delta.autoCompact.enabled", "true")
spark.conf.set("spark.databricks.delta.properties.defaults.enableChangeDataFeed", "true")
```

## Monitoring and Diagnostics

### View Spark UI Metrics

```bash
# Get active sessions
fab api "workspaces/$WS_ID/sparkPools/$POOL_ID/sparkSessions"

# Get session details
fab api "workspaces/$WS_ID/sparkPools/$POOL_ID/sparkSessions/$SESSION_ID/statements"
```

### Job Execution History

```bash
# List recent job runs
fab job list "Workspace/Notebook" -q "[].{status: status, start: startTime, end: endTime}"

# Get specific job details
fab job get "Workspace/Notebook" "<job-id>"
```

## Best Practices

### Development vs Production

| Setting | Development | Production |
|---------|-------------|------------|
| Pool Size | Small/Medium | Large/X-Large |
| Auto-Scale Min | 1 | 2-3 |
| Auto-Scale Max | 5 | 20-50 |
| Shuffle Partitions | 200 | 400-800 |
| Dynamic Allocation | Enabled | Enabled |

### Cost Optimization

- Use starter pools for development
- Enable auto-scale with appropriate min/max
- Configure session timeouts
- Use appropriate node sizes for workload
- Monitor and right-size based on utilization

### Environment Management

- Separate environments by workload type
- Version control environment definitions
- Test library updates in dev first
- Document required dependencies
- Use consistent library versions across environments

## Troubleshooting

### Out of Memory Errors

```python
# Increase driver memory (if available)
spark.conf.set("spark.driver.memory", "16g")

# Reduce partition size
spark.conf.set("spark.sql.files.maxPartitionBytes", "67108864")  # 64 MB

# Increase shuffle partitions
spark.conf.set("spark.sql.shuffle.partitions", "400")
```

### Slow Job Execution

```python
# Check execution plan
df.explain(extended=True)

# Enable AQE if not already
spark.conf.set("spark.sql.adaptive.enabled", "true")

# Check for data skew
df.groupBy("potential_skew_column").count().orderBy(desc("count")).show(10)
```

### Library Conflicts

```bash
# List current environment libraries
fab api "workspaces/$WS_ID/environments/$ENV_ID" -q "properties.libraries"

# Check for conflicts
fab api "workspaces/$WS_ID/environments/$ENV_ID/staging/libraries/conflicts"
```
