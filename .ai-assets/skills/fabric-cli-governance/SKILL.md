---
name: fabric-cli-governance
description: Use Fabric CLI for governance, security, and administration — workspace permissions, domains, capacities, sensitivity labels, and audit. Activate when users need to manage access control, configure governance policies, monitor usage, or troubleshoot permissions.
---

# Fabric CLI Governance & Administration

Expert guidance for managing Microsoft Fabric security, governance, and administration using the `fab` CLI.

## When to Use This Skill

Activate automatically when tasks involve:

- Managing workspace permissions and access control (ACLs)
- Configuring and managing domains
- Capacity assignment and monitoring
- Applying sensitivity labels to items
- Auditing user activities and access patterns
- Setting up row-level security (RLS), column-level security (CLS), or object-level security (OLS)
- Workspace identity and managed identity configuration

## Prerequisites

- Load `fabric-cli-core` skill first for foundational CLI guidance
- User must be authenticated: `fab auth status`
- Admin or Member role required for most governance operations
- Fabric Admin role required for tenant-level operations

## Automation Scripts

Ready-to-use Python scripts for governance tasks. Run any script with `--help` for full options.

| Script | Purpose | Usage |
|--------|---------|-------|
| `audit_workspace.py` | Generate comprehensive workspace audit report | `python scripts/audit_workspace.py <workspace> -o report.json` |
| `bulk_permissions.py` | Apply permissions from CSV/JSON file | `python scripts/bulk_permissions.py <workspace> -i perms.csv` |
| `validate_governance.py` | Check workspace against governance rules | `python scripts/validate_governance.py <workspace> --rules rules.json` |

Scripts are located in the `scripts/` folder of this skill.

## 1 - Workspace Roles and Permissions

### Workspace Role Hierarchy

| Role | Capabilities |
|------|-------------|
| **Admin** | Full control: delete workspace, manage all permissions, all Member capabilities |
| **Member** | Create/modify/share items, add Contributors and Viewers |
| **Contributor** | Create/modify items, cannot share or manage permissions |
| **Viewer** | Read-only access to all items |

### View Workspace Permissions

```bash
# List all workspace permissions
fab acl get "Production.Workspace"

# Get permissions in detailed format
fab acl get "Production.Workspace" -l

# Query specific permission details
fab acl get "Production.Workspace" -q "value[?role=='Admin']"
```

### Manage Workspace Permissions

```bash
# Add user as Contributor
fab acl set "Production.Workspace" -P principal=user@company.com,role=Contributor

# Add security group as Viewer
fab acl set "Production.Workspace" -P principal=DataAnalysts@company.com,role=Viewer,principalType=Group

# Add service principal as Member
fab acl set "Production.Workspace" -P principal=<app-id>,role=Member,principalType=App

# Remove user from workspace
fab acl del "Production.Workspace" -P principal=user@company.com
```

### Bulk Permission Management

```bash
#!/bin/bash
# Add multiple users to workspace
WORKSPACE="Production.Workspace"
USERS=("analyst1@company.com" "analyst2@company.com" "analyst3@company.com")

for USER in "${USERS[@]}"; do
  fab acl set "$WORKSPACE" -P principal=$USER,role=Viewer -f
  echo "Added $USER as Viewer"
done
```

## 2 - Item-Level Permissions

### View Item Permissions

```bash
# Get permissions for specific item
fab acl get "Production.Workspace/Sales.SemanticModel"

# List all shared items in workspace
fab api "workspaces/<ws-id>/items" -q "value[?permissions]"
```

### Share Items

```bash
# Share semantic model with read access
fab acl set "Production.Workspace/Sales.SemanticModel" -P principal=user@company.com,role=Read

# Share with build permission (for semantic models)
fab acl set "Production.Workspace/Sales.SemanticModel" -P principal=user@company.com,role=Build

# Share report
fab acl set "Production.Workspace/SalesReport.Report" -P principal=user@company.com,role=Read
```

### Item Permission Types

| Item Type | Available Permissions |
|-----------|----------------------|
| Semantic Model | Read, Build, Write |
| Report | Read, Write |
| Lakehouse | Read, ReadAll, Write |
| Warehouse | Read, ReadData, Write |
| Notebook | Read, Write |

## 3 - Domain Management

Domains organize workspaces into logical groupings for governance.

### List Domains

```bash
# List all domains (hidden entity)
fab ls .domains -l

# Get domain details
fab get ".domains/Finance.Domain"
```

### Create and Configure Domains

```bash
# Create a new domain
fab mkdir ".domains/Analytics.Domain"

# Create domain with description
fab api -X post "admin/domains" -i '{
  "displayName": "Analytics",
  "description": "Analytics team workspaces"
}'
```

