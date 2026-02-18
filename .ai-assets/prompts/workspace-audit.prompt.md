# Workspace Audit

Perform a comprehensive audit of workspace **${input:workspaceName}**.

## 1. Workspace Overview

### Get Workspace Details
```
fab get {workspaceName}.Workspace
```

### List All Items
```
fab ls {workspaceName}.Workspace
```

## 2. Item Inventory

List items in the workspace (note: filter by type in output, not via flag):
```
fab ls {workspaceName}.Workspace
```

Identify items by their suffixes:
- `.SemanticModel` - Power BI datasets
- `.Report` - Power BI reports
- `.Lakehouse` - Lakehouses
- `.Notebook` - Notebooks
- `.DataPipeline` - Pipelines

## 3. Capacity & Usage

### Check Workspace Capacity
```
fab get {workspaceName}.Workspace
```

### Recent Jobs
For each item that supports jobs, check run history:
```
fab job run-list {workspaceName}.Workspace/{itemName}.{ItemType}
```

## 4. Security Review

### Workspace Role Assignments
```
fab acls ls {workspaceName}.Workspace
```

### Item-Level Permissions
For sensitive items, check individual permissions:
```
fab acls ls {workspaceName}.Workspace/{itemName}.{ItemType}
```

## 5. Data Lineage

### Check Shortcuts
List items and look for shortcuts in Lakehouse paths:
```
fab ls {workspaceName}.Workspace/{lakehouseName}.Lakehouse/Files
```

## Audit Report Template

### Executive Summary
- Workspace: {workspaceName}
- Audit Date: {date}
- Total Items: {count}
- Active Users: {users}

### Item Inventory
| Type | Count | Last Modified |
|------|-------|---------------|
| Semantic Models | | |
| Reports | | |
| Lakehouses | | |
| Notebooks | | |
| Pipelines | | |

### Health Status
- Failed Jobs (Last 7 days): 
- Stale Items (No refresh > 30 days):
- Orphaned Items (No owner):

### Security Findings
- Over-permissioned items:
- External sharing:
- Guest access:

### Recommendations
1. 
2. 
3. 

## Export Audit Data

Export workspace listing to JSON:
```
fab ls {workspaceName}.Workspace -o json > audit-{workspaceName}.json
```
