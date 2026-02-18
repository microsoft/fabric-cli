# Workspace Permissions Reference

Comprehensive guide to managing workspace and item permissions with the Fabric CLI.

## Workspace Role Capabilities

### Admin Role

```bash
# Full capabilities:
# - Delete workspace
# - Add/remove all roles
# - Manage permissions
# - All Member capabilities
fab acl set "Workspace.Workspace" -P principal=user@company.com,role=Admin
```

### Member Role

```bash
# Capabilities:
# - Create/modify/delete items
# - Share items with others
# - Add Contributors and Viewers
# - Cannot add Admins or Members
fab acl set "Workspace.Workspace" -P principal=user@company.com,role=Member
```

### Contributor Role

```bash
# Capabilities:
# - Create/modify/delete items
# - Cannot share items
# - Cannot manage permissions
fab acl set "Workspace.Workspace" -P principal=user@company.com,role=Contributor
```

### Viewer Role

```bash
# Capabilities:
# - View all items
# - Run queries (SQL/DAX)
# - Cannot modify items
# - Cannot access OneLake directly
fab acl set "Workspace.Workspace" -P principal=user@company.com,role=Viewer
```

## Principal Types

### User Principals

```bash
# Add individual user
fab acl set "Workspace.Workspace" -P principal=user@company.com,role=Contributor

# Using object ID
fab acl set "Workspace.Workspace" -P principal=<user-object-id>,role=Contributor,principalType=User
```

### Security Groups

```bash
# Add security group (recommended for scale)
fab acl set "Workspace.Workspace" -P principal=DataEngineers@company.com,role=Contributor,principalType=Group

# Using group object ID
fab acl set "Workspace.Workspace" -P principal=<group-object-id>,role=Viewer,principalType=Group
```

### Service Principals

```bash
# Add service principal (for automation)
fab acl set "Workspace.Workspace" -P principal=<app-id>,role=Contributor,principalType=App

# Service principal for CI/CD
fab acl set "Production.Workspace" -P principal=<cicd-app-id>,role=Member,principalType=App
```

## Viewing Permissions

### List All Permissions

```bash
# Basic listing
fab acl get "Workspace.Workspace"

# Detailed output
fab acl get "Workspace.Workspace" -l

# JSON output for parsing
fab acl get "Workspace.Workspace" -o json
```

### Filter Permissions

```bash
# Get admins only
fab acl get "Workspace.Workspace" -q "value[?role=='Admin']"

# Get service principals
fab acl get "Workspace.Workspace" -q "value[?principalType=='App']"

# Get specific user
fab acl get "Workspace.Workspace" -q "value[?principal=='user@company.com']"
```

## Removing Permissions

```bash
# Remove user
fab acl del "Workspace.Workspace" -P principal=user@company.com

# Remove with force (no confirmation)
fab acl del "Workspace.Workspace" -P principal=user@company.com -f

# Remove service principal
fab acl del "Workspace.Workspace" -P principal=<app-id>
```

## Item-Level Permissions

### Share Semantic Model

```bash
# Read permission (view only)
fab acl set "Workspace.Workspace/Model.SemanticModel" -P principal=user@company.com,role=Read

# Build permission (connect and create reports)
fab acl set "Workspace.Workspace/Model.SemanticModel" -P principal=user@company.com,role=Build

# Write permission (full access)
fab acl set "Workspace.Workspace/Model.SemanticModel" -P principal=user@company.com,role=Write
```

### Share Report

```bash
# Share report for viewing
fab acl set "Workspace.Workspace/Report.Report" -P principal=user@company.com,role=Read

# Share with edit permission
fab acl set "Workspace.Workspace/Report.Report" -P principal=user@company.com,role=Write
```

### Share Lakehouse

```bash
# Read access
fab acl set "Workspace.Workspace/LH.Lakehouse" -P principal=user@company.com,role=Read

# Full data access
fab acl set "Workspace.Workspace/LH.Lakehouse" -P principal=user@company.com,role=ReadAll
```

## Bulk Operations

### Add Multiple Users

```bash
#!/bin/bash
WORKSPACE="Production.Workspace"
ROLE="Viewer"

# Users file: one email per line
while read USER; do
  fab acl set "$WORKSPACE" -P principal=$USER,role=$ROLE -f
  echo "Added $USER as $ROLE"
done < users.txt
```

### Clone Permissions Between Workspaces

```bash
#!/bin/bash
SOURCE_WS="Dev.Workspace"
TARGET_WS="Test.Workspace"

# Export source permissions
fab acl get "$SOURCE_WS" -o json > /tmp/permissions.json

# Apply to target (parse and apply each)
jq -r '.value[] | [.principal, .role, .principalType] | @tsv' /tmp/permissions.json | \
while IFS=$'\t' read -r PRINCIPAL ROLE TYPE; do
  fab acl set "$TARGET_WS" -P principal=$PRINCIPAL,role=$ROLE,principalType=$TYPE -f
done
```

### Audit All Workspace Permissions

```bash
#!/bin/bash
# Generate permission report across all workspaces
echo "Workspace,Principal,Role,Type" > permissions-audit.csv

for WS in $(fab ls -q "value[].displayName"); do
  fab acl get "$WS.Workspace" -o json | \
  jq -r ".value[] | [\"$WS\", .principal, .role, .principalType] | @csv" >> permissions-audit.csv
done
```

## Permission Inheritance

### Workspace to Item

- Workspace Admins/Members/Contributors → Full item access
- Workspace Viewers → Read-only item access
- Item-level permissions can extend (not restrict) workspace permissions

### Sharing with External Users

```bash
# External sharing must be enabled by admin
# Then share with external user
fab acl set "Workspace.Workspace/Report.Report" -P principal=external@partner.com,role=Read
```

## Troubleshooting

### Permission Denied Errors

```bash
# Check your current permissions
fab acl get "Workspace.Workspace" -q "value[?principal=='<your-email>']"

# Verify authentication
fab auth status
```

### Cannot Add Permissions

```bash
# Verify you have Admin or Member role
fab acl get "Workspace.Workspace" -l

# Check if user exists in tenant
# Contact Azure AD admin if user not found
```

### Service Principal Access Issues

```bash
# Verify SPN has Fabric API permissions in Azure AD
# Check tenant admin settings for SPN access to Fabric
# Ensure SPN is added with correct principalType=App
fab acl set "Workspace.Workspace" -P principal=<app-id>,role=Contributor,principalType=App
```
