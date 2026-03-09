# `deploy` Command

Deploy a Fabric workspace from local source content into a target Microsoft Fabric workspace.

---

## Description

The `deploy` command imports workspace content from a local source into a target Fabric workspace.

You can deploy:
- an entire workspace
- specific folders
- specific items

The scope and behavior of the deployment are defined entirely by the deployment configuration file.

During execution, the command:
- publishes items found in the source into the target workspace
- resolves dependencies between items automatically when logical IDs are present
- removes items from the target workspace that no longer exist in the source (unpublish)

By default, **both publish and unpublish operations are enabled and executed**.  
To disable either operation for a specific environment, it must be explicitly skipped in the configuration file.

The deployment is executed directly against Fabric workspaces using Fabric APIs.

---

## Usage

```bash
fab deploy --config <config_file> [--target_env <environment>] [--params <parameters>] [--force]
```

---

## Options

| Option | Description |
|------|-------------|
| `--config <file>` | Path to the deployment configuration file. **Required**. |
| `--target_env, -tenv <env>` | Environment name used to select environment-specific settings from the configuration file. |
| `--params, -P <params>` | JSON-formatted parameters provided to the deployment process at runtime. |
| `--force, -f` | Run the deployment without interactive confirmation prompts. |
| `--help` | Show detailed help for the `deploy` command. |

---

## Configuration Behavior

- The configuration file controls what is published and unpublished.
- Publish and unpublish operations are enabled by default.
- Skipping publish or unpublish must be explicitly defined per environment.
- Environment selection is resolved only when environment mappings are present in the configuration.
- If `--target_env` is not specified, the configuration must not contain environment-specific mappings.

---

## Configuration File

### Minimal Configuration (No Environments)

```yaml
core:
  workspace_id: "12345678-1234-1234-1234-123456789abc"
  repository_directory: "."
```

---

### Configuration Fields

| Field | Description | Mandatory |
|------|------------|-----------|
| `core.workspace_id` | Target workspace ID (GUID). Takes precedence over `workspace`. | ✅ Yes |
| `core.workspace` | Target workspace name. Alternative to `workspace_id`. | ❌ No |
| `core.repository_directory` | Path to local directory containing workspace content. | ✅ Yes |
| `core.item_types_in_scope` | List of item types included in deployment. | ❌ No |
| `core.parameter` | Path to parameter file. | ❌ No |
| `publish` | Controls publishing behavior. | ❌ No |
| `unpublish` | Controls unpublishing behavior. | ❌ No |
| `features` | Feature flags. | ❌ No |
| `constants` | API constant overrides. | ❌ No |

Relative paths are resolved relative to the configuration file location.

---

## Publish and Unpublish Settings

### Publish

```yaml
publish:
  exclude_regex: "^DONT_DEPLOY.*"        # Excludes items matching this pattern from publishing
  folder_exclude_regex: "^legacy/"       # Excludes items under matching folders from publishing
  items_to_include:                      # Publishes only the specified items (requires feature flags)
    - "MainNotebook.Notebook"
  skip:                                  # Skips publishing per environment
    dev: true
    test: false
    prod: false
```

### Unpublish

```yaml
unpublish:
  exclude_regex: "^DEBUG.*"              # Prevents matching items from being removed
  items_to_include:                      # Unpublishes only the specified items (requires feature flags)
    - "OldPipeline.DataPipeline"
  skip:                                  # Skips unpublishing per environment
    dev: true
    test: false
    prod: false
```

> **Note**  
> While selective deployment is supported, it is not recommended due to potential issues with dependency management. Use selective deployment options with caution.

---

## Parameter File

The parameter file enables environment-specific transformation of deployed content.

It can be used to:
- replace workspace and item identifiers
- replace connection strings and URLs
- update embedded values inside item definitions
- parameterize environment-specific configuration values

The parameter file is optional and is applied only when specified in the configuration.

When items were exported or created using Fabric CLI (and not through Git integration), dependencies must be explicitly defined in the parameter file to ensure correct resolution during deployment.

### Example

```yaml
find_replace:
  - find_value: "dev-connection-string"
    replace_value:
      dev: "dev-connection-string"
      test: "test-connection-string"
      prod: "prod-connection-string"
```

### Supported Variables

- `$workspace.$id` — resolves to the target workspace ID
- `$items.<ItemType>.<ItemName>.$id` — resolves to the deployed item ID

Parameterization behavior follows the documented model described here:

https://microsoft.github.io/fabric-cicd/0.1.3/how_to/parameterization/add

---

## Examples

### Basic Deployment

```bash
fab deploy --config config.yml
```

### Deployment to a Specific Environment

```bash
fab deploy --config config.yml --target_env prod
```

### Deployment with Runtime Parameters

```bash
fab deploy --config config.yml --target_env test   -P '{"core":{"item_types_in_scope":["Notebook"]}}'
```

---

## Preparing Source Content

### Using Git Integration

If the workspace is connected to Git, clone the repository locally:

```bash
git clone https://github.com/org/fabric-workspace.git
```

Use the cloned repository as the deployment source.

---

### Using `fab export`

`fab export` exports one item at a time and does not include logical IDs.

```bash
fab export --output ./path-to-ws MyDataPipeline.DataPipeline --format .py 
```

To export Notebook items use the `--format .py` option.

```bash
fab export --output ./path-to-ws MyNotebook.Notebook --format .py 
```

---

## Notes

- `fab deploy` does not require Git integration; however, using Git integration is strongly recommended to ensure dependencies.
- The deploy command supports content sourced from Git repositories, locally exported items, and items created locally.
- Specifying a target environment is optional. If --target_env is provided, only values for that environment are applied. If environment‑specific values exist in the configuration, --target_env is required.
- Parameter files are optional and apply to all deployment scenarios.

---

## Related Commands

- `export` — Export individual items from a workspace
- `import` — Import individual items into a workspace
