# Capacity Examples

This page demonstrates how to manage Microsoft Fabric [capacities](https://learn.microsoft.com/en-us/fabric/enterprise/licenses#capacity) using the CLI.

!!! note "Resource Type"
    Type: `.Capacity`

To explore all capacity commands and their parameters, run:

```
fab desc .Capacity
```

---

## Navigation

Navigate to the capacities collection using absolute path:

```
fab cd .capacities
```

Navigate to a specific capacity using relative path:

```
fab cd ../.capacities/capac1.Capacity
```

## Capacity Management

### Create Capacity
#### Create a capacity using default settings from CLI configuration

```
fab create .capacities/capac2.Capacity
```

Default values come from configuration:

- Capacity Admin: `default_az_admin`
- Capacity Location: `default_az_location`
- Resource Group: `default_az_resource_group`
- Subscription: `default_az_subscription_id`

#### Create a capacity with a specified SKU size

```
fab create .capacities/capac3.Capacity -P sku=F4
```

#### Create a capacity with complete inline configuration

```
fab create .capacities/capac4.Capacity -P sku=F2,admin=fabcli@microsoft.com,location=westeurope,resourceGroup=rg-fab-cli,subscriptionId=b1cd297b-e573-483f-ae53-1b8a08014120
```


### Check if a specific capacity exists and is accessible

```
fab exists .capacities/capac1.Capacity
```

### Get Capacity

#### Get Capacity Details

```
fab get .capacities/capac1.Capacity
```

#### Export Capacity Details to a local directory

```
fab get .capacities/capac1.Capacity -q . -o /tmp
```

### List Capacities

#### Display existing capacities in a simple format.

```
fab ls .capacities
```

#### Show capacities detailed information.

```
fab ls .capacities -l
```

### Update Capacity

Change the SKU of an existing capacity to scale compute resources

```
fab set .capacities/capac1.Capacity -q sku.name -i F4
```


### Remove Capacity

!!! warning "Removing a capacity is irreversible and will affect all assigned workspaces and items"

#### Remove a capacity with interactive confirmation

```
fab rm .capacities/capac2.Capacity
```

#### Remove a capacity without confirmation prompts

```
fab rm .capacities/capac3.Capacity -f
```

## Capacity Operations

### Start/Resume Capacity

#### Start a stopped capacity with interactive confirmation

```
fab start .capacities/capac1.Capacity
```

#### Start a capacity without confirmation prompts

```
fab start .capacities/capac1.Capacity -f
```

### Stop Capacity
#### Stop a running capacity with interactive confirmation

```
fab stop .capacities/capac1.Capacity
```

#### Stop a capacity without confirmation prompts

```
fab stop .capacities/capac1.Capacity -f
```

### Assign an active capacity to a workspace for compute and storage resources

```
fab assign .capacities/capac1.Capacity -W ws1.Workspace
```

### Unassign capacity assignment from a workspace

```
fab unassign .capacities/capac1.Capacity -W ws1.Workspace
```