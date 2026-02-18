# Create Lakehouse Pipeline

Create a data pipeline to load data into lakehouse **${input:lakehouseName}** in workspace **${input:workspaceName}**.

## Prerequisites Check

### 1. Verify Lakehouse Exists
```
fab exists {workspaceName}.Workspace/{lakehouseName}.Lakehouse
```

If lakehouse doesn't exist, create it via API:
```
fab api POST workspaces/{workspaceId}/items -b '{"type": "Lakehouse", "displayName": "{lakehouseName}"}'
```

### 2. Verify Workspace Context
```
fab cd {workspaceName}.Workspace
fab ls
```

## Pipeline Creation Options

### Option A: Create Pipeline via API

Create a new Data Pipeline:
```
fab api POST workspaces/{workspaceId}/items -b '{
  "type": "DataPipeline", 
  "displayName": "{pipelineName}",
  "description": "Pipeline to load {lakehouseName}"
}'
```

### Option B: Import Existing Pipeline Definition

If you have a pipeline definition file:
```
fab import {workspaceName}.Workspace/{pipelineName}.DataPipeline -i ./pipeline-definition -f
```

## Common Pipeline Patterns

### Pattern 1: Copy Activity (Source → Lakehouse)
- Use Copy activity to move data from external source
- Configure source connection (SQL, Azure Blob, etc.)
- Set destination to Lakehouse Tables folder

### Pattern 2: Dataflow Gen2
- Create Dataflow Gen2 for transformations
- Output to Lakehouse tables
- Schedule via Pipeline

### Pattern 3: Notebook Activity
- Use Notebook activity for Spark transformations
- Read from Files, write to Tables
- Pass parameters from Pipeline

## Data Loading Best Practices

1. **Use Delta format** - Lakehouse tables use Delta Lake
2. **Partition large tables** - By date or key columns
3. **Incremental loads** - Use watermarks for efficiency
4. **Error handling** - Configure retry policies

## Shortcuts for External Data

Create shortcuts to external data without copying:
```
fab ln {externalPath} {workspaceName}.Workspace/{lakehouseName}.Lakehouse/Files/{shortcutName}
```

## Verify Pipeline

Get pipeline details:
```
fab get {workspaceName}.Workspace/{pipelineName}.DataPipeline
```

## Run and Monitor

Trigger pipeline run:
```
fab job run {workspaceName}.Workspace/{pipelineName}.DataPipeline
```

Monitor execution:
```
fab job run-list {workspaceName}.Workspace/{pipelineName}.DataPipeline
```
