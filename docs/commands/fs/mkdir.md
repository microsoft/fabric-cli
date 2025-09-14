---
hide:
  - toc
---

# `mkdir` / `create` Command

Create a new workspace, item, or directory.

!!! info "Creating a domain requires tenant-level Fabric Administrator privileges"

**Usage:**

```
fab mkdir <path>/<name>.<type> [-P <params>]
```

**Parameters:**

- `<path>`: Path to create the resource in. If not provided, the current context is used. Optional.
- `<name>`: Name of the resource.
- `<type>`: Type of the resource (Workspace, Notebook, Capacity, etc).
- `-P, --params <params>`: Key=value parameters, comma-separated. Optional.

    The following `-P, --params` are supported:

    | Type | Required Properties | Optional Properties |
    | :--- | :--- | :--- |
    | .Lakehouse | | `enableSchemas` |
    | .Warehouse | | `enableCaseInsensitive` |
    | .KQLDatabase | | `dbType`, `eventhouseId`, `clusterUri`, `databaseName` |
    | .MirroredDatabase | | `mirrorType`, `connectionId`, `database`, `defaultSchema`, `mountedTables` |
    | .Report | | `semanticModelId` |
    | .MountedDataFactory | `subscriptionId`, `resourceGroup`, `factoryName` | |
    | .Gateway | `capacity` (or `capacityId`), `virtualNetworkName`, `subnetName` | `inactivityMinutesBeforeSleep`  (default: 30), `numberOfMemberGateways`  (default: 1), `resourceGroupName`[^4], `subscriptionId`[^4] |
    | .Connection | `connectionDetails.type`, `connectionDetails.parameters.*`[^1], `credentialDetails.type`, `credentialDetails.*`[^1] | `description`, `gateway` (or `gatewayId`), `privacyLevel`, `connectionDetails.creationMethod`[^2], `credentialDetails.connectionEncryption`[^3], `credentialDetails.singleSignOnType`, `credentialDetails.skipTestConnection` (default: False)|
    | .ExternalDataShare | `item`, `paths`, `recipient.tenantId`, `recipient.userPrincipalName` | |
    | .ManagedPrivateEndpoint | `targetPrivateLinkResourceId`, `targetSubresourceType` | `autoApproveEnabled` |
    | .Workspace | | `capacityName` |
    | .Capacity | | [`sku`](https://learn.microsoft.com/en-us/fabric/enterprise/licenses#capacity), `admin`, `location`, `resourceGroup`, `subscriptionId` |
    | .Domain | | `parentDomainName`, `description` |
    | .SparkPool | | `nodeSize`, `autoScale.maxNodeCount`, `autoScale.minNodeCount` |

[^1]: The `*` indicates parameters that depend on the chosen `type`. For example, for SQL with Basic auth, you need `connectionDetails.parameters.server`, `connectionDetails.parameters.database`, `credentialDetails.username`, and `credentialDetails.password`.
[^2]: If `connectionDetails.creationMethod` is not specified, the CLI will use the first matching creation method based on connection parameters. For connections supporting multiple creation methods, specify this value to avoid unexpected behavior.
[^3]: The default value for `credentialDetails.connectionEncryption` (Any) will first attempt encrypted connection and fallback to unencrypted if needed.
[^4]: If `resourceGroupName` and `subscriptionId` are not provided, the CLI will use your Azure credentials to search for them using the provided VNet/subnet names.

```
fab mkdir ws1.Workspace
```
