# Domain Management Reference

Guide to creating and managing domains for organizing Fabric workspaces.

## Understanding Domains

Domains are logical containers that group workspaces by business function, department, or project. They enable:

- Centralized governance policies
- Delegated administration
- Organized workspace discovery
- Consistent security settings

## Listing Domains

```bash
# List all domains (hidden entity)
fab ls .domains

# List with details
fab ls .domains -l

# Get specific domain
fab get ".domains/Finance.Domain"

# Get domain ID
DOMAIN_ID=$(fab get ".domains/Finance.Domain" -q "id" | tr -d '"')
```

## Creating Domains

### Basic Domain Creation

```bash
# Create domain via CLI
fab mkdir ".domains/Analytics.Domain"

# Create via API with description
fab api -X post "admin/domains" -i '{
  "displayName": "Analytics",
  "description": "Analytics and BI team workspaces"
}'
```

### Domain with Parent

```bash
# Create sub-domain
fab api -X post "admin/domains" -i '{
  "displayName": "Sales Analytics",
  "description": "Sales team analytics",
  "parentDomainId": "<parent-domain-id>"
}'
```

## Managing Domain Workspaces

### Assign Workspaces to Domain

```bash
# Get domain ID
DOMAIN_ID=$(fab get ".domains/Analytics.Domain" -q "id" | tr -d '"')

# Assign single workspace
WS_ID=$(fab get "Production.Workspace" -q "id" | tr -d '"')
fab api -X post "admin/domains/$DOMAIN_ID/assignWorkspaces" -i "{
  \"workspacesIds\": [\"$WS_ID\"]
}"

# Assign multiple workspaces
fab api -X post "admin/domains/$DOMAIN_ID/assignWorkspaces" -i '{
  "workspacesIds": ["<ws-id-1>", "<ws-id-2>", "<ws-id-3>"]
}'
```

### List Workspaces in Domain

```bash
# Get all workspaces assigned to domain
fab api "admin/domains/$DOMAIN_ID/workspaces"

# Count workspaces
fab api "admin/domains/$DOMAIN_ID/workspaces" -q "value | length"
```

### Unassign Workspace from Domain

```bash
fab api -X post "admin/domains/$DOMAIN_ID/unassignWorkspaces" -i "{
  \"workspacesIds\": [\"$WS_ID\"]
}"
```

## Domain Roles

### Domain Admin Role

Domain admins can:
- Manage workspaces assigned to the domain
- Assign domain roles to others
- View all items in domain workspaces

```bash
# Add domain admin
fab api -X post "admin/domains/$DOMAIN_ID/roleAssignments" -i '{
  "principals": [
    {"id": "<user-object-id>", "type": "User"}
  ],
  "role": "Admins"
}'

# Add group as domain admin
fab api -X post "admin/domains/$DOMAIN_ID/roleAssignments" -i '{
  "principals": [
    {"id": "<group-object-id>", "type": "Group"}
  ],
  "role": "Admins"
}'
```

### Domain Contributor Role

Domain contributors can:
- Create workspaces in the domain
- View domain workspaces

```bash
fab api -X post "admin/domains/$DOMAIN_ID/roleAssignments" -i '{
  "principals": [
    {"id": "<user-object-id>", "type": "User"}
  ],
  "role": "Contributors"
}'
```

### List Domain Role Assignments

```bash
# Get all role assignments
fab api "admin/domains/$DOMAIN_ID/roleAssignments"

# Get admins only
fab api "admin/domains/$DOMAIN_ID/roleAssignments" -q "value[?role=='Admins']"
```

### Remove Domain Role

```bash
# Get role assignment ID first
ASSIGNMENT_ID=$(fab api "admin/domains/$DOMAIN_ID/roleAssignments" -q "value[?principals[?id=='<user-id>']].id | [0]" | tr -d '"')

# Remove role assignment
fab api -X delete "admin/domains/$DOMAIN_ID/roleAssignments/$ASSIGNMENT_ID"
```

## Domain Configuration

### Update Domain

```bash
# Update domain name and description
fab api -X patch "admin/domains/$DOMAIN_ID" -i '{
  "displayName": "Updated Name",
  "description": "Updated description"
}'
```

### Delete Domain

```bash
# Delete domain (workspaces become unassigned)
fab api -X delete "admin/domains/$DOMAIN_ID"
```

## Domain Governance Patterns

### Organize by Business Function

```bash
# Create department domains
fab mkdir ".domains/Finance.Domain"
fab mkdir ".domains/Marketing.Domain"
fab mkdir ".domains/Sales.Domain"
fab mkdir ".domains/Engineering.Domain"

# Assign workspaces by department
# Finance workspaces
fab api -X post "admin/domains/<finance-domain-id>/assignWorkspaces" -i '{
  "workspacesIds": ["<finance-ws-1>", "<finance-ws-2>"]
}'
```

### Organize by Environment

```bash
# Create environment domains
fab mkdir ".domains/Development.Domain"
fab mkdir ".domains/Testing.Domain"
fab mkdir ".domains/Production.Domain"
```

### Hierarchical Domain Structure

```bash
# Parent domain for division
fab api -X post "admin/domains" -i '{
  "displayName": "Data Platform"
}'

# Get parent domain ID
PARENT_ID=$(fab get ".domains/DataPlatform.Domain" -q "id" | tr -d '"')

# Child domains for teams
fab api -X post "admin/domains" -i "{
  \"displayName\": \"Data Engineering\",
  \"parentDomainId\": \"$PARENT_ID\"
}"

fab api -X post "admin/domains" -i "{
  \"displayName\": \"Data Science\",
  \"parentDomainId\": \"$PARENT_ID\"
}"
```

## Bulk Domain Operations

### Assign All Team Workspaces

```bash
#!/bin/bash
DOMAIN_ID="<domain-id>"
TEAM_PREFIX="Analytics"

# Find all workspaces starting with team prefix
WS_IDS=$(fab api workspaces -q "value[?starts_with(displayName, '$TEAM_PREFIX')].id")

# Convert to JSON array and assign
echo "{\"workspacesIds\": $WS_IDS}" > /tmp/assign.json
fab api -X post "admin/domains/$DOMAIN_ID/assignWorkspaces" -i /tmp/assign.json
```

### Domain Inventory Report

```bash
#!/bin/bash
echo "Domain,WorkspaceCount,Admins" > domain-report.csv

for DOMAIN in $(fab ls .domains -q "value[].displayName"); do
  DOMAIN_ID=$(fab get ".domains/$DOMAIN.Domain" -q "id" | tr -d '"')
  WS_COUNT=$(fab api "admin/domains/$DOMAIN_ID/workspaces" -q "value | length")
  ADMIN_COUNT=$(fab api "admin/domains/$DOMAIN_ID/roleAssignments" -q "value[?role=='Admins'] | length")
  echo "$DOMAIN,$WS_COUNT,$ADMIN_COUNT" >> domain-report.csv
done
```

## Troubleshooting

### Cannot Create Domain

- Verify you have Fabric Admin role
- Check tenant settings for domain creation

### Cannot Assign Workspace

- Verify workspace exists
- Check if workspace is already assigned to another domain
- Ensure you have domain admin role

### Domain Not Visible

```bash
# Domains are hidden entities, use .domains prefix
fab ls .domains -l

# Or use admin API
fab api "admin/domains"
```
