# Azure Pipelines for Fabric CLI

Complete pipeline examples for deploying Microsoft Fabric items using Azure DevOps.

## Basic Deployment Pipeline

```yaml
trigger:
  branches:
    include:
      - main
  paths:
    include:
      - fabric-items/**

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '3.11'

stages:
  - stage: Deploy
    displayName: 'Deploy to Fabric'
    jobs:
      - job: DeployItems
        displayName: 'Deploy Fabric Items'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(pythonVersion)'
            displayName: 'Use Python $(pythonVersion)'

          - script: pip install ms-fabric-cli
            displayName: 'Install Fabric CLI'

          - script: |
              fab auth login --service-principal
              fab auth status
            displayName: 'Authenticate'
            env:
              FAB_SPN_TENANT_ID: $(FABRIC_TENANT_ID)
              FAB_SPN_CLIENT_ID: $(FABRIC_CLIENT_ID)
              FAB_SPN_CLIENT_SECRET: $(FABRIC_CLIENT_SECRET)

          - script: |
              fab import "$(TARGET_WORKSPACE)/Pipeline.DataPipeline" -i ./fabric-items/Pipeline.DataPipeline -f
              fab import "$(TARGET_WORKSPACE)/Notebook.Notebook" -i ./fabric-items/Notebook.Notebook -f
            displayName: 'Deploy items'
```

## Multi-Stage Pipeline (Dev → Test → Prod)

```yaml
trigger:
  branches:
    include:
      - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: fabric-credentials  # Contains shared credentials

stages:
  # Development
  - stage: Dev
    displayName: 'Deploy to Dev'
    variables:
      TARGET_WORKSPACE: 'Development.Workspace'
    jobs:
      - template: templates/deploy-job.yml
        parameters:
          environment: 'dev'
          workspace: '$(TARGET_WORKSPACE)'

  # Test (requires approval)
  - stage: Test
    displayName: 'Deploy to Test'
    dependsOn: Dev
    variables:
      TARGET_WORKSPACE: 'Testing.Workspace'
    jobs:
      - deployment: DeployTest
        environment: 'test'
        strategy:
          runOnce:
            deploy:
              steps:
                - template: templates/deploy-steps.yml
                  parameters:
                    workspace: '$(TARGET_WORKSPACE)'

  # Production (requires approval)
  - stage: Prod
    displayName: 'Deploy to Prod'
    dependsOn: Test
    variables:
      TARGET_WORKSPACE: 'Production.Workspace'
    jobs:
      - deployment: DeployProd
        environment: 'production'
        strategy:
          runOnce:
            deploy:
              steps:
                - template: templates/deploy-steps.yml
                  parameters:
                    workspace: '$(TARGET_WORKSPACE)'
```

## Reusable Template: deploy-steps.yml

```yaml
# templates/deploy-steps.yml
parameters:
  - name: workspace
    type: string

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'

  - script: pip install ms-fabric-cli
    displayName: 'Install Fabric CLI'

  - script: |
      fab auth login --service-principal
      fab auth status
    displayName: 'Authenticate'
    env:
      FAB_SPN_TENANT_ID: $(FABRIC_TENANT_ID)
      FAB_SPN_CLIENT_ID: $(FABRIC_CLIENT_ID)
      FAB_SPN_CLIENT_SECRET: $(FABRIC_CLIENT_SECRET)

  - script: |
      echo "Deploying to ${{ parameters.workspace }}"
      for ITEM in ./fabric-items/*; do
        ITEM_NAME=$(basename "$ITEM")
        fab import "${{ parameters.workspace }}/$ITEM_NAME" -i "$ITEM" -f
      done
    displayName: 'Deploy items to ${{ parameters.workspace }}'

  - script: |
      fab exists "${{ parameters.workspace }}" || exit 1
      echo "Deployment verified"
    displayName: 'Validate deployment'
```

## Service Connection with Federated Credential

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

