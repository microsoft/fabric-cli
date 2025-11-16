# `ls` / `dir` Command

List workspaces, items, and files.

!!! info "Listing domains requires tenant-level Fabric Administrator privileges"

**Usage:**

```
fab ls <path> [-l] [-a] [-q QUERY]
```

**Parameters:**

- `<path>`: Path to list. Optional.
- `-l, --long`: Show detailed output. Optional.
- `-a, --all`: Show hidden entities. Optional.
- `-q, --query QUERY`: JMESPath query to filter and project fields in output. Optional.

**Examples:**

```
# List basic workspace info
fab ls ws1.Workspace

# Project single field using array projection
fab ls -q "[*].name"

# Project multiple fields using array syntax
fab ls -q [].[name, capacityName]

# Project and rename fields using object syntax
fab ls -q [].{displayName: name, capacity: capacityName}

# Filter and project fields in a workspace
fab ls ws1.Workspace -q [].[?type=='Notebook'].{name: name, id: id}

# Show detailed output with specific fields
fab ls -l -q [].[name, id, capacityName]
```

**Notes:**

- The `-q` parameter accepts JMESPath query expressions (https://jmespath.org)
- Array projection `[*].field` returns an array of values
- Array syntax `[].[field1, field2]` selects multiple fields
- Object syntax `[].{newName: field}` renames fields in output
- Filter expressions `[].[?field=='value']` filter results
- To project detailed output use `-l` flag