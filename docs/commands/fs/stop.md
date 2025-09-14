# `stop` Command

Stop a resource.

**Supported Types:**

- `.Capacity`
- `.MirroredDatabase`

**Usage:**

```
fab stop <path> [-f]
```

**Parameters:**

- `<path>`: Path to the resource.
- `-f, --force`: Force stop without confirmation. Optional.

**Example:**

```
fab stop ws1.Workspace/nb1.Notebook
```

