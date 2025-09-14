# Managed Private Endpoint Examples

This page demonstrates how to manage private endpoints in Microsoft Fabric using the CLI. Managed private endpoints provide secure, private connectivity to Azure resources without exposing traffic to the public internet.

!!! note "Resource Type"
    Type: `.ManagedPrivateEndpoint`

To explore all managed private endpoint commands and their parameters, run:

```
fab desc .ManagedPrivateEndpoint
```

---

## Navigation

Navigate to the managed private endpoints collection within a workspace:

```
fab cd ws1.Workspace/.managedprivateendpoints
```

Navigate to a specific managed private endpoint:

```
fab cd ws1.Workspace/.managedprivateendpoints/storage-endpoint.ManagedPrivateEndpoint
```

## Managed Private Endpoints Management

### Create Managed Private Endpoint


**Required Parameters:** `targetPrivateLinkResourceId` and `targetSubresourceType`.

**Optional Parameters:** `autoApproveEnabled` (default: false).

!!! info "See Microsoft documentation for [supported endpoints](https://learn.microsoft.com/fabric/security/security-managed-private-endpoints-create), [resource ID formats](https://learn.microsoft.com/fabric/security/security-managed-private-endpoints-create), and [subresource types](https://learn.microsoft.com/azure/private-link/private-endpoint-overview#private-link-resource)"

#### Create Managed Private Endpoint to Azure Data Lake Storage Gen2

Create a private endpoint to securely connect to Azure Data Lake Storage.

```
fab create ws1.Workspace/.managedprivateendpoints/adls-endpoint.ManagedPrivateEndpoint -P targetPrivateLinkResourceId=/subscriptions/<subscription_id>/resourceGroups/<resource_group_name>/providers/Microsoft.Storage/storageAccounts/<storage_account_name>,targetsubresourcetype=dfs
```

#### Create Auto-Approved Managed Private Endpoint to SQL Server

Create a private endpoint to SQL Server with automatic approval enabled.

```
fab create ws1.Workspace/.managedprivateendpoints/sql-endpoint.ManagedPrivateEndpoint -P targetPrivateLinkResourceId=/subscriptions/<subscription_id>/resourceGroups/<resource_group_name>/providers/Microsoft.Sql/servers/<sql_server_name>,targetSubresourceType=sqlServer,autoApproveEnabled=true
```

### Check Managed Private Endpoint Existence

Check if a specific managed private endpoint exists and is accessible.

```
fab exists ws1.Workspace/.managedprivateendpoints/storage-endpoint.ManagedPrivateEndpoint
```

### Get Managed Private Endpoint

#### Get Managed Private Endpoint Details

Retrieve full managed private endpoint details.

```
fab get ws1.Workspace/.managedprivateendpoints/storage-endpoint.ManagedPrivateEndpoint
```

#### Export Managed Private Endpoint Details

Query and export managed private endpoint properties to a local directory.

```
fab get ws1.Workspace/.managedprivateendpoints/storage-endpoint.ManagedPrivateEndpoint -q . -o /tmp
```

### List Managed Private Endpoints

#### List All Managed Private Endpoints

Display all managed private endpoints in the workspace in simple format.

```
fab ls ws1.Workspace/.managedprivateendpoints
```

#### List Managed Private Endpoints with Details

Show managed private endpoints with detailed information including target resources, status, and configuration.

```
fab ls ws1.Workspace/.managedprivateendpoints -l
```


### Remove Managed Private Endpoints


!!! info "Managed private endpoints cannot be removed while in `Provisioning` state. Wait for provisioning to complete before attempting removal"


#### Remove Managed Private Endpoint with Confirmation

Delete a managed private endpoint with interactive confirmation.

```
fab rm ws1.Workspace/.managedprivateendpoints/deprecated-endpoint.ManagedPrivateEndpoint
```

#### Force Remove Managed Private Endpoint

Delete a managed private endpoint without confirmation prompts.

```
fab rm ws1.Workspace/.managedprivateendpoints/test-endpoint.ManagedPrivateEndpoint -f
```
