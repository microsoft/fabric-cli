# Describe (desc) Examples

This page demonstrates how to use the `desc` command to explore and understand available commands for different Fabric resource types. The describe functionality helps you discover what operations are supported for specific items and elements.

To explore all describe commands and their parameters, run:

```
fab desc -h
```

---


## Fabric Items Elements

Fabric items are the primary content types within workspaces, including notebooks, datasets, reports, and other analytical assets.

### Check Item Commands by Extension

Check available commands for item using the extension syntax.

```
fab desc .Notebook
```

### Check Item Commands by Existing Path

Check available commands for an existing item using its full path.

```
fab desc ws1.Workspace/nb1.Notebook
```

## Virtual Item Elements

### Check Commands by Extension

Check available commands for virtual item using the extension syntax.

```
fab desc .Capacity
```

### Check Commands by Existing Path

Check available commands for an existing virtual item using its full path.

```
fab desc .capacities/capac1.Capacity
```

## Virtual Elements List

The following non-item elements are available for description:

### Tenant-Level Resources

```
# Capacity management
fab desc .Capacity

# Data gateway management  
fab desc .Gateway

# Connection management
fab desc .Connection

# Domain management
fab desc .Domain
```

### Workspace-Level Resources

```
# Workspace management
fab desc .Workspace

# External data sharing
fab desc .ExternalDataShare

# Identity management
fab desc .ManagedIdentity

# Network endpoints
fab desc .ManagedPrivateEndpoint

# Spark compute resources
fab desc .SparkPool
```

---


The `desc` command is your gateway to understanding the full capabilities of Fabric CLI for any resource type. Use it liberally to explore and discover new functionality.
