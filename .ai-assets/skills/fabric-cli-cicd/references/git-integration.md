# Git Integration for Fabric Items

Patterns for storing and managing Fabric item definitions in Git repositories.

## Repository Structure

### Recommended Layout

```
fabric-repo/
├── .github/
│   └── workflows/
│       └── deploy.yml
├── fabric-items/
│   ├── pipelines/
│   │   ├── ETL-Daily.DataPipeline/
│   │   │   └── pipeline-content.json
│   │   └── ETL-Weekly.DataPipeline/
│   │       └── pipeline-content.json
│   ├── notebooks/
│   │   ├── Transform.Notebook/
│   │   │   └── notebook-content.py
│   │   └── Validation.Notebook/
│   │       └── notebook-content.py
│   ├── semantic-models/
│   │   └── Sales.SemanticModel/
│   │       ├── model.tmdl
│   │       ├── tables/
│   │       └── relationships/
│   └── reports/
│       └── SalesDashboard.Report/
│           └── report.json
├── config/
│   ├── dev.env
│   ├── test.env
│   └── prod.env
└── README.md
```

## Exporting Items for Git

### Export Single Item

```bash
# Export a data pipeline
fab export "Dev.Workspace/ETL-Daily.DataPipeline" -o ./fabric-items/pipelines/ -f

# Export a notebook
fab export "Dev.Workspace/Transform.Notebook" -o ./fabric-items/notebooks/ -f

# Export a semantic model (TMDL format)
fab export "Dev.Workspace/Sales.SemanticModel" -o ./fabric-items/semantic-models/ -f
```

### Export Full Workspace

```bash
# Export all items
fab export "Dev.Workspace" -o ./fabric-items/ -a -f

# Organize by type (post-export script)
mkdir -p fabric-items/{pipelines,notebooks,semantic-models,reports}

for ITEM in fabric-items/*.*; do
    case "$ITEM" in
        *.DataPipeline) mv "$ITEM" fabric-items/pipelines/ ;;
        *.Notebook) mv "$ITEM" fabric-items/notebooks/ ;;
        *.SemanticModel) mv "$ITEM" fabric-items/semantic-models/ ;;
        *.Report) mv "$ITEM" fabric-items/reports/ ;;
    esac
done
```

### Export Definitions Only

```bash
# Get raw definition (useful for semantic models)
fab get "Dev.Workspace/Sales.SemanticModel" -q "definition" > ./fabric-items/semantic-models/Sales.SemanticModel/definition.json
```

## Git Workflow

### Initial Setup

```bash
# Clone/create repo
git clone https://github.com/org/fabric-repo.git
cd fabric-repo

# Export current state
fab auth login
fab export "Dev.Workspace" -o ./fabric-items/ -a -f

# Initial commit
git add .
git commit -m "Initial export of Fabric items"
git push
```

### Feature Branch Workflow

```bash
# Create feature branch
git checkout -b feature/new-pipeline

# Make changes in Fabric UI or export updated items
fab export "Dev.Workspace/NewPipeline.DataPipeline" -o ./fabric-items/pipelines/ -f

# Commit changes
git add fabric-items/pipelines/NewPipeline.DataPipeline/
git commit -m "Add new ETL pipeline"

# Push and create PR
git push -u origin feature/new-pipeline
```

### Syncing Changes from Fabric

```bash
# Pull latest from Git
git pull origin main

# Export current Fabric state
fab export "Dev.Workspace" -o ./temp-export/ -a -f

# Compare with Git (visual diff)
diff -r ./fabric-items/ ./temp-export/

# Update Git with changes
cp -r ./temp-export/* ./fabric-items/
git add .
git commit -m "Sync changes from Fabric"
```

## Semantic Model (TMDL) in Git

### TMDL Structure

```
Sales.SemanticModel/
├── definition.tmdl
├── model.tmdl
├── tables/
│   ├── Sales.tmdl
│   ├── Products.tmdl
│   └── Date.tmdl
├── relationships/
│   └── relationships.tmdl
├── roles/
│   └── roles.tmdl
└── expressions/
    └── expressions.tmdl
```

### Export TMDL

```bash
# Export semantic model (automatically creates TMDL structure)
fab export "Dev.Workspace/Sales.SemanticModel" -o ./fabric-items/semantic-models/ -f
```

