# External Data Share Examples

This page demonstrates how to manage [external data shares](https://learn.microsoft.com/en-us/fabric/governance/external-data-sharing-overview) in Microsoft Fabric using the CLI.

!!! note "Resource Type"
    Type: `.ExternalDataShare`

To explore all external data share commands and their parameters, run:

```
fab desc .ExternalDataShare
```

---

## Navigation

Navigate to the external data shares collection within a workspace:

```
fab cd ws1.Workspace/.externaldatashares
```

Navigate to a specific external data share:

```
fab cd ws1.Workspace/.externaldatashares/eds1.ExternalDataShare
```

## External Data Share Management


### Create External Data Shares

!!! info "The 'External data sharing' tenant setting must be enabled by your Fabric administrator before creating external data shares"

**Required Parameters:** `item`, `paths`, `recipient.tenantId` and `recipient.userPrincipalName`.

#### Create Basic External Data Share

Create an external data share with required parameters to share specific paths with an external user.

```
fab create ws1.Workspace/.externaldatashares/customer-data-share.ExternalDataShare -P item=analytics.Lakehouse,paths=[Files/public-data],recipient.tenantId=00000000-0000-0000-0000-000000000000,recipient.userPrincipalName=fabcli@microsoft.com
```

#### Create External Data Share with Multiple Paths

Share multiple directories or files with an external recipient.

```
fab create ws1.Workspace/.externaldatashares/multi-path-share.ExternalDataShare -P item=research.Lakehouse,paths=[Files/reports,Files/datasets,Tables/public_metrics],recipient.tenantId=00000000-0000-0000-0000-000000000000,recipient.userPrincipalName=fabcli@microsoft.com
```

#### Create External Data Share for Warehouse

Share warehouse data with external partners.

```
fab create ws1.Workspace/.externaldatashares/warehouse-share.ExternalDataShare -P item=sales.Warehouse,paths=[Tables/public_sales_data],recipient.tenantId=00000000-0000-0000-0000-000000000000,recipient.userPrincipalName=fabcli@microsoft.com
```

### Check External Data Share Existence

Check if a specific external data share exists and is accessible.

```
fab exists ws1.Workspace/.externaldatashares/eds1.ExternalDataShare
```

### Get External Data Share

#### Get External Data Share Details

Retrieve full external data share details in JSON format.

```
fab get ws1.Workspace/.externaldatashares/eds1.ExternalDataShare -q .
```

#### Export External Data Share Details

Query and export external data share properties to a local directory.

```
fab get ws1.Workspace/.externaldatashares/eds1.ExternalDataShare -q . -o /tmp
```


### List External Data Shares

#### List All External Data Shares

Display all external data shares in the workspace in simple format.

```
fab ls ws1.Workspace/.externaldatashares
```

#### List External Data Shares with Details

Show external data shares with detailed information including recipients, paths, and status.

```
fab ls ws1.Workspace/.externaldatashares -l
```

### Remove (Revoke) External Data Shares

#### Remove External Data Share with Confirmation

Revoke an external data share with interactive confirmation.

```
fab rm ws1.Workspace/.externaldatashares/analytics.ExternalDataShare
```

#### Force Remove External Data Share

Remove an external data share without confirmation prompts.

```
fab rm ws1.Workspace/.externaldatashares/research.ExternalDataShare -f
```

