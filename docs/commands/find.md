# `find` Command

Search the Fabric catalog for items across all workspaces.

**Usage:**

```
fab find <query> [-P <params>] [-l] [-q <query>]
```

**Parameters:**

- `<query>`: Search text. Matches display name, description, and workspace name.
- `-P, --params`: Filter parameters in `key=value` or `key!=value` format. Use brackets for multiple values: `type=[Lakehouse,Notebook]`. Use `!=` to exclude: `type!=Dashboard`.
- `-l, --long`: Show detailed table with IDs (name, id, type, workspace, workspace_id, description). Optional.
- `-q, --query`: JMESPath query to filter results client-side. Optional.

**Examples:**

```
# search for items by name or description
fab find 'sales report'

# search for lakehouses only
fab find 'data' -P type=Lakehouse

# search for multiple item types (bracket syntax)
fab find 'dashboard' -P type=[Report,SemanticModel]

# exclude a type
fab find 'data' -P type!=Dashboard

# show detailed output with IDs
fab find 'sales' -l

# combine filters
fab find 'finance' -P type=[Warehouse,Lakehouse] -l

# project specific fields
fab find 'data' -q "[].{name: name, workspace: workspace}"
```

**Behavior:**

- In interactive mode (`fab` shell), results are paged 50 at a time with "Press Enter to continue..." prompts.
- In command-line mode (`fab find ...`), all results are fetched in a single pass (up to 1000 per API call).
- Type names are case-insensitive. `type=lakehouse` matches `Lakehouse`.
- The `-q` JMESPath filter is applied client-side after results are returned from the API.

**Supported filter parameters:**

| Parameter | Description |
|-----------|-------------|
| `type`    | Filter by item type. Supports `eq` (default) and `ne` (`!=`) operators. |

