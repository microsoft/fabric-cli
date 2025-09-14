# `start` Command

Start a resource.

**Supported Types:**

- `.Capacity`
- `.MirroredDatabase`

**Usage:**

```
fab start <path> [-f]
```

**Parameters:**

- `<path>`: Path to the resource.
- `-f, --force`: Force start without confirmation. Optional.

**Example:**

```
fab start ws1.Workspace/nb1.Notebook
```
