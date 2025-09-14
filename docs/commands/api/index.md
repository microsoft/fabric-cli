# API Commands

The `api` commands provide direct access to Microsoft Fabric's REST APIs, allowing you to make authenticated requests for advanced operations and automation.

**Supported Types:**

All item types and virtual item types (any valid Fabric REST API endpoint).

## Available Commands

| Command | Description                       | Usage                        |
|---------|-----------------------------------|------------------------------|
| `api`   | Make an authenticated API request | `api <endpoint> [parameters]`   |

---

### api

Make an authenticated request to a Fabric API endpoint.

**Usage:**

```
fab api <endpoint> [parameters]
```

**Parameters:**

- `<endpoint>`: API endpoint relative to the base URL.
- `-A, --audience`: Target audience (fabric, storage, azure, powerbi). Default: fabric.
- `-H, --headers`: Additional request headers (key=value format). Optional.
- `-i, --input`: Request body, as a path to a JSON file or an inline JSON string (e.g., `'{"key": "value"}'`). Optional.
- `-P, --params`: Query parameters (key=value format). Optional.
- `-q, --query`: [JMESPath](https://jmespath.org) query to filter response. Optional.
- `-X, --method`: HTTP method (get, post, delete, put, patch). Default: get.
- `--show_headers`: Include response headers in output. Optional.

**Examples:**

```
fab api workspaces
fab api workspaces/11111111-2222-3333-4444-555555555555 --show_headers
fab api workspaces -q "value[?type=='Workspace']"
fab api workspaces/11111111-2222-3333-4444-555555555555/items -X post -H "content-type=application/json" -i '{"displayName": "Item Name", "type": "Report"}'
```

---

## Supported Audiences

| Audience   | Description           | Base URL                                   |
|------------|----------------------|--------------------------------------------|
| `fabric`   | Fabric REST API      | `https://api.fabric.microsoft.com`         |
| `storage`  | OneLake Storage API  | `https://*.dfs.fabric.microsoft.com`       |
| `azure`    | Azure Resource Mgr   | `https://management.azure.com`             |
| `powerbi`  | Power BI REST API    | `https://api.powerbi.com`                  |

---

## Error Handling

Common error scenarios and solutions:

- **403 Forbidden**: Check authentication method and permissions.
- **404 Not Found**: Verify resource IDs and endpoint URLs.
- **400 Bad Request**: Validate JSON payload format.
- **401 Unauthorized**: Refresh authentication or check token scope.

---

For more examples and detailed scenarios, see [API Examples](../../examples/api_examples.md).
Common error scenarios and solutions:

- **403 Forbidden**: Check authentication method and permissions
- **404 Not Found**: Verify resource IDs and endpoint URLs
- **400 Bad Request**: Validate JSON payload format
- **401 Unauthorized**: Refresh authentication or check token scope

For more examples and detailed scenarios, see [API Examples](../../examples/api_examples.md).
