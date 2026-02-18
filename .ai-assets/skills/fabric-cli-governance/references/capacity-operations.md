# Capacity Operations Reference

Guide to managing Fabric capacities, workspace assignment, and capacity monitoring.

## Understanding Capacities

Fabric capacities are compute resources that power your workloads. Types include:

| Capacity Type | Description | SKUs |
|--------------|-------------|------|
| Fabric Capacity | Full Fabric features | F2, F4, F8, F16, F32, F64, F128, F256, F512, F1024, F2048 |
| Power BI Premium | Power BI focused | P1, P2, P3, P4, P5 |
| Power BI Embedded | Embedding scenarios | A1-A6, EM1-EM3 |

## Listing Capacities

```bash
# List all capacities (hidden entity)
fab ls .capacities

# List with details
fab ls .capacities -l

# Get specific capacity
fab get ".capacities/FabricProd.Capacity"

# Get capacity ID
CAPACITY_ID=$(fab get ".capacities/FabricProd.Capacity" -q "id" | tr -d '"')
```

## Workspace Assignment

### Assign Workspace to Capacity

```bash
# Assign using capacity ID
CAPACITY_ID=$(fab get ".capacities/FabricProd.Capacity" -q "id" | tr -d '"')
fab assign "Production.Workspace" -P capacityId=$CAPACITY_ID

# Force assignment (skip confirmation)
fab assign "Production.Workspace" -P capacityId=$CAPACITY_ID -f
```

### Assign During Workspace Creation

```bash
# Create workspace on specific capacity (by name)
fab mkdir "NewWorkspace.Workspace" -P capacityname=FabricProd

# Create workspace with no capacity (shared)
fab mkdir "NewWorkspace.Workspace" -P capacityname=none
```

### Unassign from Capacity

```bash
# Move workspace to shared capacity
fab unassign "Production.Workspace"

# Force unassignment
fab unassign "Production.Workspace" -f
```

### Check Workspace Capacity Assignment

```bash
# Get workspace details including capacity
fab get "Production.Workspace" -v

# Query capacity assignment
fab get "Production.Workspace" -q "capacityId"
```

## Capacity Administration via Azure

### List Capacities in Subscription

```bash
SUBSCRIPTION_ID="<subscription-id>"

# List all Fabric capacities
fab api -A azure "subscriptions/$SUBSCRIPTION_ID/providers/Microsoft.Fabric/capacities?api-version=2023-11-01"

# Filter by resource group
RESOURCE_GROUP="<resource-group>"
fab api -A azure "subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Fabric/capacities?api-version=2023-11-01"
```

### Get Capacity Details

```bash
CAPACITY_NAME="fabricprod"

fab api -A azure "subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Fabric/capacities/$CAPACITY_NAME?api-version=2023-11-01"
```

### Available SKUs

```bash
# List all available Fabric SKUs
fab api -A azure "subscriptions/$SUBSCRIPTION_ID/providers/Microsoft.Fabric/skus?api-version=2023-11-01"

# List SKUs available in specific location
fab api -A azure "subscriptions/$SUBSCRIPTION_ID/providers/Microsoft.Fabric/locations/eastus/skus?api-version=2023-11-01"
```

## Capacity Operations

### Pause Capacity

```bash
# Pause capacity (stops billing)
fab api -A azure -X post "subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Fabric/capacities/$CAPACITY_NAME/suspend?api-version=2023-11-01"
```

### Resume Capacity

```bash
# Resume paused capacity
fab api -A azure -X post "subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Fabric/capacities/$CAPACITY_NAME/resume?api-version=2023-11-01"
```

### Scale Capacity

```bash
# Scale to different SKU
fab api -A azure -X patch "subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Fabric/capacities/$CAPACITY_NAME?api-version=2023-11-01" -i '{
  "sku": {
    "name": "F64",
    "tier": "Fabric"
  }
}'
```

## Capacity Monitoring

### Get Capacity Metrics

```bash
# Query capacity utilization metrics
fab api -A azure "subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Fabric/capacities/$CAPACITY_NAME/providers/microsoft.insights/metrics?api-version=2023-10-01&metricnames=CapacityUtilization"
```

### Capacity Admin Portal

```bash
# Get capacity settings via admin API
fab api "admin/capacities"

# Get specific capacity
fab api "admin/capacities/$CAPACITY_ID"

# Get workspaces on capacity
fab api "admin/capacities/$CAPACITY_ID/workspaces"
```

## Bulk Capacity Operations

### Move Multiple Workspaces

```bash
#!/bin/bash
CAPACITY_ID="<target-capacity-id>"
WORKSPACES=("Dev.Workspace" "Test.Workspace" "Staging.Workspace")

for WS in "${WORKSPACES[@]}"; do
  fab assign "$WS" -P capacityId=$CAPACITY_ID -f
  echo "Moved $WS to capacity"
done
```

### Capacity Inventory

```bash
#!/bin/bash
echo "Capacity,SKU,WorkspaceCount,State" > capacity-report.csv

# Get all capacities
for CAP in $(fab ls .capacities -q "value[].displayName"); do
  CAP_ID=$(fab get ".capacities/$CAP.Capacity" -q "id" | tr -d '"')
  SKU=$(fab get ".capacities/$CAP.Capacity" -q "sku.name")
  STATE=$(fab get ".capacities/$CAP.Capacity" -q "state")
  WS_COUNT=$(fab api "admin/capacities/$CAP_ID/workspaces" -q "value | length" 2>/dev/null || echo "0")
  echo "$CAP,$SKU,$WS_COUNT,$STATE" >> capacity-report.csv
done
```

### Evacuate Capacity (Move All Workspaces)

```bash
#!/bin/bash
SOURCE_CAPACITY="OldCapacity"
TARGET_CAPACITY_ID="<new-capacity-id>"

SOURCE_ID=$(fab get ".capacities/$SOURCE_CAPACITY.Capacity" -q "id" | tr -d '"')

# Get all workspaces on source capacity
WORKSPACES=$(fab api "admin/capacities/$SOURCE_ID/workspaces" -q "value[].name")

for WS in $WORKSPACES; do
  fab assign "$WS.Workspace" -P capacityId=$TARGET_CAPACITY_ID -f
  echo "Moved $WS"
done
```

## Capacity Planning

### SKU Comparison

| SKU | CU/s | Memory | Best For |
|-----|------|--------|----------|
| F2 | 2 | 3 GB | Dev/test |
| F4 | 4 | 6 GB | Small teams |
| F8 | 8 | 12 GB | Medium workloads |
| F16 | 16 | 24 GB | Production |
| F32 | 32 | 48 GB | Large workloads |
| F64+ | 64+ | 96 GB+ | Enterprise |

### Check Capacity Availability

```bash
# Check if capacity has available resources
fab get ".capacities/FabricProd.Capacity" -q "state"

# Should return "Active" for healthy capacity
```

## Troubleshooting

### Workspace Won't Assign

```bash
# Check capacity state
fab get ".capacities/TargetCapacity.Capacity" -q "state"

# Verify you have capacity admin rights
fab api "admin/capacities/$CAPACITY_ID" -q "admins"
```

### Capacity at Limit

```bash
# Check current utilization
fab api -A azure "subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Fabric/capacities/$CAPACITY_NAME/providers/microsoft.insights/metrics?api-version=2023-10-01&metricnames=CapacityUtilization"

# Consider scaling up or moving workspaces
```

### Permission Errors

- Capacity assignment requires workspace Admin role
- Capacity administration requires Capacity Admin role
- Azure operations require appropriate RBAC permissions
