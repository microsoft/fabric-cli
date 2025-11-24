# Configuration Commands

The `config` commands manage settings that control CLI behavior, authentication, and preferences.

**Supported Types:**

Not resource-specific; applies to CLI environment.

## Available Commands

| Command           | Description                | Usage                           |
|-------------------|---------------------------|---------------------------------|
| `config ls` (dir) | List all configurations   | `config ls`                     |
| `config get`      | Get a configuration value | `config get <key>`              |
| `config set`      | Set a configuration value | `config set <key> <value>`      |
| `config clear-cache` | Clear the CLI cache    | `config clear-cache`            |

---

### ls (dir)

List all configuration settings and their current values.

**Usage:**

```
fab config ls
```

---

### get

Get the value of a specific configuration setting.

**Usage:**

```
fab config get <key>
```

**Examples:**

```
fab config get mode
fab config get local_definition_labels
fab config get encryption_fallback_enabled
```

---

### set

Set or update a configuration value.

**Usage:**

```
fab config set <key> <value>
```

**Examples:**

```py
# Change CLI mode
fab config set mode command_line

# Set label definitions path
fab config set local_definition_labels /path/to/labels.json

# Enable encryption fallback
fab config set encryption_fallback_enabled true
```

---

### clear-cache

Clear cached CLI data.

**Usage:**

```
fab config clear-cache
```

---

For more examples and detailed scenarios, see [Configuration Examples](../../examples/config_examples.md).
