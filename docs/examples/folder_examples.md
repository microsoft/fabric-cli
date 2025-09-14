# Folder Management Examples

!!! info "Enable Folder Listing"

    By default, the `ls` command does not display folders. To enable folder listing, run the following command:
    
    ```
    fab config set folder_listing_enabled true
    ```

This page demonstrates how to manage folders in Microsoft Fabric using the CLI. Folder operations allow you to organize items and resources within workspaces and supported item types.

!!! note "Resource Type"
    Type: `.Folder`

To explore all folder-related commands and their parameters, run:

```
fab desc .Folder
```

---

## Navigation

Navigate to a folder using the full workspace path.

```
fab cd ws1.Workspace/fd1.Folder
```

Navigate to a workspace using relative path from current context.

```
fab cd ../../ws1.Workspace/fd1.Folder
```

## Folder Management

### Create Folder

Create a new folder within a workspace.

```
fab create ws1.Workspace/fd1.Folder
```

### Folder Existence

Check if a folder exists.

```
fab exists ws1.Workspace/fd1.Folder
```

### Get Folder
#### Get Folder Details

Retrieve full folder details.

```
fab get ws1.Workspace/fd1.Folder
```

#### Query Specific Properties

Query folder properties using JMESPath syntax.

```
fab get ws1.Workspace/f1.Folder -q id
```

#### Export Query Results

Save query results to a local file.

```
fab get ws1.Workspace/fd1.Folder -q parentFolderId -o /tmp
```
### List Folders

List the workspace contents. This command returns both items and folders within the workspace.
```
fab ls ws1.Workspace
```

### List Folder Items

List the contents of a folder. Use `-l` for detailed output.

```
fab ls ws1.Workspace/fd1.Folder
```

### Update Folder

Set or update folder properties (currently only `displayName` is supported). Use `-f` to force updates.

```
fab set ws1.Workspace/fd1.Folder -q displayName -i fd1ren
```

### Remove Folder

Remove a folder. Use `-f` to force deletion without confirmation.

```
fab rm ws1.Workspace/fd1.Folder
```

## Folder Operations

### Copy Folder


#### Copy Folder to Workspace

The folder is copied to the root of the destination workspace, preserving its name. This will fail if a folder with the same name already exists.

```
fab cp source.Workspace/source.Folder target.Workspace
```

*Result:* `target.Workspace/source.Folder`

#### Copy Folder to Folder

- If the destination folder **exists**, the source folder is copied **inside** it.

    ```
    fab cp ws.Workspace/source.Folder ws.Workspace/dest.Folder
    ```

    *Result:* `ws.Workspace/dest.Folder/source.Folder`

- If the destination folder **does not exist**, the source folder is renamed to the destination folder name.
    
    ```
    fab cp ws.Workspace/source.Folder ws.Workspace/dest.Folder
    ```

    *Result:* `ws.Workspace/dest.Folder`


### Move Folder


#### Move Folder To Workspace

Move folder to workspace, preserving its name. 

!!! warning "This command will fail if a folder with the same name already exists"

```
fab mv ws1.Workspace/source.Folder ws2.Workspace
```

#### Move Folder To Folder

- If the destination folder **does not exist**, the source folder is renamed to the destination folder name.

    ```
    fab mv ws1.Workspace/source.Folder ws2.Workspace/dest.Folder
    ```

    *Result:* `ws2.Workspace/dest.Folder`

- If the destination folder **exists**, the source folder is moved **inside** it.

    ```
    fab mv ws1.Workspace/source.Folder ws2.Workspace/dest.Folder
    ```

    *Result:* `ws2.Workspace/dest.Folder/source.Folder`

---

For managing folders within OneLake storage (e.g., `Lakehouse/Files`), see [OneLake Examples](./onelake_examples.md)