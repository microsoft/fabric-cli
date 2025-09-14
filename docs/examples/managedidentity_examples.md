# Managed Identity Examples

This page demonstrates how to manage workspace-scoped managed identities in Microsoft Fabric using the CLI. Managed identities provide secure authentication for Fabric workspaces when accessing external Azure resources.

!!! note "Resource Type"
    Type: `.ManagedIdentity`

To explore all managed identity commands and their parameters, run:

```
fab desc .ManagedIdentity
```

---

## Navigation

Navigate to the managed identities collection within a workspace:

```
fab cd ws1.Workspace/.managedidentities
```

Navigate to a specific managed identity using relative path:

```
fab cd ws1.Workspace/.managedidentities/ws1.ManagedIdentity
```


## Managed Identity Management

### Create Managed Identity


!!! info

    - Only **one managed identity per workspace** is allowed
    - The managed identity name will be automatically set to the workspace name
    - Any provided name in the command is ignored
    - Attempting to create multiple identities triggers a `WorkspaceIdentityAlreadyExists` error

Create a managed identity for the workspace to enable secure access to Azure resources.


```
fab create ws1.Workspace/.managedidentities/workspace-identity.ManagedIdentity
```

### Check Managed Identity Existence

Check if a managed identity exists for the workspace.

```
fab exists ws1.Workspace/.managedidentities/ws1.ManagedIdentity
```

### List Managed Identities

#### List All Managed Identities

Display all managed identities in the workspace in simple format.

```
fab ls ws1.Workspace/.managedidentities
```

#### List Managed Identities with Details

Show managed identities with detailed information including configuration and status.

```
fab ls ws1.Workspace/.managedidentities -l
```


### Remove Managed Identity

#### Remove Managed Identity with Confirmation

Delete the workspace managed identity with interactive confirmation.

```
fab rm ws1.Workspace/.managedidentities/ws1.ManagedIdentity
```

#### Force Remove Managed Identity

Delete the workspace managed identity without confirmation prompts.

```
fab rm ws1.Workspace/.managedidentities/ws1.ManagedIdentity -f
```