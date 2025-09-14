# `desc` Command

The `desc` command provides detailed descriptions and information about CLI commands and elements.

For a full list, see [Resource Types](../../essentials/resource_types.md).

## Available Commands

| Command | Description           | Usage              |
|---------|----------------------|--------------------|
| `desc`  | Check command support| `fab desc <path>`  |

---

### desc

Check command support for a resource type or path.

**Usage:**

```
fab desc <path>
```

**Parameters:**

- `<path>`: Resource type (e.g., `.Notebook`) or path to an existing resource.

**Examples:**

```
fab desc .Capacity
fab desc .capacities/capac1.Capacity
```