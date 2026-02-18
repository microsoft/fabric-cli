---
name: fabric-cli-cicd
description: Use for CI/CD pipelines, deployment automation, environment promotion, and Git integration with Microsoft Fabric CLI. Activate when deploying Fabric items, setting up GitHub Actions or Azure Pipelines, or automating environment migrations.
---

# Fabric CLI CI/CD Operations

Expert guidance for automating Microsoft Fabric deployments using the `fab` CLI in CI/CD pipelines.

## When to Use This Skill

Activate automatically when tasks involve:

- Setting up deployment pipelines (GitHub Actions, Azure Pipelines)
- Environment promotion (dev → test → prod)
- Automating Fabric item exports/imports
- Git-based source control for Fabric definitions
- Scheduling and orchestrating Fabric operations
- Service principal authentication for automation

## Prerequisites

- Load `fabric-cli-core` skill first for foundational guidance
- User must have appropriate workspace permissions in target environments
- Service principal with Fabric API permissions recommended for automation
- `fab` CLI installed in pipeline environment (`pip install ms-fabric-cli`)

## Automation Scripts

Ready-to-use Python scripts for CI/CD automation. Run any script with `--help` for full options.

| Script | Purpose | Usage |
|--------|---------|-------|
| `deploy.py` | Deploy items from local folder to workspace | `python scripts/deploy.py <source> <target-ws> [--dry-run]` |
| `export_workspace.py` | Export all workspace items for version control | `python scripts/export_workspace.py <workspace> -o <dir>` |
| `diff_definitions.py` | Compare item definitions between environments | `python scripts/diff_definitions.py <item1> <item2>` |

Scripts are located in the `scripts/` folder of this skill.

## 1 - Authentication for CI/CD

### Service Principal Setup (Recommended)

Use environment variables for secure, non-interactive authentication:

```bash
# Required environment variables
export FAB_SPN_TENANT_ID="<tenant-id>"
export FAB_SPN_CLIENT_ID="<client-id>"
export FAB_SPN_CLIENT_SECRET="<client-secret>"  # Or use certificate/federated

# Authenticate
fab auth login --service-principal

# Verify
fab auth status
```

### Authentication Methods by Priority

| Method | Use Case | Security |
|--------|----------|----------|
| Federated credential | GitHub Actions, Azure Pipelines | Best (no secrets) |
| Certificate | Long-running automation | Good |
| Client secret | Simple automation | Rotate regularly |
| Managed identity | Azure-hosted runners | Best (no credentials) |

### Federated Credential (GitHub Actions)

```bash
export FAB_SPN_TENANT_ID="<tenant-id>"
export FAB_SPN_CLIENT_ID="<client-id>"
export FAB_SPN_FEDERATED_TOKEN="$ACTIONS_ID_TOKEN"

fab auth login --service-principal --federated
```

## 2 - Export/Import Patterns

### Export Items for Version Control

```bash
# Export single item
fab export "Dev.Workspace/Pipeline.DataPipeline" -o ./fabric-items/ -f

# Export entire workspace
fab export "Dev.Workspace" -o ./fabric-items/ -a -f

# Export with specific format
fab get "Dev.Workspace/Model.SemanticModel" -q "definition" > ./definitions/model.json
```

### Import Items to Target Environment

```bash
# Import single item (create or update)
fab import "Prod.Workspace/Pipeline.DataPipeline" -i ./fabric-items/Pipeline.DataPipeline -f

# Import with new name
fab import "Prod.Workspace/Pipeline-v2.DataPipeline" -i ./fabric-items/Pipeline.DataPipeline -f
```

### Critical Flags for Automation

| Flag | Purpose | Always Use? |
|------|---------|-------------|
| `-f` | Force (skip prompts) | Yes in CI/CD |
| `-a` | All items (export) | When exporting workspace |
| `-o` | Output directory | For exports |
| `-i` | Input file/directory | For imports |

## 3 - Environment Promotion Strategy

### Recommended Folder Structure

```
repo/
├── .github/
│   └── workflows/
│       └── deploy-fabric.yml
├── fabric-items/
│   ├── pipelines/
│   │   └── ETL.DataPipeline/
│   ├── notebooks/
│   │   └── Transform.Notebook/
│   └── semantic-models/
│       └── Sales.SemanticModel/
└── config/
    ├── dev.env
    ├── test.env
    └── prod.env
```

### Promotion Workflow

