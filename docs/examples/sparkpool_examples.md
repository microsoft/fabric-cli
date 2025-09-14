# Spark Pool Examples

This page demonstrates how to manage Spark pools in Microsoft Fabric using the CLI. Spark pools provide dedicated compute resources for data engineering and analytics workloads within workspaces.

!!! note "Resource Type"
    Type: `.SparkPool`

To explore all Spark pool commands and their parameters, run:

```
fab desc .SparkPool
```

---

## Navigation

Navigate to the Spark pools collection within a workspace.

```
fab cd ws1.Workspace/.sparkpools
```

Navigate to a specific Spark pool.

```
fab cd ws1.Workspace/.sparkpools/analytics-pool.SparkPool
```

## Spark Pool Management


### Create Spark Pool


**Optional Parameters:** [`nodeSize`](https://learn.microsoft.com/en-us/fabric/data-engineering/create-custom-spark-pools#node-size-options) (default: Small), `autoScale.maxNodeCount` (default: 1) and `autoScale.minNodeCount` (default: 1).<br>
 `maxNodeCount` must be greater or equal to `minNodeCount`.

#### Create Basic Spark Pool

Create a Spark pool with default configuration (Small, single-node).

```
fab create ws1.Workspace/.sparkpools/basic-pool.SparkPool
```

#### Create Spark Pool with Custom Node Size

Create a Spark pool with a specific node size for different workload requirements.

```
fab create ws1.Workspace/.sparkpools/large-pool.SparkPool -P nodeSize=Large
```

#### Create Auto-Scaling Spark Pool

Create a Spark pool with auto-scaling configuration for dynamic workloads.

```
fab create ws1.Workspace/.sparkpools/scaling-pool.SparkPool -P nodeSize=Medium,autoScale.minNodeCount=1,autoScale.maxNodeCount=5
```

### Check Spark Pool Existence


Check if a specific Spark pool exists and is accessible.

```
fab exists ws1.Workspace/.sparkpools/analytics-pool.SparkPool
```

### Get Spark Pool

#### Get Spark Pool Details

Retrieve full Spark pool details.

```
fab get ws1.Workspace/.sparkpools/analytics-pool.SparkPool
```

#### Export Spark Pool Details

Query and export Spark pool properties to a local directory.

```
fab get ws1.Workspace/.sparkpools/analytics-pool.SparkPool -q . -o /tmp
```

### List Spark Pools

#### List All Spark Pools

Display all Spark pools in the workspace in simple format.

```
fab ls ws1.Workspace/.sparkpools
```

#### List Spark Pools with Details

Show Spark pools with detailed information including node configuration, scaling settings, and status.

```
fab ls ws1.Workspace/.sparkpools -l
```


### Update Spark Pool

**Supported Properties:** `name`, `nodeSize`, `autoScale.enabled`, `autoScale.minNodeCount` and `autoScale.maxNodeCount`.

#### Rename Spark Pool

Update the name of a Spark pool for better identification.

```
fab set ws1.Workspace/.sparkpools/analytics-pool.SparkPool -q name -i "production-analytics-pool"
```

#### Change Node Size

Update the node size to scale compute capacity up or down.

```
fab set ws1.Workspace/.sparkpools/production-analytics-pool.SparkPool -q nodeSize -i Large
```

#### Enable Auto-Scaling

Enable auto-scaling for dynamic resource allocation.

```
fab set ws1.Workspace/.sparkpools/production-analytics-pool.SparkPool -q autoScale.enabled -i True
```

#### Update Scaling Configuration

Modify minimum and maximum node counts for auto-scaling.

```
# Set maximum nodes
fab set ws1.Workspace/.sparkpools/production-analytics-pool.SparkPool -q autoScale.maxNodeCount -i 8

# Set minimum nodes
fab set ws1.Workspace/.sparkpools/production-analytics-pool.SparkPool -q autoScale.minNodeCount -i 2
```


### Remove Spark Pools

#### Remove Spark Pool with Confirmation

Delete a Spark pool with interactive confirmation.

```
fab rm ws1.Workspace/.sparkpools/test-pool.SparkPool
```

#### Force Remove Spark Pool

Delete a Spark pool without confirmation prompts.

```
fab rm ws1.Workspace/.sparkpools/deprecated-pool.SparkPool -f
```
