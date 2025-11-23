# `set` Command

Set a workspace or item property.

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

## Set Item Support

### Input

When providing JSON input in command-line mode, different shells process quotes and escape characters before passing them to the CLI.


**Best Practice:** Surround JSON input with single quotes (`'`). Some shells may require escaping inner double quotes with backslashes (`\"`)

=== "Bash/Zsh"
    ```bash
    fab set item.Resource -q query -i '{"key":"value"}'
    ```

=== "PowerShell"
    ```powershell
    fab set item.Resource -q query -i '{\"key\":\"value\"}'
    ```

### Query

The following queries are supported:

#### Item Metadata

- `displayName` - The display name of the item (all item types)
- `description` - The description of the item (all item types)
- `properties` - Custom properties (`.VariableLibrary` only)

#### Item Definition

- Any explicit path to properties within the item's `definition` structure according to [Microsoft Fabric item definitions](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions).

#### Item-Specific Definition Property Path Name

These are friendly names that map to specific paths in the item's definition structure. When using the `set` command, you can use these names directly (as the `-query` / `--q` argument value) as they map to the correct definition paths:

- **Notebook**: `lakehouse`, `environment`, `warehouse`
- **Report**: `semanticModelId` (applies only to [Report definition.pbir version 1](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report?tabs=v1%2Cdesktop#definitionpbir). For other versions, check the correct property path in the Report definition documentation)
- **SparkJobDefinition**: `payload`

!!! warning "Note on friendly names"

    These friendly names may be deprecated in a future release. We strongly recommend using explicit JSON paths within the item's definition structure according to [Microsoft Fabric item definitions](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions) rather than friendly names.

