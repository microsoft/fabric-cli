# Workspace Examples

This page demonstrates how to manage Microsoft Fabric workspaces using the CLI. Workspaces are containers for Fabric items and provide collaboration and security boundaries.

!!! note "Resource Type"
    Type: `.Workspace`

To explore all workspace commands and their parameters, run:

```
fab desc .Workspace
```

---

## Navigation

Navigate to a workspace using the full workspace path.

```
fab cd /ws1.Workspace
```

Navigate to a workspace using relative path from current context.

```
fab cd ../../ws1.Workspace
```

Navigate to your personal workspace using the workspace name or shortcut.

```
# Using workspace name
fab cd "My workspace.Personal"

# Using shortcut
fab cd ~
```

## Workspace Management


### Create Workspace

Create a workspace. Use `-P capacityName=<capacity name>` to specify inline capacity (default: CLI-configured capacity config set default_capacity <>).

#### Create with Default Capacity

Create a workspace using the CLI-configured default capacity.

```
fab create ws1.Workspace
```

#### Create with Specific Capacity

Create a workspace and assign it to a specific capacity.

```
fab create ws1.Workspace -P capacityname=capac1
```

#### Create Without Capacity

Create a workspace without assigning it to any capacity.

```
fab create ws1.Workspace -P capacityname=none
```


### Check Workspace Existence

Check if a workspace exists and is accessible.

```
fab exists ws1.Workspace
```

### Get Workspace

#### Get Workspace Details

Retrieve full workspace details.

```
fab get ws1.Workspace
```

#### Query Specific Properties

Query workspace properties using JMESPath syntax.

```
fab get ws1.Workspace -q id
```

#### Export Query Results

Save query results to a local file.

```
fab get ws1.Workspace -q sparkSettings -o /tmp
```


### List Workspaces and Folders

#### List All Workspaces and Folders

Display available workspaces with different detail levels.

```
# Simple list
fab ls

# Detailed list
fab ls -l

# Include hidden elements
fab ls -l -a
```

**Hidden elements at tenant level include:**

- [Capacities](./capacity_examples.md) (`.capacities`)
- [Connections](./connection_examples.md) (`.connections`) 
- [Domains](./domain_examples.md) (`.domains`)
- [Gateways](./gateway_examples.md) (`.gateways`)

#### List Workspace Items

Display items within a specific workspace.

```
# Simple list
fab ls ws1.Workspace

# Detailed list
fab ls ws1.Workspace -l

# Include hidden workspace elements
fab ls ws1.Workspace -la
```

**Hidden elements at workspace level include:**

- [External Data Shares](./externaldatashare_examples.md) (`.ExternalDataShare`)
- [Managed Identities](./managedidentity_examples.md) (`.ManagedIdentity`)
- [Managed Private Endpoints](./managedprivateendpoint_examples.md) (`.ManagedPrivateEndpoint`)
- [Spark Pools](./sparkpool_examples.md) (`.SparkPool`)

!!! tip "To always show hidden elements without using `-a`, configure: `fab config set show_hidden true`"


### Update Workspace

#### Update Workspace Display Name

Change the workspace display name.

```
fab set ws1.Workspace -q displayName -i ws2r
```

#### Update Workspace Description

Set or modify the workspace description.

```
fab set ws1.Workspace -q description -i "New description"
```

#### Configure Spark Runtime Version

Update the Spark runtime version for the workspace.

```
fab set ws1.Workspace -q sparkSettings.environment.runtimeVersion -i 1.2
```

#### Assign Starter Pool

Assign the Starter Pool as the default pool for the workspace.

```
fab set ws1.Workspace -q sparkSettings.pool.defaultPool -i '{"name": "Starter Pool","type": "Workspace"}'
```

#### Assign Custom Pool

Assign a custom Spark pool as the default pool.

```
fab set ws1.Workspace -q sparkSettings.pool.defaultPool -i '{"name": "spool1","type": "Workspace","id": "00000000-0000-0000-0000-000000000000"}'
```


### Remove Workspace

#### Remove Multiple Workspaces Interactively

Select and remove multiple workspaces (interactive mode only).

```
fab rm .
```

#### Remove Workspace Items Selectively

Remove specific items from a workspace (interactive mode).

```
fab rm ws1.Workspace
```

#### Force Remove Entire Workspace

Delete workspace and all its contents without confirmation.

```
fab rm ws1.Workspace -f
```

!!! warning "Using `-f` flag will delete the entire workspace and all items permanently. Use with extreme caution"

## Workspace Operations

### Export Workspace Items

!!! info "When you export item definition, the sensitivity label is not part of the definition"
Export items from a workspace to an output path. Supported for [exportable items](./item_examples.md#export-to-local); use `-a` to export all the items.

#### Export Workspace Items to Local Directory

Export items from a workspace to a local directory.

!!! warning "Windows OS File Name Restrictions"
    In Windows, items with names containing `\ / : * ? " < > |` will cause export errors. Provide a valid name in the output path to resolve this:
    ```
    fab export "ws1.Workspace/n?1.Notebook" -o "/tmp/n1.Notebook"
    ```

```py
fab export ws1.Workspace -o /tmp

# Export all items
fab export ws1.Workspace -o /tmp -a
```


#### Export Workspace Items to Lakehouse Files

Export workspace items directly to a Lakehouse Files location.

```py
fab export ws1.Workspace -o /ws1.Workspace/lh1.Lakehouse/Files

# Export all items
fab export ws1.Workspace -o /ws1.Workspace/lh1.Lakehouse/Files -a
```

### Copy Workspace Items
#### Copy Items Between Workspaces

Copy items from one workspace to another. Supported for [exportable items](./item_examples.md#copy-item).

```
fab cp ws1.Workspace ws2.Workspace
```

### Move Workspace Items

#### Move Items Between Workspaces

Move items from one workspace to another (interactive mode only).

```
fab mv ws1.Workspace ws2.Workspace
```

### Open in Browser

#### Open Workspace in Web Browser

Launch the workspace in your default web browser.

```
fab open ws1.Workspace
```