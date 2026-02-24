# API Examples

This page demonstrates how to interact with various Microsoft APIs through the Fabric CLI. The API functionality allows direct REST API calls to Fabric, OneLake, Azure Resource Manager, and Power BI services.

To explore all API commands and their parameters, run:

```
fab api -h
```

!!! info "When using interactive authentication, some `api` commands may have limited functionality. If you encounter permission issues while using certain `api` commands, consider using service principal authentication as an alternative"

---

## Fabric REST API

Interact with the [Fabric REST API](https://learn.microsoft.com/rest/api/fabric/articles/) to manage Fabric resources programmatically.

### List All Fabric Workspaces

```
fab api workspaces
```

### List Lakehouses in a Workspace

```
fab api -X get workspaces/00000000-0000-0000-0000-000000000000/lakehouses
```

### Post request with inline payload

```
fab api -X post workspaces/00000000-0000-0000-0000-000000000000/lakehouses -i '{"displayName": "lakehouseitem"}'
```

### Post request with local file payload

```
fab api -X post workspaces/00000000-0000-0000-0000-000000000000/lakehouses -i /tmp/lakehouse-config.json
```

Example JSON file content:

```json
{
  "displayName": "prodlakehouse",
  "description": "Main production data lakehouse"
}
```

## OneLake REST API

Interact with the [OneLake REST API](https://learn.microsoft.com/fabric/onelake/onelake-access-api) using the storage audience for data operations.

### Get Files and Folders from Lakehouse

Access content from a Lakehouse Files section with specific parameters.

```
fab api -A storage ws1.Workspace/lh1.Lakehouse/Files?resource=filesystem&recursive=false
```

### Get Files Using Parameters

Alternative method using parameters instead of query string.

```
fab api -A storage ws1/lh1.Lakehouse/Files -P resource=filesystem,recursive=false --show_headers
```


## ARM REST API

Interact with [Azure Resource Manager (ARM) REST API for Fabric capacities](https://learn.microsoft.com/rest/api/microsoftfabric/) using the Azure audience.

### List Capacities by Subscription

Retrieve all Fabric capacities within a specific Azure subscription.

```
fab api -A azure subscriptions/00000000-0000-0000-0000-000000000000/providers/Microsoft.Fabric/capacities?api-version=2023-11-01
```


### Get Available Fabric SKUs

List all available Fabric capacity SKUs for a subscription.

```
fab api -A azure subscriptions/00000000-0000-0000-0000-000000000000/providers/Microsoft.Fabric/skus?api-version=2023-11-01
```

## Power BI REST API

Interact with the [Power BI REST API](https://learn.microsoft.com/rest/api/power-bi/) using the Power BI audience for legacy Power BI operations.

### List Power BI groups

List all accessible Power BI workspaces.

```
fab api -A powerbi groups
```

### Get a Workspace details

Retrieve Power BI workspace details.

```
fab api -A powerbi groups/00000000-0000-0000-0000-000000000000
```

### Refresh Semantic Model

For detailed examples on triggering and monitoring semantic model refresh using the API command, see the [Semantic Model Refresh Example](refresh_semantic_model_example.md).