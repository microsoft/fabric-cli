# Sensitivity Labels Reference

Guide to applying and managing Microsoft Purview sensitivity labels in Fabric.

## Understanding Sensitivity Labels

Sensitivity labels classify and protect data based on organizational policies:

- **Public** — No restrictions
- **Internal** — Organization-internal only
- **Confidential** — Limited access
- **Highly Confidential** — Strict access controls

## Prerequisites

- Sensitivity labels must be configured in Microsoft Purview
- Labels must be published to users
- User needs appropriate Fabric permissions

## Listing Available Labels

```bash
# Get all available sensitivity labels
fab api "admin/labels"

# Query specific label
fab api "admin/labels" -q "value[?name=='Confidential']"

# Get label ID
LABEL_ID=$(fab api "admin/labels" -q "value[?name=='Confidential'].id | [0]" | tr -d '"')
```

## Applying Labels

### Apply Label to Item

```bash
# Get IDs
WS_ID=$(fab get "Production.Workspace" -q "id" | tr -d '"')
ITEM_ID=$(fab get "Production.Workspace/Sales.SemanticModel" -q "id" | tr -d '"')
LABEL_ID="<label-id>"

# Apply label
fab api -X post "workspaces/$WS_ID/items/$ITEM_ID/applyLabel" -i "{
  \"labelId\": \"$LABEL_ID\"
}"
```

### Apply Label with Justification

```bash
# When downgrading label, justification may be required
fab api -X post "workspaces/$WS_ID/items/$ITEM_ID/applyLabel" -i "{
  \"labelId\": \"$LABEL_ID\",
  \"assignmentMethod\": \"Standard\",
  \"justificationText\": \"Data has been declassified per policy\"
}"
```

### Remove Label

```bash
# Remove label from item
fab api -X post "workspaces/$WS_ID/items/$ITEM_ID/removeLabel" -i '{}'
```

## Viewing Item Labels

### Check Item Label

```bash
# Get item details including label
fab get "Production.Workspace/Sales.SemanticModel" -v

# Query label specifically
fab get "Production.Workspace/Sales.SemanticModel" -q "sensitivityLabel"
```

### List Labeled Items in Workspace

```bash
WS_ID=$(fab get "Production.Workspace" -q "id" | tr -d '"')

# Get all items with their labels
fab api "workspaces/$WS_ID/items" -q "value[].{name: displayName, type: type, label: sensitivityLabel}"
```

## Bulk Label Operations

### Apply Label to All Items

```bash
#!/bin/bash
WORKSPACE="Production.Workspace"
LABEL_ID="<confidential-label-id>"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')

# Get all items
ITEMS=$(fab api "workspaces/$WS_ID/items" -q "value[].id")

for ITEM_ID in $ITEMS; do
  ITEM_ID=$(echo $ITEM_ID | tr -d '"')
  fab api -X post "workspaces/$WS_ID/items/$ITEM_ID/applyLabel" -i "{\"labelId\": \"$LABEL_ID\"}" 2>/dev/null && \
    echo "Labeled item $ITEM_ID" || echo "Failed to label $ITEM_ID"
done
```

### Apply Label by Item Type

```bash
#!/bin/bash
WORKSPACE="Production.Workspace"
LABEL_ID="<label-id>"
ITEM_TYPE="SemanticModel"
WS_ID=$(fab get "$WORKSPACE" -q "id" | tr -d '"')

# Get items of specific type
ITEMS=$(fab api "workspaces/$WS_ID/items" -q "value[?type=='$ITEM_TYPE'].id")

for ITEM_ID in $ITEMS; do
  ITEM_ID=$(echo $ITEM_ID | tr -d '"')
  fab api -X post "workspaces/$WS_ID/items/$ITEM_ID/applyLabel" -i "{\"labelId\": \"$LABEL_ID\"}"
  echo "Applied label to $ITEM_ID"
done
```

### Label Audit Report

```bash
#!/bin/bash
echo "Workspace,Item,Type,Label" > label-audit.csv

for WS in $(fab ls -q "value[].displayName"); do
  WS_ID=$(fab get "$WS.Workspace" -q "id" | tr -d '"')
  
  fab api "workspaces/$WS_ID/items" -q "value[]" | \
  jq -r ".[] | [\"$WS\", .displayName, .type, (.sensitivityLabel.labelId // \"none\")] | @csv" >> label-audit.csv
done
```

## Label Policies

### Mandatory Labeling

When mandatory labeling is enabled:

```bash
# All new items must have labels
# Use --label parameter when creating (if supported)
# Or apply immediately after creation

# Create item
fab mkdir "Production.Workspace/NewModel.SemanticModel"

# Apply label
WS_ID=$(fab get "Production.Workspace" -q "id" | tr -d '"')
ITEM_ID=$(fab get "Production.Workspace/NewModel.SemanticModel" -q "id" | tr -d '"')
fab api -X post "workspaces/$WS_ID/items/$ITEM_ID/applyLabel" -i "{\"labelId\": \"$LABEL_ID\"}"
```

### Label Inheritance

Labels can be inherited from:
- Parent workspace
- Source item (when copying)
- Data source

```bash
# When copying items, label may be inherited
fab cp "Source.Workspace/LabeledModel.SemanticModel" "Target.Workspace"

# Verify label was inherited
fab get "Target.Workspace/LabeledModel.SemanticModel" -q "sensitivityLabel"
```

## Label Encryption

### Encrypted Labels

Some labels apply encryption:

```bash
# Items with encrypted labels have restricted access
# Verify label encryption settings
fab api "admin/labels" -q "value[?name=='HighlyConfidential'].encryptionEnabled"
```

### Impact on Operations

- Encrypted items may require additional permissions
- Export operations may be blocked
- Sharing may be restricted

## Compliance Scenarios

### Financial Data Classification

```bash
#!/bin/bash
# Apply financial data labels
FINANCIAL_LABEL=$(fab api "admin/labels" -q "value[?name=='Financial-Confidential'].id | [0]" | tr -d '"')

# Label all financial workspaces
for WS in Finance-Prod Finance-Dev Finance-Reports; do
  WS_ID=$(fab get "$WS.Workspace" -q "id" | tr -d '"')
  ITEMS=$(fab api "workspaces/$WS_ID/items" -q "value[].id")
  
  for ITEM_ID in $ITEMS; do
    fab api -X post "workspaces/$WS_ID/items/$ITEM_ID/applyLabel" -i "{\"labelId\": \"$FINANCIAL_LABEL\"}" 2>/dev/null
  done
done
```

### PII Data Protection

```bash
# Find items potentially containing PII
# Apply appropriate label
PII_LABEL=$(fab api "admin/labels" -q "value[?name=='PII-Restricted'].id | [0]" | tr -d '"')

# Apply to customer data items
fab api -X post "workspaces/$WS_ID/items/$CUSTOMER_DATA_ID/applyLabel" -i "{\"labelId\": \"$PII_LABEL\"}"
```

## Troubleshooting

### Label Not Available

```bash
# Check if label is published to you
fab api "admin/labels"

# Contact Purview admin if label not visible
```

### Cannot Apply Label

- Verify you have Write permission on item
- Check if downgrade requires justification
- Ensure label is in your scope

### Label Conflicts

```bash
# When importing items with different labels
# The import may fail or require resolution
# Check current label before import
fab get "Target.Workspace/ExistingItem.SemanticModel" -q "sensitivityLabel"
```
