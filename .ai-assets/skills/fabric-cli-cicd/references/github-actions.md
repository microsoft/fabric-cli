# GitHub Actions for Fabric CLI

Complete workflow examples for deploying Microsoft Fabric items using GitHub Actions.

## Basic Deployment Workflow

```yaml
name: Deploy Fabric Items

on:
  push:
    branches: [main]
    paths:
      - 'fabric-items/**'
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'dev'
        type: choice
        options:
          - dev
          - test
          - prod

env:
  PYTHON_VERSION: '3.11'

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment || 'dev' }}
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Fabric CLI
        run: pip install ms-fabric-cli

      - name: Authenticate with Service Principal
        env:
          FAB_SPN_TENANT_ID: ${{ secrets.FABRIC_TENANT_ID }}
          FAB_SPN_CLIENT_ID: ${{ secrets.FABRIC_CLIENT_ID }}
          FAB_SPN_CLIENT_SECRET: ${{ secrets.FABRIC_CLIENT_SECRET }}
        run: |
          fab auth login --service-principal
          fab auth status

      - name: Deploy items
        env:
          TARGET_WORKSPACE: ${{ vars.FABRIC_WORKSPACE }}
        run: |
          fab import "$TARGET_WORKSPACE/Pipeline.DataPipeline" -i ./fabric-items/Pipeline.DataPipeline -f
          fab import "$TARGET_WORKSPACE/Notebook.Notebook" -i ./fabric-items/Notebook.Notebook -f
```

## Federated Credential Workflow (No Secrets)

```yaml
name: Deploy with Federated Credential

on:
  push:
    branches: [main]

permissions:
  id-token: write  # Required for federated credential
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Fabric CLI
        run: pip install ms-fabric-cli

      - name: Azure Login with OIDC
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Get Federated Token
        run: |
          TOKEN=$(az account get-access-token --resource https://analysis.windows.net/powerbi/api --query accessToken -o tsv)
          echo "FAB_SPN_FEDERATED_TOKEN=$TOKEN" >> $GITHUB_ENV

      - name: Authenticate Fabric CLI
        env:
          FAB_SPN_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
          FAB_SPN_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
        run: |
          fab auth login --service-principal --federated
          fab auth status

      - name: Deploy
        run: |
          fab import "Prod.Workspace/Item.Type" -i ./fabric-items/Item.Type -f
```

## Multi-Environment Deployment

```yaml
name: Multi-Environment Deploy

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options:
          - dev
          - test
          - prod

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup
        run: |
          pip install ms-fabric-cli
          
      - name: Authenticate
        env:
          FAB_SPN_TENANT_ID: ${{ secrets.FABRIC_TENANT_ID }}
          FAB_SPN_CLIENT_ID: ${{ secrets.FABRIC_CLIENT_ID }}
          FAB_SPN_CLIENT_SECRET: ${{ secrets.FABRIC_CLIENT_SECRET }}
        run: fab auth login --service-principal

      - name: Set workspace based on environment
        run: |
          case "${{ github.event.inputs.environment }}" in
            dev)  echo "WORKSPACE=Development.Workspace" >> $GITHUB_ENV ;;
            test) echo "WORKSPACE=Testing.Workspace" >> $GITHUB_ENV ;;
            prod) echo "WORKSPACE=Production.Workspace" >> $GITHUB_ENV ;;
          esac

      - name: Deploy to ${{ github.event.inputs.environment }}
        run: |
          echo "Deploying to $WORKSPACE"
          fab import "$WORKSPACE/Pipeline.DataPipeline" -i ./fabric-items/Pipeline.DataPipeline -f
```

## Deploy Changed Items Only

```yaml
name: Deploy Changed Items

on:
  push:
    branches: [main]
    paths:
      - 'fabric-items/**'

jobs:
  deploy-changes:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2  # Need previous commit for diff

      - name: Setup Fabric CLI
        run: pip install ms-fabric-cli

      - name: Authenticate
        env:
          FAB_SPN_TENANT_ID: ${{ secrets.FABRIC_TENANT_ID }}
          FAB_SPN_CLIENT_ID: ${{ secrets.FABRIC_CLIENT_ID }}
          FAB_SPN_CLIENT_SECRET: ${{ secrets.FABRIC_CLIENT_SECRET }}
        run: fab auth login --service-principal

      - name: Get changed items
        id: changes
        run: |
          CHANGED=$(git diff --name-only HEAD~1 -- fabric-items/ | grep -E '\.(DataPipeline|Notebook|SemanticModel)/' | xargs -I {} dirname {} | sort -u)
          echo "changed=$CHANGED" >> $GITHUB_OUTPUT
          echo "Changed items: $CHANGED"

      - name: Deploy changed items
        env:
          TARGET_WORKSPACE: ${{ vars.FABRIC_WORKSPACE }}
        run: |
          for ITEM_PATH in ${{ steps.changes.outputs.changed }}; do
            ITEM_NAME=$(basename "$ITEM_PATH")
            echo "Deploying $ITEM_NAME..."
            fab import "$TARGET_WORKSPACE/$ITEM_NAME" -i "$ITEM_PATH" -f
          done
```

