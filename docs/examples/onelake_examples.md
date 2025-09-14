# OneLake Examples

This page demonstrates how to manage files and folders in Microsoft Fabric OneLake using the CLI. OneLake provides unified data lake storage that's integrated across all Fabric experiences.

OneLake is the built-in data lake for Microsoft Fabric that provides a single, unified namespace for all your data. You can manage files and folders directly through the CLI for supported item types.

---


## Navigation

Navigate to the Files section of a Lakehouse.

```
fab cd ws1.Workspace/lh1.Lakehouse/Files
```

Navigate to the Tables section of a Lakehouse.

```
fab cd ws1.Workspace/lh1.Lakehouse/Tables
```

Navigate to a nested folder within the Files section.

```
fab cd ws1.Workspace/lh1.Lakehouse/Files/raw-data/2024
```

## OneLake Management

### Check Folder Existence

Check if a specific directory exists in OneLake.

```
fab exists ws1.Workspace/lh1.Lakehouse/Files/data-processing
```

#### Check File Exists

Check if a specific file exists in OneLake.

```
fab exists ws1.Workspace/lh1.Lakehouse/Files/datasets/sales.parquet
```

### Get File/Folder

#### Get File/Folder Details

Retrieve full metadata for a file or folder.

```
fab get ws1.Workspace/lh1.Lakehouse/Files/datasets
```

#### Query Specific Properties

Extract specific properties using JMESPath queries.

```
# Get first path item
fab get ws1.Workspace/lh1.Lakehouse/Files/datasets -q paths[0]

# Get complete object
fab get ws1.Workspace/lh1.Lakehouse/Files/datasets -q .
```

#### Export Metadata

Save metadata query results to local storage or OneLake.

```py
# Export to local directory
fab get ws1.Workspace/lh1.Lakehouse/Files/datasets -q paths[0] -o /tmp/metadata
```

### List OneLake Content

**Items Supporting OneLake Folder Structure:**

- `.Lakehouse`
- `.Warehouse`
- `.MirroredDatabase`
- `.SQLDatabase`
- `.SemanticModel`[^1]
- `.KQLDatabase`[^1]

[^1]: Requires explicit enablement


Display content for an item.

```py
# List Files section in Lakehouse
fab ls ws1.Workspace/lh1.Lakehouse/Files

# List dbo Tables section in Warehouse
fab ls ws1.Workspace/wh1.Warehouse/Tables/dbo

# List Tables in SemanticModel
fab ls ws1.Workspace/sem1.SemanticModel/Tables
```

### Create Folders

!!! info "Create a folder in OneLake. Only supported for `Files` in `.Lakehouse`, `Main` and `Libs` folders in `.SparkJobDefinition`"

#### Create Directory in Lakehouse Files

Create a new folder within the Files section of a Lakehouse.

```
fab create ws1.Workspace/lh1.Lakehouse/Files/data-processing
```

#### Create Nested Directories

Create folder structures for organizing data.

```
fab create ws1.Workspace/lh1.Lakehouse/Files/raw-data/2024/january
fab create ws1.Workspace/lh1.Lakehouse/Files/processed-data/reports
```

### Remove Files and Folders

#### Remove Folder

Delete a folder and its contents from OneLake.

```
fab rm ws1.Workspace/lh1.Lakehouse/Files/old-data
```

#### Remove Specific File

Delete a specific file with force flag to skip confirmation.

```
fab rm ws1.Workspace/lh1.Lakehouse/Files/temp/temporary-file.csv -f
```

#### Remove with Confirmation

Delete resources with interactive confirmation.

```
fab rm ws1.Workspace/lh1.Lakehouse/Files/important-folder
```

## OneLake Operations

### Copy Files Between Folders

#### Copy File with Same Name

Copy a file from one OneLake folder to another, maintaining the original filename.

```
fab cp ws1.Workspace/lh1.Lakehouse/Files/csv/data.csv ws1.Workspace/lh1.Lakehouse/Files/dest/
```

#### Copy File with New Name

Copy a file to a different folder and rename it in the process.

```
fab cp ws1.Workspace/lh1.Lakehouse/Files/csv/data.csv ws1.Workspace/lh1.Lakehouse/Files/dest/renamed_data.csv
```


### Upload Files to OneLake

#### Upload File with Same Name

Copy a local file to OneLake, keeping the original filename.

```
fab cp /tmp/local-data/dataset.csv ws1.Workspace/lh1.Lakehouse/Files/upload/
```

#### Upload File with New Name

Upload a local file to OneLake and rename it during the upload process.

```
fab cp /tmp/local-data/dataset.csv ws1.Workspace/lh1.Lakehouse/Files/upload/processed_dataset.csv
```

### Download Files from OneLake

#### Download File with Same Name

Download a file from OneLake to a local directory, maintaining the filename.

```
fab cp ws1.Workspace/lh1.Lakehouse/Files/csv/fab.csv /tmp/mydir
```

#### Download File with New Name

Download a file from OneLake and rename it locally.

```
fab cp ws1.Workspace/lh1.Lakehouse/Files/csv/fab.csv /tmp/mydir/renamed_copy_fab.csv
```