# Gateway Examples

This page demonstrates how to manage [on-premises and virtual network (VNet) data gateways](https://learn.microsoft.com/en-us/data-integration/gateway/) in Microsoft Fabric using the CLI.

!!! note "Resource Type"
    Type: `.Gateway`

To explore all gateway commands and their parameters, run:

```
fab desc .Gateway
```

---

## Navigation
Navigate to the gateways collection using absolute path:

```
fab cd /.gateways
```

Navigate to a specific gateway using relative path:

```
fab cd ../.gateways/prod-gateway.Gateway
```
## Gateway Management


### Create Gateway

Create a gateway synchronously. Use optional parameters with -P as needed; defaults apply if unspecified — see config set.

!!! tip "VNet Gateway Prerequisites"
    Before creating a VNet Gateway, ensure all requirements are met:

    - Feature is supported in your region
    - Subnet follows all requirements and is properly delegated
    - Proper permissions on Azure subscription and VNet
    - See [VNet Gateway Documentation](https://learn.microsoft.com/en-us/data-integration/vnet/create-data-gateways) for complete requirements

#### Create Basic VNet Gateway

Create a VNet gateway with required parameters only.

```
fab create .gateways/basic-vnet-gateway.Gateway -P capacity=mycapacityname,virtualNetworkName=west-us-2-fabric-test-vnet,subnetName=vnet-gateway
```

#### Create VNet Gateway with Custom Configuration

Create a VNet gateway with additional configuration parameters.

```
fab create .gateways/advanced-vnet-gateway.Gateway -P capacity=production-capacity,resourceGroupName=fabric-rg,subscriptionId=25bdf70e-a1b2-4c3d-8e9f-123456789abc,virtualNetworkName=prod-fabric-vnet,subnetName=prod-gateway-subnet,inactivityMinutesBeforeSleep=60,numberOfMemberGateways=2
```

### Check Gateway Existence

Check if a specific gateway exists and is accessible.

```
fab exists .gateways/prodgateway.Gateway
```

### Get Gateway

#### Get Gateway Details

Retrieve full gateway details.

```
fab get .gateways/prod-gateway.Gateway
```

#### Export Gateway Details

Query and export gateway properties to a local directory.

```
fab get .gateways/prod-gateway.Gateway -q . -o /tmp
```

### List Gateways
#### Display existing gateways in a simple format.
```
fab ls .gateways
```

#### Show gateways with detailed information.

```
fab ls .gateways -l
```

### Update Gateway

Update the display name of a gateway for better identification.

```
fab set .gateways/prod-gateway.Gateway -q displayName -i "Production Data Gateway"
```

### Remove Gateway

!!! warning "Gateway Deletion Impact"
    Removing a gateway will affect all connections and data sources that depend on it. Ensure dependent resources are updated or migrated before deletion.

#### Remove a gateway with interactive confirmation

```
fab rm .gateways/old-gateway.Gateway
```

#### Remove a gateway without confirmation prompts.

```
fab rm .gateways/test-gateway.Gateway -f
```

### Get Gateway Permissions
#### Get Gateway Permission Details
```
fab acl get .gateways/prod-gateway.Gateway
```

#### Query Gateway Permission Principals

Extract principal information using JMESPath query.

```
fab acl get .gateways/prod-gateway.Gateway -q "[*].principal"
```

#### Export Gateway Permission Query

Save gateway permission query results to a local directory.

```
fab acl get .gateways/prod-gateway.Gateway -q "[*].principal" -o /tmp
```

#### Export to Lakehouse from Gateway Context

Navigate to gateway and export permissions to Lakehouse.

```
fab cd .gateways/prod-gateway.Gateway
fab acl get . -q "[*].principal" -o /ws1.Workspace/lh1.Lakehouse/Files
```

### List Gateway Permissions

```
fab acl ls .gateways/prod-gateway.Gateway
```