### Assign Workspaces to Domains

```bash
# Get domain ID
DOMAIN_ID=$(fab get ".domains/Analytics.Domain" -q "id" | tr -d '"')

# Assign workspace to domain
fab api -X post "admin/domains/$DOMAIN_ID/assignWorkspaces" -i '{
  "workspacesIds": ["<workspace-id-1>", "<workspace-id-2>"]
}'

# List workspaces in domain
fab api "admin/domains/$DOMAIN_ID/workspaces"
```

### Domain Admins

```bash
# Add domain admin
fab api -X post "admin/domains/$DOMAIN_ID/roleAssignments" -i '{
  "principals": [{"id": "<user-id>", "type": "User"}],
  "role": "Admins"
}'

# List domain admins
fab api "admin/domains/$DOMAIN_ID/roleAssignments"
```

## 4 - Capacity Management

### List Capacities

```bash
# List all capacities (hidden entity)
fab ls .capacities -l

# Get capacity details
fab get ".capacities/FabricCapacity1.Capacity"

# Get capacity ID
CAPACITY_ID=$(fab get ".capacities/FabricCapacity1.Capacity" -q "id" | tr -d '"')
```

### Assign Workspace to Capacity

```bash
# Assign workspace to capacity
fab assign "Production.Workspace" -P capacityId=$CAPACITY_ID

# Unassign workspace from capacity (moves to shared capacity)
fab unassign "Production.Workspace"

# Create workspace on specific capacity
fab mkdir "NewWorkspace.Workspace" -P capacityname=FabricCapacity1
```

### Monitor Capacity Usage

```bash
# Get capacity metrics via Azure API
SUBSCRIPTION_ID="<subscription-id>"
RESOURCE_GROUP="<resource-group>"
CAPACITY_NAME="<capacity-name>"

fab api -A azure "subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Fabric/capacities/$CAPACITY_NAME?api-version=2023-11-01"

# List all Fabric capacities in subscription
fab api -A azure "subscriptions/$SUBSCRIPTION_ID/providers/Microsoft.Fabric/capacities?api-version=2023-11-01"
```

### Capacity SKUs

```bash
# Get available SKUs
fab api -A azure "subscriptions/$SUBSCRIPTION_ID/providers/Microsoft.Fabric/skus?api-version=2023-11-01"
```

## 5 - Sensitivity Labels

### List Available Labels

```bash
# Get sensitivity labels from Purview
fab api "admin/labels"

# Query label details
fab api "admin/labels" -q "value[?name=='Confidential']"
```

### Apply Labels to Items

```bash
# Get workspace and item IDs
WS_ID=$(fab get "Production.Workspace" -q "id" | tr -d '"')
ITEM_ID=$(fab get "Production.Workspace/Sales.SemanticModel" -q "id" | tr -d '"')
LABEL_ID="<label-id>"

# Apply label via API
fab api -X post "workspaces/$WS_ID/items/$ITEM_ID/applyLabel" -i "{
  \"labelId\": \"$LABEL_ID\"
}"
```

### Bulk Label Application

```bash
#!/bin/bash
# Apply label to all semantic models in workspace
WORKSPACE="Production.Workspace"
LABEL_ID="<confidential-label-id>"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')

# Get all semantic models
MODELS=$(fab api "workspaces/$WS_ID/items" -q "value[?type=='SemanticModel'].id")

for MODEL_ID in $MODELS; do
  fab api -X post "workspaces/$WS_ID/items/$MODEL_ID/applyLabel" -i "{\"labelId\": \"$LABEL_ID\"}"
  echo "Applied label to $MODEL_ID"
done
```

## 6 - Audit and Monitoring

### Access Audit Logs

Fabric audit logs are available through Microsoft Purview or Office 365 Management API.

```bash
# Query activities via Admin API
fab api "admin/activityEvents" -P startDateTime=2024-01-01T00:00:00Z,endDateTime=2024-01-02T00:00:00Z

# Filter by activity type
fab api "admin/activityEvents" -P startDateTime=2024-01-01T00:00:00Z,endDateTime=2024-01-02T00:00:00Z,activityType=ViewReport
```

### Common Audit Queries

```bash
# Get all workspace access events
fab api "admin/activityEvents" -P activityType=GetWorkspaces

# Get all export events
fab api "admin/activityEvents" -P activityType=ExportReport

# Get all sharing events
fab api "admin/activityEvents" -P activityType=ShareReport
```

### Workspace Inventory