```bash
# 1. Export from source environment
fab export "Dev.Workspace" -o ./fabric-items/ -a -f

# 2. Commit to Git (manual or automated)
git add ./fabric-items/
git commit -m "Export from Dev"

# 3. Import to target environment (in pipeline)
fab import "Test.Workspace/Pipeline.DataPipeline" -i ./fabric-items/pipelines/ETL.DataPipeline -f
fab import "Test.Workspace/Notebook.Notebook" -i ./fabric-items/notebooks/Transform.Notebook -f
```

### Environment-Specific Configuration

```bash
# Use different workspaces per environment
DEV_WORKSPACE="Dev.Workspace"
TEST_WORKSPACE="Test.Workspace"
PROD_WORKSPACE="Prod.Workspace"

# Parameterize deployment
TARGET_WORKSPACE="${ENV}.Workspace"
fab import "$TARGET_WORKSPACE/Item.Type" -i ./fabric-items/Item.Type -f
```

## 4 - Error Handling in Pipelines

### Verify Before Deploy

```bash
# Check target exists
fab exists "$TARGET_WORKSPACE" || { echo "Workspace not found"; exit 1; }

# Check auth is valid
fab auth status || { echo "Not authenticated"; exit 1; }

# Check item exists before update
fab exists "$TARGET_WORKSPACE/$ITEM_NAME" && echo "Will update existing item"
```

### Capture and Log Errors

```bash
# Bash pattern with error capture
if ! fab import "$TARGET/Item.Type" -i ./Item.Type -f 2>&1 | tee deploy.log; then
    echo "::error::Deployment failed. See deploy.log"
    exit 1
fi
```

### Rollback Strategy

```bash
# Before deployment, backup current state
fab export "$PROD_WORKSPACE/$ITEM" -o ./backup/ -f

# If deployment fails, restore from backup
fab import "$PROD_WORKSPACE/$ITEM" -i ./backup/$ITEM -f
```

## 5 - Secrets Management

### GitHub Actions Secrets

```yaml
env:
  FAB_SPN_TENANT_ID: ${{ secrets.FABRIC_TENANT_ID }}
  FAB_SPN_CLIENT_ID: ${{ secrets.FABRIC_CLIENT_ID }}
  FAB_SPN_CLIENT_SECRET: ${{ secrets.FABRIC_CLIENT_SECRET }}
```

### Azure Pipelines Variable Groups

```yaml
variables:
  - group: fabric-credentials  # Contains TENANT_ID, CLIENT_ID, CLIENT_SECRET
```

### Never Do This

- Do not hardcode secrets in scripts
- Do not echo/print secrets in logs
- Do not commit secrets to Git
- Do not use secrets in item names or paths

## 6 - Common CI/CD Tasks

### Deploy Changed Items Only

```bash
# Get list of changed files from Git
CHANGED=$(git diff --name-only HEAD~1 -- fabric-items/)

for ITEM_PATH in $CHANGED; do
    ITEM_NAME=$(basename "$ITEM_PATH")
    fab import "$TARGET_WORKSPACE/$ITEM_NAME" -i "$ITEM_PATH" -f
done
```

### Run Post-Deployment Jobs

```bash
# Trigger notebook after deployment
fab job run "$TARGET_WORKSPACE/PostDeploy.Notebook" --timeout 600

# Refresh semantic model
WS_ID=$(fab get "$TARGET_WORKSPACE" -q "id" | tr -d '"')
MODEL_ID=$(fab get "$TARGET_WORKSPACE/Model.SemanticModel" -q "id" | tr -d '"')
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{"type":"Full"}'
```

### Validate Deployment

```bash
# Verify item exists after import
fab exists "$TARGET_WORKSPACE/$ITEM" || { echo "Deployment verification failed"; exit 1; }

# Check job completed successfully
STATUS=$(fab job run-status "$TARGET_WORKSPACE/Notebook.Notebook" --id "$JOB_ID" -q "status")
[[ "$STATUS" == "Completed" ]] || exit 1
```

## 7 - References

For detailed examples and patterns, see:

- [GitHub Actions](./references/github-actions.md) — Complete workflow examples
- [Azure Pipelines](./references/azure-pipelines.md) — Pipeline YAML templates
- [Environment Promotion](./references/environment-promotion.md) — Dev/test/prod strategies
- [Git Integration](./references/git-integration.md) — Source control patterns
- [Automation Patterns](./references/automation-patterns.md) — Scripts and error handling
