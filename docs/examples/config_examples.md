# Configuration Examples

This page demonstrates how to configure and manage Fabric CLI settings. Configuration allows you to customize the CLI behavior to match your preferences and environment.

To explore all configuration commands and their parameters, run:

```
fab config -h
```

---

## Clear Cache


Clear All CLI Caches

```
fab config clear-cache
```

## Get Single Configuration Value

Retrieve the value for a given configuration key

```
fab config get mode
```

## List Configuration Settings

Retrieve a list of configuration keys and values

```
fab config ls
```

Filter the configuration list using JMESPath

```
fab config ls -q  [?setting=='mode']
```

## Set Configuration Settings

### Enable/Disable Cache

Control whether the CLI caches data for improved performance.

```
fab config set cache_enabled true
```

### Enable/Disable Debug Mode

Control debug output and logging level for troubleshooting.

```
fab config set debug_enabled true
```

### Enable/Disable Encryption Fallback

Allow authentication token cache in plaintext when encryption is unavailable.

```
fab config set encryption_fallback_enabled true
```

### Enable/Disable Job Timeout Behavior

Control whether jobs are cancelled when they timeout.

```
fab config set job_cancel_ontimeout true
```

### Set Labels Definition File

Specify a local file containing label definitions for the CLI.

```
fab config set local_definition_labels /tmp/labels.json
```

### Switch CLI Mode

Set the default interaction mode for the CLI.
**Allowed Values:** `interactive`, `command_line`

```
fab config set mode interactive
```

### Configure Item Sort Order

Set the default sorting criteria for listing items.
**Allowed Values:** `byname`, `bytype`

```
fab config set output_item_sort_criteria bytype
```

### Show Hidden Elements

Control visibility of hidden Fabric elements like virtual elements.

```
fab config set show_hidden true
```

### Set Default Azure Subscription

Configure the default Azure subscription for capacity operations.

```
fab config set default_az_subscription_id 00000000-0000-0000-0000-000000000000
```


### Set Default Resource Group

Configure the default Azure resource group.

```
fab config set default_az_resource_group myresourcegroup
```


### Set Default Azure Location

Configure the default Azure region/location.

```
fab config set default_az_location westeurope
```


### Set Default Fabric Admin

Configure the default Fabric administrator email.

```
fab config set default_az_admin fabcli@microsoft.com
```

### Set Default Capacity

Configure the default Fabric capacity for workspace operations.

```
fab config set default_capacity cap1
```

### Set Default Open Experience

Configure the default experience when opening items in web browser.
**Allowed Values:** `powerbi`, `fabric`

```
fab config set default_open_experience powerbi
```

For complete details on all available configuration settings, see the [Settings documentation](../essentials/settings.md#available-settings).