## Matrix Deployment (Multiple Workspaces)

```yaml
name: Matrix Deploy

on:
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        workspace:
          - name: Sales
            path: sales-items
          - name: Marketing
            path: marketing-items
          - name: Finance
            path: finance-items
      fail-fast: false

    steps:
      - uses: actions/checkout@v4

      - name: Setup and Auth
        env:
          FAB_SPN_TENANT_ID: ${{ secrets.FABRIC_TENANT_ID }}
          FAB_SPN_CLIENT_ID: ${{ secrets.FABRIC_CLIENT_ID }}
          FAB_SPN_CLIENT_SECRET: ${{ secrets.FABRIC_CLIENT_SECRET }}
        run: |
          pip install ms-fabric-cli
          fab auth login --service-principal

      - name: Deploy to ${{ matrix.workspace.name }}
        run: |
          for ITEM in ./fabric-items/${{ matrix.workspace.path }}/*; do
            ITEM_NAME=$(basename "$ITEM")
            fab import "${{ matrix.workspace.name }}.Workspace/$ITEM_NAME" -i "$ITEM" -f
          done
```

## Export and Commit Workflow

```yaml
name: Export Fabric Items

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM UTC
  workflow_dispatch:

jobs:
  export:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4

      - name: Setup
        env:
          FAB_SPN_TENANT_ID: ${{ secrets.FABRIC_TENANT_ID }}
          FAB_SPN_CLIENT_ID: ${{ secrets.FABRIC_CLIENT_ID }}
          FAB_SPN_CLIENT_SECRET: ${{ secrets.FABRIC_CLIENT_SECRET }}
        run: |
          pip install ms-fabric-cli
          fab auth login --service-principal

      - name: Export workspace items
        run: |
          fab export "Production.Workspace" -o ./fabric-items/ -a -f

      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add ./fabric-items/
          if git diff --staged --quiet; then
            echo "No changes to commit"
          else
            git commit -m "Auto-export Fabric items $(date +%Y-%m-%d)"
            git push
          fi
```

## Post-Deployment Validation

```yaml
name: Deploy with Validation

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4

      - name: Setup and Auth
        env:
          FAB_SPN_TENANT_ID: ${{ secrets.FABRIC_TENANT_ID }}
          FAB_SPN_CLIENT_ID: ${{ secrets.FABRIC_CLIENT_ID }}
          FAB_SPN_CLIENT_SECRET: ${{ secrets.FABRIC_CLIENT_SECRET }}
        run: |
          pip install ms-fabric-cli
          fab auth login --service-principal

      - name: Deploy items
        run: |
          fab import "Prod.Workspace/ETL.DataPipeline" -i ./fabric-items/ETL.DataPipeline -f

      - name: Validate deployment
        run: |
          # Verify item exists
          fab exists "Prod.Workspace/ETL.DataPipeline" || exit 1
          
          # Run post-deployment test
          fab job run "Prod.Workspace/Validation.Notebook" --timeout 300
          
          echo "Deployment validated successfully"

      - name: Notify on failure
        if: failure()
        run: |
          echo "::error::Deployment validation failed"
```

## Required Secrets Configuration

Set these secrets in your repository settings:

| Secret Name | Description |
|-------------|-------------|
| `FABRIC_TENANT_ID` | Azure AD tenant ID |
| `FABRIC_CLIENT_ID` | Service principal client ID |
| `FABRIC_CLIENT_SECRET` | Service principal secret |

## Required Variables Configuration

Set these variables per environment:

| Variable Name | Description | Example |
|---------------|-------------|---------|
| `FABRIC_WORKSPACE` | Target workspace name | `Production.Workspace` |
