# Environment Promotion Strategies

Patterns for promoting Fabric items across development, test, and production environments.

## Environment Architecture

### Recommended Setup

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Development    │───▶│     Testing     │───▶│   Production    │
│   .Workspace    │    │   .Workspace    │    │   .Workspace    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
       │                       │                       │
       ▼                       ▼                       ▼
   Dev Capacity           Test Capacity          Prod Capacity
```

### Workspace Naming Convention

| Environment | Workspace Name | Purpose |
|-------------|----------------|---------|
| Development | `ProjectName-Dev.Workspace` | Active development |
| Testing | `ProjectName-Test.Workspace` | QA and validation |
| Production | `ProjectName-Prod.Workspace` | Live workloads |

## Full Workspace Promotion

### Export Entire Workspace

```bash
# Export all items from source
fab export "Dev.Workspace" -o ./export/ -a -f

# Directory structure created:
# ./export/
# ├── Pipeline1.DataPipeline/
# ├── Pipeline2.DataPipeline/
# ├── Notebook1.Notebook/
# ├── Model1.SemanticModel/
# └── Report1.Report/
```

### Import to Target Workspace

```bash
# Import each item type
for ITEM in ./export/*; do
    ITEM_NAME=$(basename "$ITEM")
    fab import "Test.Workspace/$ITEM_NAME" -i "$ITEM" -f
done
```

### Selective Promotion

```bash
# Promote only specific items
ITEMS_TO_PROMOTE=(
    "ETL-Pipeline.DataPipeline"
    "Transform.Notebook"
    "Sales-Model.SemanticModel"
)

for ITEM in "${ITEMS_TO_PROMOTE[@]}"; do
    fab import "Test.Workspace/$ITEM" -i "./export/$ITEM" -f
done
```

## Parameterized Deployments

### Environment Configuration Files

```bash
# config/dev.env
WORKSPACE_NAME="Dev.Workspace"
LAKEHOUSE_NAME="DevLakehouse"
CONNECTION_STRING="dev-connection"

# config/prod.env
WORKSPACE_NAME="Prod.Workspace"
LAKEHOUSE_NAME="ProdLakehouse"
CONNECTION_STRING="prod-connection"
```

### Load Environment Config

```bash
#!/bin/bash
# deploy.sh

ENV=${1:-dev}
source "./config/$ENV.env"

echo "Deploying to $WORKSPACE_NAME"

fab import "$WORKSPACE_NAME/Pipeline.DataPipeline" -i ./fabric-items/Pipeline.DataPipeline -f
```

### Parameter Substitution in Definitions

For items with environment-specific settings:

```bash
# Export definition
fab get "Dev.Workspace/Pipeline.DataPipeline" -q "definition" > pipeline-def.json

# Substitute parameters (using jq or sed)
cat pipeline-def.json | \
    sed "s/DevLakehouse/$TARGET_LAKEHOUSE/g" | \
    sed "s/dev-connection/$TARGET_CONNECTION/g" \
    > pipeline-def-updated.json

# Import with updated definition
fab set "Prod.Workspace/Pipeline.DataPipeline" -q definition -i pipeline-def-updated.json
```

## Promotion Workflows

### Manual Promotion Script

```bash
#!/bin/bash
# promote.sh - Promote items from one environment to another

SOURCE_ENV=$1
TARGET_ENV=$2

if [ -z "$SOURCE_ENV" ] || [ -z "$TARGET_ENV" ]; then
    echo "Usage: ./promote.sh <source-env> <target-env>"
    echo "Example: ./promote.sh dev test"
    exit 1
fi

SOURCE_WS="${SOURCE_ENV^}.Workspace"  # Capitalize
TARGET_WS="${TARGET_ENV^}.Workspace"

echo "Promoting from $SOURCE_WS to $TARGET_WS"

# Create temp directory
EXPORT_DIR=$(mktemp -d)

# Export from source
echo "Exporting from $SOURCE_WS..."
fab export "$SOURCE_WS" -o "$EXPORT_DIR" -a -f

# Import to target
echo "Importing to $TARGET_WS..."
for ITEM in "$EXPORT_DIR"/*; do
    ITEM_NAME=$(basename "$ITEM")
    echo "  - $ITEM_NAME"
    fab import "$TARGET_WS/$ITEM_NAME" -i "$ITEM" -f
done

# Cleanup
rm -rf "$EXPORT_DIR"

echo "Promotion complete"
```

### Promotion with Approval Gate

```bash
#!/bin/bash
# promote-with-approval.sh

SOURCE_WS="Test.Workspace"
TARGET_WS="Prod.Workspace"

# List items to promote
echo "Items to promote from $SOURCE_WS:"
fab ls "$SOURCE_WS" -l

# Prompt for approval
read -p "Proceed with promotion to $TARGET_WS? (yes/no): " APPROVAL

if [ "$APPROVAL" != "yes" ]; then
    echo "Promotion cancelled"
    exit 0
fi

# Backup current production
echo "Creating backup of $TARGET_WS..."
fab export "$TARGET_WS" -o "./backup/$(date +%Y%m%d)" -a -f

# Perform promotion
echo "Promoting items..."
fab export "$SOURCE_WS" -o ./temp-export -a -f

for ITEM in ./temp-export/*; do
    ITEM_NAME=$(basename "$ITEM")
    fab import "$TARGET_WS/$ITEM_NAME" -i "$ITEM" -f
done

rm -rf ./temp-export
echo "Promotion complete"
```

## Dependency-Aware Promotion

### Order of Deployment

Deploy items in dependency order:

```bash
# 1. Data stores first (lakehouses, warehouses)
fab import "$TARGET/DataLakehouse.Lakehouse" -i ./items/DataLakehouse.Lakehouse -f

# 2. Semantic models (depend on data stores)
fab import "$TARGET/SalesModel.SemanticModel" -i ./items/SalesModel.SemanticModel -f

# 3. Reports (depend on semantic models)
fab import "$TARGET/SalesReport.Report" -i ./items/SalesReport.Report -f

# 4. Pipelines and notebooks (may depend on any above)
fab import "$TARGET/ETL.DataPipeline" -i ./items/ETL.DataPipeline -f
fab import "$TARGET/Transform.Notebook" -i ./items/Transform.Notebook -f
```

### Dependency Mapping File

```yaml
# dependencies.yml
items:
  - name: DataLakehouse.Lakehouse
    depends_on: []
    
  - name: SalesModel.SemanticModel
    depends_on:
      - DataLakehouse.Lakehouse
      
  - name: SalesReport.Report
    depends_on:
      - SalesModel.SemanticModel
      
  - name: ETL.DataPipeline
    depends_on:
      - DataLakehouse.Lakehouse
```

## Rollback Strategies

### Immediate Rollback

```bash
#!/bin/bash
# rollback.sh

BACKUP_DIR=$1
TARGET_WS=$2

if [ -z "$BACKUP_DIR" ] || [ -z "$TARGET_WS" ]; then
    echo "Usage: ./rollback.sh <backup-dir> <target-workspace>"
    exit 1
fi

echo "Rolling back $TARGET_WS from $BACKUP_DIR"

for ITEM in "$BACKUP_DIR"/*; do
    ITEM_NAME=$(basename "$ITEM")
    echo "Restoring $ITEM_NAME..."
    fab import "$TARGET_WS/$ITEM_NAME" -i "$ITEM" -f
done

echo "Rollback complete"
```

### Versioned Backups

```bash
# Create timestamped backup before each deployment
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
fab export "$PROD_WS" -o "$BACKUP_DIR" -a -f

# Keep last N backups
ls -dt ./backups/*/ | tail -n +6 | xargs rm -rf
```

## Validation After Promotion

### Verify Items Exist

```bash
#!/bin/bash
# validate-deployment.sh