```bash
#!/bin/bash
# Generate workspace inventory report
echo "Workspace,ItemCount,Capacity,Domain" > inventory.csv

WORKSPACES=$(fab api workspaces -q "value[].{name: displayName, id: id}")

echo "$WORKSPACES" | jq -r '.[] | [.name, .id] | @tsv' | while IFS=$'\t' read -r NAME ID; do
  ITEM_COUNT=$(fab api "workspaces/$ID/items" -q "value | length")
  # Get capacity and domain info
  WS_INFO=$(fab get "$NAME.Workspace" -v)
  echo "$NAME,$ITEM_COUNT,..." >> inventory.csv
done
```

## 7 - Managed Identities

### List Workspace Managed Identities

```bash
# List managed identities (hidden entity)
fab ls "Production.Workspace/.managedidentities"

# Get managed identity details
fab get "Production.Workspace/.managedidentities/default.ManagedIdentity"
```

### Configure Workspace Identity

```bash
WS_ID=$(fab get "Production.Workspace" -q "id" | tr -d '"')

# Create workspace identity
fab api -X post "workspaces/$WS_ID/assignToCapacity" -i '{
  "identityType": "SystemAssigned"
}'
```

## 8 - Connections and Gateways

### List Connections

```bash
# List all connections (hidden entity)
fab ls .connections -l

# Get connection details
fab get ".connections/SQLServerConnection.Connection"
```

### List Gateways

```bash
# List all gateways (hidden entity)
fab ls .gateways -l

# Get gateway details
fab get ".gateways/OnPremGateway.Gateway"

# List data sources on gateway
GATEWAY_ID=$(fab get ".gateways/OnPremGateway.Gateway" -q "id" | tr -d '"')
fab api -A powerbi "gateways/$GATEWAY_ID/datasources"
```

## 9 - Security Patterns

### Row-Level Security (RLS)

RLS is configured within semantic models. Use CLI to manage model definitions:

```bash
# Export model with RLS configuration
fab export "Production.Workspace/Sales.SemanticModel" -o ./model-backup -f

# The TMDL definition contains RLS roles
# Edit definition/roles/*.tmdl files

# Re-import updated model
fab import "Production.Workspace/Sales.SemanticModel" -i ./model-backup/Sales.SemanticModel -f
```

### OneLake Security

```bash
# Configure OneLake data access roles via API
WS_ID=$(fab get "Production.Workspace" -q "id" | tr -d '"')
LH_ID=$(fab get "Production.Workspace/Sales.Lakehouse" -q "id" | tr -d '"')

# Get current data access roles
fab api "workspaces/$WS_ID/lakehouses/$LH_ID/dataAccessRoles"
```

## 10 - Governance Best Practices

### Permission Audit Checklist

```bash
#!/bin/bash
# Audit script for workspace permissions

WORKSPACE="Production.Workspace"

echo "=== Permission Audit for $WORKSPACE ==="

# List all permissions
echo "Current Permissions:"
fab acl get "$WORKSPACE" -l

# Check for overly permissive access
echo "Users with Admin role:"
fab acl get "$WORKSPACE" -q "value[?role=='Admin']"

# Check service principals
echo "Service Principals with access:"
fab acl get "$WORKSPACE" -q "value[?principalType=='App']"
```

### Security Recommendations

1. **Principle of least privilege** - Grant minimum required permissions
2. **Use security groups** - Manage permissions via groups, not individuals
3. **Regular audits** - Review permissions quarterly
4. **Service principal rotation** - Rotate credentials regularly
5. **Sensitivity labels** - Apply labels to classify data
6. **Domain organization** - Group workspaces by business function
7. **Capacity isolation** - Separate dev/prod workloads

## 11 - Common Governance Tasks

### Offboard User

```bash
#!/bin/bash
# Remove user from all workspaces
USER="departing.user@company.com"

WORKSPACES=$(fab api workspaces -q "value[].displayName")

for WS in $WORKSPACES; do
  fab acl del "$WS.Workspace" -P principal=$USER -f 2>/dev/null && \
    echo "Removed from $WS" || echo "Not in $WS"
done
```

### Transfer Ownership

```bash
# Transfer workspace admin
OLD_ADMIN="old.admin@company.com"
NEW_ADMIN="new.admin@company.com"
WORKSPACE="Production.Workspace"

# Add new admin first
fab acl set "$WORKSPACE" -P principal=$NEW_ADMIN,role=Admin -f

# Then remove old admin
fab acl del "$WORKSPACE" -P principal=$OLD_ADMIN -f
```

## 12 - References

For detailed governance patterns, see:

- [references/workspace-permissions.md](./references/workspace-permissions.md) — ACL patterns and examples
- [references/domain-management.md](./references/domain-management.md) — Domain configuration
- [references/capacity-operations.md](./references/capacity-operations.md) — Capacity management
- [references/sensitivity-labels.md](./references/sensitivity-labels.md) — Label application
- [references/audit-patterns.md](./references/audit-patterns.md) — Audit and monitoring
