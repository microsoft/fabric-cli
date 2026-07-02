# `deploy` Command

The `deploy` command imports workspace items from a local source into a target Fabric workspace.

You can deploy:

- all items from the source workspace
- specific folders that contain items
- specific items

**Supported Types:**

- All Fabric workspace item types that support definition import (e.g., `.Notebook`, `.DataPipeline`, `.Report` )

**Usage:**

```bash
fab deploy --config <config_file> [--target_env <environment>] [--params <parameters>] [--force]
```

**Parameters:**

- `--config <file>`: Path to the deployment configuration YAML file. **Required**.
- `--target_env, -tenv <env>`: Environment name used to select environment-specific settings from the configuration file and the parameter file (if present). Optional.
- `--params, -P <params>`: JSON-formatted parameters provided to the deployment process at runtime. Optional.
- `--force, -f`: Run the deployment without interactive confirmation prompts. Optional.

**Example:**

```bash
fab deploy --config config.yml --target_env dev
```

---

### Deployment Behavior

The scope of the deployment, its operations (e.g., publish, unpublish), and settings are defined entirely by the configurations set in a YAML file.

During execution, the command:

- publishes items found in the source into the target workspace
- resolves dependencies between items automatically when logical IDs are present
- unpublishes items from the target workspace that no longer exist in the source

By default, **both publish and unpublish operations are enabled and executed**.  
To disable either operation for a specific environment, it must be explicitly skipped in the configuration file.

The deployment to the Fabric workspaces is executed via the Fabric REST APIs.

---

### Bulk Publish (Experimental)

By default, `deploy` publishes items **one at a time**. You can optionally enable
**bulk publish**, which deploys all items in a **single bulk import API call**.

Enable it with the `--bulk_publish` flag:

```bash
fab deploy --config config.yml --target_env dev --bulk_publish
```

Notes:

- This feature is **experimental** in the underlying [`fabric-cicd`](https://microsoft.github.io/fabric-cicd/latest/how_to/optional_feature/) library and uses its bulk import (beta) API. It may change or fail; omit the `--bulk_publish` flag to use the standard per-item publish behavior.
- It is **disabled by default**, so existing deployments keep the standard per-item publish behavior.
- When enabled, the CLI turns on the required `enable_experimental_features` and `enable_bulk_publish` fabric-cicd feature flags for you.

---

### Configuration Behavior

- The configuration file controls what is published and unpublished.
- Publish and unpublish operations are enabled by default.
- Skipping publish or unpublish must be explicitly defined per environment.
- Target Environment selection is resolved only when environment mappings are present in the configuration.
- If `--target_env` is not specified, the configuration fields must not contain environment-mappings.

---

### Configuration File

#### Minimal Configuration (No Environment Mappings)

```yaml
core:
  workspace_id: "12345678-1234-1234-1234-123456789abc"
  repository_directory: "."
```

#### Configuration Fields

| Field | Description | Mandatory |
|------|------------|-----------|
| `core.workspace_id` | Target workspace ID (GUID). Takes precedence over `workspace`. | ✅ Yes |
| `core.workspace` | Target workspace name. Alternative to `workspace_id`. | ❌ No |
| `core.repository_directory` | Path to local directory containing item files. | ✅ Yes |
| `core.item_types_in_scope` | List of item types included in deployment. | ❌ No |
| `core.parameter` | Path to parameter file. | ❌ No |
| `publish` | Controls publishing behavior. | ❌ No |
| `unpublish` | Controls unpublishing behavior. | ❌ No |
| `features` | Set feature flags. | ❌ No |
| `constants` | Override constant values. | ❌ No |

Relative paths for `repository_directory` and `parameter` fields are resolved relative to the configuration file location.

---

### Publish and Unpublish Settings

#### Publish

```yaml
publish:
  exclude_regex: "^DONT_DEPLOY.*"        # Excludes items matching this pattern from publishing
  folder_exclude_regex: "^/legacy"       # Excludes items under matching folders from publishing (requires feature flags)
  folder_path_to_include:                # Publishes only the specified items under matching folder (requires feature flags)
    - /subfolder_1
  items_to_include:                      # Publishes only the specified items (requires feature flags)
    - "MainNotebook.Notebook"
  skip:                                  # Skips publishing per environment
    dev: true
    test: false
    prod: false
```

#### Unpublish

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

### Parameter File

The parameter file enables environment‑specific transformations by applying targeted replacements within deployed content.

It can be used to:

- replace workspace and item identifiers
- replace connection strings and URLs
- update embedded values inside item definitions
- parameterize environment-specific configuration values

The parameter file is optional and is applied only when specified in the configuration.

When deploying item files that were not created via Git Integration but instead exported (for example, using the Fabric CLI export command), parameterization should be used to resolve dependencies. Otherwise, items will reference the original item.

#### Example

```yaml
find_replace:
  - find_value: "dev-connection-string"
    replace_value:
      dev: "dev-connection-string"
      test: "test-connection-string"
      prod: "prod-connection-string"
```

#### Supported `replace_value` Variables

- `$workspace.$id` — resolves to the target workspace ID
- `$items.<ItemType>.<ItemName>.$id` — resolves to the deployed item ID

Parameterization behavior follows the documented model described here:

https://microsoft.github.io/fabric-cicd/latest/how_to/parameterization

---

### More Examples

#### Deployment to a Specific Environment

```bash
fab deploy --config config.yml --target_env prod
```

#### Deployment with Runtime Parameters

```bash
fab deploy --config config.yml --target_env test -P config_override='{"core":{"item_types_in_scope":["Notebook"]}}'
```

---

### Preparing Source Content

#### Using Git Integration

If the workspace is connected to Git, clone the repository locally:

```bash
git clone <git-repository-url>.git
```

Use the cloned repository as the deployment source.

#### Using `fab export`

`fab export` exports one item at a time and does not include logical IDs.

```bash
fab export  ws.Workspace/MyDataPipeline.DataPipeline -o C:\Users\myuser
```

---

### Additional Notes

- The `deploy` command can be applied to Fabric item files created via Git integration or using the `export` command (utilizes Get Item Definition API).
- `fab deploy` does not require items to be created via Git integration prior to deployment; however, using Git integration is strongly recommended for dependency resolution with minimal parameterization.
- Parameterization is optional and can be applied in any deployment scenario.

---

### Useful Links

- [Fabric CI/CD Library](https://microsoft.github.io/fabric-cicd/latest/)
