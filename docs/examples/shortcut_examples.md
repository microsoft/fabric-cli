# Shortcut Examples

This page demonstrates how to manage [shortcuts](https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts) in Microsoft Fabric using the CLI. Shortcuts provide virtual access to data stored in external locations or other OneLake items without copying the data.

Shortcuts enable you to virtualize data from various sources including OneLake, Azure Data Lake Storage, Amazon S3, and other cloud storage services directly within your Lakehouse.

---

## Shortcut Management

### Create Shortcut
Create shortcuts in Lakehouse `/Files` or `/Tables` sections.

#### Create an Internal OneLake File Shortcut

Create a shortcut to another OneLake Files location within the same tenant.

```
fab ln ws1.Workspace/lh1.Lakehouse/Files/shared_data.Shortcut --type oneLake --target ../../shared.Workspace/source.Lakehouse/Files/datasets
```

#### Create an External Azure Data Lake Gen2 Shortcut

Create a shortcut to Azure Data Lake Storage Gen2 for external data access.

```
fab ln ws1.Workspace/lh1.Lakehouse/Tables/external_sales.Shortcut --type adlsGen2 -i '{"location": "https://<storage_name>.dfs.core.windows.net/", "subpath": "sales-data/2024", "connectionId": "<connection-id>"}'
```

### Check Shortcut Existence

#### Verify File Shortcut Exists

Check if a shortcut exists in the Files section of a Lakehouse.

```
fab exists ws1.Workspace/lh1.Lakehouse/Files/external_data.Shortcut
```

#### Verify Table Shortcut Exists

Check if a shortcut exists in the Tables section of a Lakehouse.

```
fab exists ws1.Workspace/lh1.Lakehouse/Tables/external_table.Shortcut
```

### Get Shortcut

#### Get Shortcut Details

Retrieve full shortcut details including target information and configuration.

```
fab get ws1.Workspace/lh1.Lakehouse/Files/external_data.Shortcut
fab get ws1.Workspace/lh1.Lakehouse/Tables/external_table.Shortcut
```

#### Query Shortcut Target

Extract target information using JMESPath query.

```
fab get ws1.Workspace/lh1.Lakehouse/Files/external_data.Shortcut -q target
```

#### Get Complete Shortcut Object

Retrieve all shortcut properties for detailed analysis.

```
fab get ws1.Workspace/lh1.Lakehouse/Tables/external_table.Shortcut -q .
```

#### Export Shortcut Details

Save shortcut configuration to local directory or OneLake.

```py
# Export to local directory
fab get ws1.Workspace/lh1.Lakehouse/Files/external_data.Shortcut -q target -o /tmp

# Export complete configuration
fab get ws1.Workspace/lh1.Lakehouse/Tables/external_table.Shortcut -q . -o /tmp
```


### Update Shortcut

#### Rename File Shortcut

Change the name of a shortcut in the Files section.

```
fab set ws1.Workspace/lh1.Lakehouse/Files/updated_name.Shortcut -q name -i external_data
```

#### Force Rename Table Shortcut

Rename a table shortcut without confirmation prompts.

```
fab set ws1.Workspace/lh1.Lakehouse/Tables/customer_data.Shortcut -q name -i customer_master_data -f
```


### Remove Shortcut

#### Remove File Shortcut

Delete a shortcut from the Files section with confirmation.

```
fab rm ws1.Workspace/lh1.Lakehouse/Files/old_external_data.Shortcut
```

#### Force Remove Table Shortcut

Delete a shortcut from the Tables section without confirmation.

```
fab rm ws1.Workspace/lh1.Lakehouse/Tables/deprecated_source.Shortcut -f
```
