# Migrate Items Between Workspaces

Migrate items from **${input:sourceWorkspace}** to **${input:targetWorkspace}**.

## Pre-Migration Assessment

### 1. Verify Source Items
```
fab ls {sourceWorkspace}.Workspace
```

### 2. Check Target Workspace
```
fab ls {targetWorkspace}.Workspace
```

### 3. Verify Permissions
Source (need read):
```
fab acls ls {sourceWorkspace}.Workspace
```

Target (need write):
```
fab acls ls {targetWorkspace}.Workspace
```

## Migration Strategy

### Option 1: Item-by-Item Migration
Copy individual items:
```
fab cp {sourceWorkspace}.Workspace/{itemName}.{ItemType} {targetWorkspace}.Workspace/ -f
```

### Option 2: Export/Import Pattern
Export from source, then import to target:
```
# Export
fab export {sourceWorkspace}.Workspace/{itemName}.{ItemType} -o ./migration -f

# Import
fab import {targetWorkspace}.Workspace/{itemName}.{ItemType} -i ./migration/{itemName}.{ItemType} -f
```

## Migration Order (Dependencies)

Follow this order to maintain dependencies:

1. **Lakehouses** - Data foundation
2. **Semantic Models** - Depend on Lakehouses
3. **Reports** - Depend on Semantic Models
4. **Pipelines** - May reference other items
5. **Notebooks** - Usually independent

## Post-Migration Validation

### 1. Verify Items Copied
```
fab ls {targetWorkspace}.Workspace
```

### 2. Compare Source and Target
List both workspaces and compare item counts manually:
```
fab ls {sourceWorkspace}.Workspace
fab ls {targetWorkspace}.Workspace
```

### 3. Test Key Items
Get details of critical items to verify:
```
fab get {targetWorkspace}.Workspace/{keyModel}.SemanticModel
```

### 4. Test Refresh
Trigger refresh on migrated items:
```
fab job run {targetWorkspace}.Workspace/{keyModel}.SemanticModel
```

## Connection Updates

After migration, update data source connections if needed:
- Lakehouses may need shortcut updates
- Semantic Models may need connection rebinding
- Pipelines may need parameter updates

## Rollback Plan

If migration fails:
1. Document which items successfully migrated
2. Delete failed items in target: `fab rm {targetWorkspace}.Workspace/{itemName}.{ItemType} -f`
3. Re-attempt migration for failed items
4. Source workspace remains unchanged (copy doesn't delete)

## Migration Checklist

- [ ] Backup target workspace inventory (if items exist)
- [ ] Verify source access
- [ ] Verify target access
- [ ] Copy items in dependency order
- [ ] Validate item counts match
- [ ] Test refresh on semantic models
- [ ] Test reports open correctly
- [ ] Update connections if needed
- [ ] Update ACLs if needed
- [ ] Notify users of new workspace location
