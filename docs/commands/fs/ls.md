# `ls` / `dir` Command

List workspaces, items, and files.

!!! info "Listing domains requires tenant-level Fabric Administrator privileges"

**Usage:**

```
fab ls <path> [-l] [-a] [-q <query>]
```

**Parameters:**

- `<path>`: Path to list. Optional.
- `-l, --long`: Show detailed output. Optional.
- `-a, --all`: Show hidden entities. Optional.
- `-q, --query`: JMESPath query to filter results. Optional.

**Examples:**

```
fab ls ws1.Workspace
fab ls -l
fab ls ws1.Workspace -q [].[?contains(name, 'report')]
fab ls -q [].[?type=='Lakehouse']
```