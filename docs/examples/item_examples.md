# Item Management Examples

This page demonstrates how to manage Microsoft Fabric items using the CLI. Items are the core resource types within Fabric workspaces, including notebooks, reports, lakehouses, etc.

!!! note "Resource Types"
    Type: `.<item_type>` (e.g., `.Notebook`, `.Lakehouse`, `.Report`)

To explore commands for any item type, run:

```
fab desc .<item_type>
```

See all [available item extensions](../essentials/resource_types.md#item-types).

---

## Navigation

Navigate to an item using its full path.

```
fab cd /ws1.Workspace/lh1.Lakehouse
```

Navigate to an item using relative path from current context.

```
fab cd ../ws1.Workspace/lh1.Lakehouse
```

## Item Management

### Create Item

**Unsupported Items:** `.Dashboard`, `.Datamart`, `.MirroredWarehouse`, `.PaginatedReport`, `.SQLEndpoint`

**Items with Required Parameters:**

- `.MountedDataFactory`: `subscriptionId`, `resourceGroup`, `factoryName`

**Items with Optional Parameters:**

- `.Lakehouse`: `enableSchemas`
- `.Warehouse`: `enableCaseInsensitive`
- `.KQLDatabase`: `dbtype`, `eventhouseId`, `clusterUri`, `databaseName`
- `.MirroredDatabase`: `mirrorType`, `connectionId`, `defaultSchema`, `database`, `mountedTables`
- `.Report`: `semanticModelId`

#### Create Basic Items

Create items without special parameters.

```
fab create ws1.Workspace/lh1.Lakehouse
```

#### Create Items with Parameters

Create items with specific configuration parameters.

```
fab create ws1.Workspace/lh1.Lakehouse -P enableSchemas=true
```

#### Check Item Supported Parameters
View supported parameters for any item type.

```
fab create lh1.Lakehouse -P
```

### Check Item Existence

Check if a specific item exists and is accessible.

```
fab exists ws1.Workspace/nb1.Notebook
```

### Get Item

!!! info "When you get an item definition, the sensitivity label is not a part of the definition"

**Unsupported Items:** `.Dashboard`, `.Datamart`, `.MirroredWarehouse`, `.PaginatedReport`, `.SQLEndpoint`

#### Get Item Details

Retrieve full item details.

```
fab get ws1.Workspace/lh1.Lakehouse
```

#### Get All Properties (Verbose)

Show comprehensive item properties including extended metadata.

```
fab get ws1.Workspace/rep1.Report -v
```

#### Query Specific Properties

Extract specific properties using JMESPath query.

```
fab get ws1.Workspace/lh1.Lakehouse -q properties.sqlEndpointProperties
```

#### Export Query Results

Save query results to a local directory.

```
fab get ws1.Workspace/lh1.Lakehouse -q properties.sqlEndpointProperties -o /tmp
```

### List Items

#### List Items in Workspace

Display all items within a workspace.

```
fab ls ws1.Workspace
```

#### List Items with Details

Show items with comprehensive metadata.

```
fab ls ws1.Workspace -l
```

#### Query List Items in Workspace

```
fab ls ws1.Workspace -q [].name
fab ls ws1.Workspace -q [].{name:name,id:id}
fab ls ws1.Workspace -q [?contains(name, 'Notebook')]
fab ls ws1.Workspace -l -q [?contains(name, 'Dataflow')].{name:name, id:id}
```

#### List Item Contents

Browse contents of items that support folder structures.

```
fab ls ws1.Workspace/lh1.Lakehouse
fab ls ws1.Workspace/wh1.Warehouse
fab ls ws1.Workspace/sem1.SemanticModel
```

**Items Supporting OneLake Folder Structure:**

- `.Lakehouse`
- `.Warehouse`
- `.MirroredDatabase`
- `.SQLDatabase`
- `.SemanticModel`[^1]
- `.KQLDatabase`[^1]

[^1]: Requires explicit enablement

### Update Item

For detailed information on updating item properties, including limitations and property paths, see the [`set` command documentation](../commands/fs/set.md#query-support).

#### Update Display Name

Change the display name of an item.

```
fab set ws1.Workspace/nb1.Notebook -q displayName -i "Updated Notebook Name"
```

#### Set Description

Add or update item description.

```
fab set ws1.Workspace/lh1.Lakehouse -q description -i "Production data lakehouse"
```

### Remove Item

#### Remove Item with Confirmation

Delete an item with interactive confirmation.

```
fab rm ws1.Workspace/nb1.Notebook
```

#### Force Remove Item

Delete an item without confirmation prompts.

```
fab rm ws1.Workspace/lh1.Lakehouse -f
```

### Set Item Properties

#### Set default lakehouse

```
fab set ws1.Workspace/nb1.Notebook -q definition.parts[0].payload.metadata.dependencies.lakehouse -i '{"known_lakehouses": [{"id": "00000000-0000-0000-0000-000000000001"}],"default_lakehouse": "00000000-0000-0000-0000-000000000001", "default_lakehouse_name": "lh1","default_lakehouse_workspace_id": "00000000-0000-0000-0000-000000000000"}'
```

#### Set Default Environment for a Notebook

```
fab set ws1.Workspace/nb1.Notebook -q environment -i '{"environmentId": "00000000-0000-0000-0000-000000000002", "workspaceId": "00000000-0000-0000-0000-000000000000"}'
```

#### Set Default Warehouse for a Notebook

```
fab set ws1.Workspace/nb1.Notebook -q warehouse -i '{"known_warehouses": [{"id": "00000000-0000-0000-0000-000000000003", "type": "Datawarehouse"}], "default_warehouse": "00000000-0000-0000-0000-000000000003"}'
```

#### Rebind Report to Semantic Model

For Report PBIR definition version 1:

```
fab set ws1.Workspace/rep1.Report -q semanticModelId -i "00000000-0000-0000-0000-000000000000"
```

For Report PBIR definition version 2:

```
fab set ws1.Workspace/rep1.Report -q definition.parts[0].payload.datasetReference.byConnection.ConnectionString -i "ConnectionStringPrefix....semanticmodelid=00000000-0000-0000-0000-000000000000"
```


## Item Operations
### Copy Item

!!! info "When you copy an item definition, the sensitivity label is not a part of the definition"

**Supported Item Types for Copy:**

- `.Notebook`, `.SparkJobDefinition`, `.DataPipeline`
- `.Report`, `.SemanticModel`
- `.KQLDatabase`, `.KQLDashboard`, `.KQLQueryset`
- `.Eventhouse`, `.Eventstream`
- `.MirroredDatabase`, `.Reflex`
- `.MountedDataFactory`, `.CopyJob`, `.VariableLibrary`


#### Copy Item to Workspace

Copy an item to the a  workspace, preserving its original name.

```
fab cp ws1.Workspace/source.Item target.Workspace
```

#### Copy Item With to Workspace with a new Item Name

Copy an item to the destination and rename.

```
fab cp ws1.Workspace/source.Item ws2.Workspace/dest.Item
```

#### Copy Item to Folder

Copy an item into the destination folder. If the folder does not exist, it will be created.

```
fab cp ws1.Workspace/source.Item ws2.Workspace/dest.Folder
```


### Move Item

!!! info "When you move item definition, the sensitivity label is not a part of the definition"

#### Move Item to Workspace

Move an item to a workspace (removes from source).

```
fab mv ws1.Workspace/nb1.Notebook ws2.Workspace
```

#### Move Item To Workspace with a New Name

Move an item to the destination and rename.

```
fab mv ws1.Workspace/nb1.Notebook ws2.Workspace/nb_new_name.Notebook
```

#### Move Item To Folder

Move an item into a folder, preserving its original name.

```
fab mv ws1.Workspace/nb.Notebook ws2.Workspace/dest.Folder
```

### Export Item


!!! info "When you export item definition, the sensitivity label is not a part of the definition"

#### Export to Local

Export an item definition to a local directory.

```
fab export ws1.Workspace/nb1.Notebook -o /tmp
```

**Exportable Item Types:**

- `.Notebook`, `.SparkJobDefinition`, `.DataPipeline`
- `.Report`, `.SemanticModel`
- `.KQLDatabase`, `.KQLDashboard`, `.KQLQueryset`
- `.Eventhouse`, `.Eventstream`, `.MirroredDatabase`
- `.Reflex`, `.MountedDataFactory`, `.CopyJob`, `.VariableLibrary`


#### Export to Lakehouse

Export item definition directly to a Lakehouse Files location.

```
fab export ws1.Workspace/nb1.Notebook -o /ws1.Workspace/lh1.Lakehouse/Files/exports
```

### Import Item

#### Import from Local

Import an item definition from a local directory into the workspace.

```
fab import ws1.Workspace/nb1_imported.Notebook -i /tmp/exports/nb1.Notebook
```

**Supported Import Formats:** `.ipynb` (default) and `.py`.


### Start/Stop Mirrored Databases

#### Start Mirrored Database

Start data synchronization for a mirrored database.

```
fab start ws1.Workspace/mir1.MirroredDatabase
```


#### Force Start Mirrored Database

Start mirrored database without confirmation.

```
fab start ws1.Workspace/mir1.MirroredDatabase -f
```

#### Stop Mirrored Database

Stop data synchronization for a mirrored database.

```
fab stop ws1.Workspace/mir1.MirroredDatabase
```

#### Force Stop Mirrored Database

Stop mirrored database without confirmation.

```
fab stop ws1.Workspace/mir1.MirroredDatabase -f
```

### Semantic Model Refresh

For detailed examples on triggering and monitoring semantic model refresh using the API command, see the [Semantic Model Refresh Example](refresh_semantic_model_example.md).

### Open in Browser

#### Open Item in Web Interface

Launch an item in the default web browser.

```
fab open ws1.Workspace/lh1.Lakehouse
```