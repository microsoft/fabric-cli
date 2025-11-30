# `set` Command

Set a resource property.

**Supported Resource Types:**

- Workspace
- Item
- Capacity
- Domain
- Connection
- Gateway
- Spark Pool
- Folder
- Shortcut

!!! info "Setting domain properties requires tenant-level Fabric Administrator privileges"

!!! warning "When setting an item definition, it is set without its sensitivity label"

**Usage:**

```
fab set <path> -q <jmespath_query> -i <input_value> [-f]
```

**Parameters:**

- `<path>`: Path to the resource.
- `-q, --query <jmespath_query>`: JMESPath query to the property.
- `-i, --input <input_value>`: Input value to set.
    
    !!! tip "Working with JSON input"
        For guidance on providing JSON input values across different shells, see [JSON Input Handling](../../essentials/input.md#json-input-handling).

- `-f, --force`: Force set without confirmation. Optional.

**Example:**

```bash
fab set ws1.Workspace -q displayName -i "New Name" -f
```

## Limitations

- Only one property path can be specified per `--query` argument
- Paths must map directly to JSON paths **without** filters or wildcards
- If the property path doesn't exist on the item definition, it will be added, provided it's valid according to the item's schema. The `set` command supports creation of 1 level at a time (e.g., to set `a.b.c`, first set `a.b`, then set `a.b.c`)
- Properties that expect a JSON string value are not supported - JSON input is always parsed as an object

## Query Support

The following table shows supported queries per resource type:

| Resource | Supported Queries |
|----------------|-------------------|
| **Item** | `displayName`, `description`, `properties` (`.VariableLibrary` only), [`definition.<path>`](#definition-paths) |
| **Workspace** | `displayName`, `description`, `sparkSettings` |
| **Capacity** | `sku.name` |
| **Domain** | `displayName`, `description`, `contributorsScope` |
| **Connection** | `displayName`, `privacyLevel`, `credentialDetails` |
| **Gateway** | `displayName`, `allowCloudConnectionRefresh`, `allowCustomConnectors`, `capacityId`, `inactivityMinutesBeforeSleep`, `numberOfMemberGateways` |
| **Spark Pool** | `name`, `nodeSize`, `autoScale.enabled`, `autoScale.minNodeCount`, `autoScale.maxNodeCount` |
| **Folder** | `displayName` |
| **Shortcut** | `name`, `target` |

<a id="definition-paths"></a>
!!! note "Setting Item Definition Properties"
    For **Items**, you can set any explicit path within the `definition` structure using dot notation for nested properties. The `<path>` placeholder represents any valid property path within your item's definition structure.
    
    **Examples:**
    
    - `definition.parts[0].name`
    - `definition.someProperty.nestedValue`
    - `definition.config.settings`
    
    Paths must map directly to JSON paths **without** filters or wildcards. Refer to the [Microsoft Fabric item definitions](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions) for the complete definition structure.

#### Item-Specific Definition Path Aliasing

!!! warning "Note on definition path aliases"

    These definition path aliases may be deprecated in a future release. We strongly recommend using explicit JSON paths within the item's definition structure rather than aliases.

These are definition path aliases that map to specific paths in the item's definition structure. When using the `set` command, you can use these aliases directly (as the `-query` / `--q` argument value) as they map to the correct definition paths:

| Item Type | Definition Path Alias | Notes |
|-----------|----------------|-------|
| **Notebook** | `lakehouse`, `environment`, `warehouse` | |
| **Report** | `semanticModelId` | Applies only to [Report definition.pbir version 1](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report?tabs=v1%2Cdesktop#definitionpbir). For other versions, check the correct property path in the Report definition documentation |
| **SparkJobDefinition** | `payload` | |