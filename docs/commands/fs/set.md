# `set` Command

Set a workspace or item property.

!!! info "Setting domain properties requires tenant-level Fabric Administrator privileges"

!!! warning "When setting an item definition, it is set without its sensitivity label"

**Usage:**

```
fab set <path> -q <jmespath_query> -i <input_to_replace> [-f]
```

**Parameters:**

- `<path>`: Path to the resource.
- `-q, --query <jmespath_query>`: JMESPath query.
- `-i, --input <input_to_replace>`: Input value to replace.
- `-f, --force`: Force set without confirmation. Optional.

**Example:**

```
fab set ws1.Workspace/nb1.Notebook -q .property -i value
```