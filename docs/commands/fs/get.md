# `get` Command

Get a workspace or item property.

!!! info "Getting domain details requires tenant-level Fabric Administrator privileges"

!!! warning "When retrieving an item definition, it is retrieved without its sensitivity label"

**Usage:**

```
fab get <path> [-q <jmespath_query>] [-o <output_path>] [-v] [-f]
```

**Parameters:**

- `<path>`: Path to the resource.
- `-q, --query <jmespath_query>`: JMESPath query to filter (use `.` for complete object). Optional.
- `-o, --output <output_path>`: Output directory path. Optional.
- `-v, --verbose`: Show all properties. Optional.
- `-f, --force`: Force item's definition retrieval without confirmation. Optional.

**Example:**

```
fab get ws1.Workspace -q .
```