TARGET_WS=$1
EXPECTED_ITEMS=(
    "ETL.DataPipeline"
    "Transform.Notebook"
    "SalesModel.SemanticModel"
    "SalesReport.Report"
)

FAILED=0

for ITEM in "${EXPECTED_ITEMS[@]}"; do
    if fab exists "$TARGET_WS/$ITEM"; then
        echo "[OK] $ITEM exists"
    else
        echo "[FAILED] $ITEM NOT FOUND"
        FAILED=1
    fi
done

exit $FAILED
```

### Run Smoke Tests

```bash
# Run validation notebook
fab job run "$TARGET_WS/ValidationTests.Notebook" --timeout 300

# Check semantic model refresh
WS_ID=$(fab get "$TARGET_WS" -q "id" | tr -d '"')
MODEL_ID=$(fab get "$TARGET_WS/SalesModel.SemanticModel" -q "id" | tr -d '"')

# Trigger test refresh
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{"type":"Full"}'

# Wait and check status
sleep 60
STATUS=$(fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes?\$top=1" -q "value[0].status")
echo "Refresh status: $STATUS"
```

## Best Practices

### Do's

- Always backup before promoting to production
- Use consistent naming across environments
- Validate deployments with automated tests
- Keep promotion scripts in version control
- Use environment-specific configuration files
- Deploy in dependency order

### Don'ts

- Do not promote directly from dev to prod (skip test)
- Do not promote without backups
- Do not hardcode environment-specific values in items
- Do not ignore failed deployments
- Do not promote during business hours (for prod)