### Track TMDL Changes

```bash
# See what tables changed
git diff fabric-items/semantic-models/Sales.SemanticModel/tables/

# See measure changes
git diff fabric-items/semantic-models/Sales.SemanticModel/model.tmdl
```

## Notebook Source Control

### Notebook Format

```
Transform.Notebook/
├── notebook-content.py     # Main code
└── .platform               # Metadata
```

### Export Notebook

```bash
fab export "Dev.Workspace/Transform.Notebook" -o ./fabric-items/notebooks/ -f
```

### Edit Notebooks Locally

You can edit the `.py` file directly and re-import:

```bash
# Edit locally
code ./fabric-items/notebooks/Transform.Notebook/notebook-content.py

# Import changes
fab import "Dev.Workspace/Transform.Notebook" -i ./fabric-items/notebooks/Transform.Notebook -f
```

## Data Pipeline Source Control

### Pipeline Format

```
ETL-Daily.DataPipeline/
├── pipeline-content.json   # Pipeline definition
└── .platform               # Metadata
```

### Export and Track

```bash
# Export
fab export "Dev.Workspace/ETL-Daily.DataPipeline" -o ./fabric-items/pipelines/ -f

# View changes
git diff fabric-items/pipelines/ETL-Daily.DataPipeline/pipeline-content.json
```

## .gitignore Configuration

```gitignore
# Fabric CLI
.config/fab/
*.log

# Temporary exports
temp-export/
backup/

# OS files
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Don't ignore Fabric items
!fabric-items/
```

## Branching Strategy

### GitFlow for Fabric

```
main (production)
  │
  ├── develop (integration)
  │     │
  │     ├── feature/new-report
  │     ├── feature/update-model
  │     └── bugfix/pipeline-fix
  │
  └── release/v1.2
```

### Branch Protection Rules

For `main` branch:
- Require pull request reviews
- Require status checks (deployment validation)
- No direct pushes

## Automated Sync Workflow

### GitHub Action: Daily Sync from Fabric

```yaml
name: Sync from Fabric

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup
        run: pip install ms-fabric-cli

      - name: Authenticate
        env:
          FAB_SPN_TENANT_ID: ${{ secrets.FABRIC_TENANT_ID }}
          FAB_SPN_CLIENT_ID: ${{ secrets.FABRIC_CLIENT_ID }}
          FAB_SPN_CLIENT_SECRET: ${{ secrets.FABRIC_CLIENT_SECRET }}
        run: fab auth login --service-principal

      - name: Export from Fabric
        run: fab export "Dev.Workspace" -o ./fabric-items/ -a -f

      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add ./fabric-items/
          if git diff --staged --quiet; then
            echo "No changes"
          else
            git commit -m "Sync from Fabric $(date +%Y-%m-%d)"
            git push
          fi
```

## Conflict Resolution

### When Git and Fabric Diverge

```bash
# 1. Export current Fabric state
fab export "Dev.Workspace" -o ./fabric-export/ -a -f

# 2. Compare with Git
diff -r ./fabric-items/ ./fabric-export/

# 3. Decide which version to keep
# Option A: Keep Git version (deploy to Fabric)
fab import "Dev.Workspace/Item.Type" -i ./fabric-items/Item.Type -f

# Option B: Keep Fabric version (update Git)
cp -r ./fabric-export/Item.Type ./fabric-items/
git add ./fabric-items/Item.Type
git commit -m "Update from Fabric"
```

### Merge Conflicts in TMDL

When merging branches with TMDL changes:

```bash
# Pull with rebase
git pull --rebase origin main

# If conflicts in .tmdl files:
# 1. Open conflicted file
# 2. Choose correct version (usually keep both measures/columns)
# 3. Validate syntax

# After resolving
git add .
git rebase --continue
```

## Best Practices

### Do's

- Export items after significant changes
- Use meaningful commit messages
- Review TMDL changes in PRs
- Keep Git as source of truth for production
- Use branches for new features
- Automate sync with scheduled exports

### Don'ts

- Do not edit production items directly (bypass Git)
- Do not commit secrets or connection strings
- Do not force push to main branch
- Do not ignore merge conflicts
- Do not mix multiple unrelated changes in one commit
