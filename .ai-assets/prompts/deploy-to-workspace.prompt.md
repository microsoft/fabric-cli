# Deploy Items to Target Workspace

Deploy Fabric items from **${input:sourceWorkspace}** to **${input:targetWorkspace}**.

## Pre-Deployment Checklist

Before deploying, verify:

1. **Authentication** - Confirm `fab auth status` shows valid credentials
2. **Source exists** - List items in source workspace to confirm what to deploy
3. **Target access** - Verify write permissions on target workspace
4. **Item conflicts** - Check if items already exist in target (will be overwritten)

## Deployment Steps

1. First, list items in the source workspace:
   ```
   fab ls {sourceWorkspace}.Workspace
   ```

2. For each item to deploy, use copy command:
   ```
   fab cp {sourceWorkspace}.Workspace/{itemName}.{ItemType} {targetWorkspace}.Workspace/ -f
   ```

3. Verify deployment by listing target workspace:
   ```
   fab ls {targetWorkspace}.Workspace
   ```

## Safety Guidelines

- **Never deploy to production without testing first**
- Copy commands OVERWRITE existing items with same name
- Use `-f` flag for non-interactive execution
- For large deployments, deploy in batches and verify each

## Common Item Types

- `.SemanticModel` - Power BI datasets
- `.Report` - Power BI reports  
- `.Notebook` - Spark notebooks
- `.Lakehouse` - Lakehouse definitions
- `.DataPipeline` - Data pipelines
- `.Warehouse` - SQL warehouses

## Rollback Strategy

If deployment fails:
1. Check item status with `fab get {targetWorkspace}.Workspace/{itemName}.{ItemType}`
2. Items can be re-deployed from source
3. Consider keeping backups via `fab export` before deployment