stages:
  - stage: Deploy
    jobs:
      - job: DeployWithFederated
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.11'

          - script: pip install ms-fabric-cli
            displayName: 'Install Fabric CLI'

          - task: AzureCLI@2
            displayName: 'Authenticate with Federated Credential'
            inputs:
              azureSubscription: 'fabric-service-connection'  # Service connection name
              scriptType: 'bash'
              scriptLocation: 'inlineScript'
              inlineScript: |
                # Get token for Fabric API
                TOKEN=$(az account get-access-token --resource https://analysis.windows.net/powerbi/api --query accessToken -o tsv)
                echo "##vso[task.setvariable variable=FAB_TOKEN;issecret=true]$TOKEN"

          - script: |
              export FAB_SPN_FEDERATED_TOKEN=$(FAB_TOKEN)
              fab auth login --service-principal --federated
              fab auth status
            displayName: 'Login to Fabric CLI'
            env:
              FAB_SPN_TENANT_ID: $(FABRIC_TENANT_ID)
              FAB_SPN_CLIENT_ID: $(FABRIC_CLIENT_ID)

          - script: |
              fab import "$(TARGET_WORKSPACE)/Item.Type" -i ./fabric-items/Item.Type -f
            displayName: 'Deploy items'
```

## Deploy Changed Items Only

```yaml
trigger:
  branches:
    include:
      - main
  paths:
    include:
      - fabric-items/**

pool:
  vmImage: 'ubuntu-latest'

jobs:
  - job: DeployChanges
    steps:
      - checkout: self
        fetchDepth: 2  # Need for git diff

      - task: UsePythonVersion@0
        inputs:
          versionSpec: '3.11'

      - script: pip install ms-fabric-cli
        displayName: 'Install Fabric CLI'

      - script: |
          fab auth login --service-principal
        displayName: 'Authenticate'
        env:
          FAB_SPN_TENANT_ID: $(FABRIC_TENANT_ID)
          FAB_SPN_CLIENT_ID: $(FABRIC_CLIENT_ID)
          FAB_SPN_CLIENT_SECRET: $(FABRIC_CLIENT_SECRET)

      - script: |
          # Get changed item directories
          CHANGED=$(git diff --name-only HEAD~1 -- fabric-items/ | xargs -I {} dirname {} | sort -u)
          
          if [ -z "$CHANGED" ]; then
            echo "No items changed"
            exit 0
          fi
          
          for ITEM_PATH in $CHANGED; do
            if [ -d "$ITEM_PATH" ]; then
              ITEM_NAME=$(basename "$ITEM_PATH")
              echo "Deploying $ITEM_NAME..."
              fab import "$(TARGET_WORKSPACE)/$ITEM_NAME" -i "$ITEM_PATH" -f
            fi
          done
        displayName: 'Deploy changed items'
```

## Scheduled Export Pipeline

```yaml
trigger: none

schedules:
  - cron: '0 6 * * *'  # Daily at 6 AM UTC
    displayName: 'Daily export'
    branches:
      include:
        - main
    always: true

pool:
  vmImage: 'ubuntu-latest'

jobs:
  - job: ExportItems
    steps:
      - checkout: self
        persistCredentials: true

      - task: UsePythonVersion@0
        inputs:
          versionSpec: '3.11'

      - script: pip install ms-fabric-cli
        displayName: 'Install Fabric CLI'

      - script: |
          fab auth login --service-principal
        displayName: 'Authenticate'
        env:
          FAB_SPN_TENANT_ID: $(FABRIC_TENANT_ID)
          FAB_SPN_CLIENT_ID: $(FABRIC_CLIENT_ID)
          FAB_SPN_CLIENT_SECRET: $(FABRIC_CLIENT_SECRET)

      - script: |
          fab export "$(SOURCE_WORKSPACE)" -o ./fabric-items/ -a -f
        displayName: 'Export workspace items'

      - script: |
          git config user.name "Azure Pipelines"
          git config user.email "azuredevops@microsoft.com"
          git add ./fabric-items/
          if git diff --staged --quiet; then
            echo "No changes to commit"
          else
            git commit -m "Auto-export Fabric items $(date +%Y-%m-%d)"
            git push origin HEAD:main
          fi
        displayName: 'Commit and push changes'
```

## Pipeline with Rollback Support

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: fabric-credentials

stages:
  - stage: Backup
    jobs:
      - job: BackupCurrent
        steps:
          - script: |
              pip install ms-fabric-cli
              fab auth login --service-principal
              fab export "$(TARGET_WORKSPACE)" -o $(Build.ArtifactStagingDirectory)/backup -a -f
            env:
              FAB_SPN_TENANT_ID: $(FABRIC_TENANT_ID)
              FAB_SPN_CLIENT_ID: $(FABRIC_CLIENT_ID)
              FAB_SPN_CLIENT_SECRET: $(FABRIC_CLIENT_SECRET)
          
          - publish: $(Build.ArtifactStagingDirectory)/backup
            artifact: backup
            displayName: 'Publish backup artifact'

  - stage: Deploy
    dependsOn: Backup
    jobs:
      - deployment: DeployProd
        environment: 'production'
        strategy:
          runOnce:
            deploy:
              steps:
                - script: |
                    pip install ms-fabric-cli
                    fab auth login --service-principal
                    fab import "$(TARGET_WORKSPACE)/Item.Type" -i ./fabric-items/Item.Type -f
                  env:
                    FAB_SPN_TENANT_ID: $(FABRIC_TENANT_ID)
                    FAB_SPN_CLIENT_ID: $(FABRIC_CLIENT_ID)
                    FAB_SPN_CLIENT_SECRET: $(FABRIC_CLIENT_SECRET)
            
            on:
              failure:
                steps:
                  - download: current
                    artifact: backup
                  
                  - script: |
                      pip install ms-fabric-cli
                      fab auth login --service-principal
                      fab import "$(TARGET_WORKSPACE)/Item.Type" -i $(Pipeline.Workspace)/backup/Item.Type -f
                      echo "##vso[task.logissue type=warning]Rolled back to previous version"
                    env:
                      FAB_SPN_TENANT_ID: $(FABRIC_TENANT_ID)
                      FAB_SPN_CLIENT_ID: $(FABRIC_CLIENT_ID)
                      FAB_SPN_CLIENT_SECRET: $(FABRIC_CLIENT_SECRET)
                    displayName: 'Rollback on failure'
```

## Variable Groups Setup

Create these variable groups in Azure DevOps:

### fabric-credentials (Linked to Key Vault recommended)

| Variable | Description | Secret? |
|----------|-------------|---------|
| `FABRIC_TENANT_ID` | Azure AD tenant ID | No |
| `FABRIC_CLIENT_ID` | Service principal client ID | No |
| `FABRIC_CLIENT_SECRET` | Service principal secret | Yes |

### fabric-environments-dev

| Variable | Value |
|----------|-------|
| `TARGET_WORKSPACE` | `Development.Workspace` |

### fabric-environments-prod

| Variable | Value |
|----------|-------|
| `TARGET_WORKSPACE` | `Production.Workspace` |

## Environment Approvals

Configure environment approvals in Azure DevOps:

1. Go to **Pipelines** → **Environments**
2. Create environments: `dev`, `test`, `production`
3. Add approvers for `test` and `production`
4. Configure branch policies if needed
