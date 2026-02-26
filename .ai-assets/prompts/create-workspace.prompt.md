````prompt
# Create a Fabric Workspace

Create a new Microsoft Fabric workspace with specified configuration.

## Required Information

Before proceeding, confirm the following with the user:

- **Workspace name** - The display name for the workspace
- **Capacity** - The Fabric capacity to assign (or use default)

If either is missing, ask for clarification before proceeding.

## Pre-Creation Checklist

1. **Verify authentication**
   ```
   fab auth status
   ```
   If not authenticated, run `fab auth login` first.

2. **List available capacities**
   ```
   fab ls .capacities
   ```
   Note: Users need capacity access to create workspaces on specific capacities.

3. **Check if workspace name exists**
   ```
   fab exists "{workspaceName}.Workspace"
   ```
   Workspace names must be unique within the tenant.

## Create the Workspace

### Basic workspace (default capacity)

```
fab mkdir "{workspaceName}.Workspace"
```

### Workspace on specific capacity

```
fab mkdir "{workspaceName}.Workspace" -P capacityName="{capacityName}"
```

## Post-Creation Validation

1. **Verify workspace was created**
   ```
   fab ls
   ```

2. **Get workspace details**
   ```
   fab get "{workspaceName}.Workspace"
   ```

3. **Retrieve workspace ID** (for further configuration)
   ```
   fab get "{workspaceName}.Workspace" -q "id"
   ```

## Optional Configuration

### Set Large storage format

After creation, configure the workspace to use Large storage format for semantic models:

```
fab api -A powerbi -X patch "groups/{workspaceId}" -i '{"defaultDatasetStorageFormat":"Large"}'
```

### Create initial folder structure

```
fab mkdir "{workspaceName}.Workspace/Development.Folder"
fab mkdir "{workspaceName}.Workspace/Production.Folder"
```

## Safety Guidelines

- Workspace names cannot contain special characters: `< > : " / \ | ? *`
- Workspace names must be unique within the tenant
- Creating a workspace does not automatically assign permissions to other users
- Verify capacity has available resources before creation

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Permission denied | Verify you have capacity assignment rights |
| Name already exists | Choose a different workspace name |
| Capacity not found | Check capacity name with `fab ls .capacities` |
| Authentication failed | Run `fab auth login` to re-authenticate |

## Output

After successful creation, provide:

1. Workspace name and ID
2. Assigned capacity
3. Verification that workspace is accessible

````
