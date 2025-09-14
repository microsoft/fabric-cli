# Domain Examples

This page demonstrates how to manage [domains](https://learn.microsoft.com/en-us/fabric/governance/domains) in Microsoft Fabric using the CLI. Domains provide hierarchical organization and governance capabilities for workspaces and data assets within your Fabric tenant.

!!! note "Resource Type"
    Type: `.Domain`

To explore all domain commands and their parameters, run:

```
fab desc .Domain
```

**Contributors Scope Options:**

| Scope | Description | Use Case |
|-------|-------------|----------|
| `AdminsOnly` | Only domain admins can contribute | Restricted, governance-focused domains |
| `AllTenant` | All tenant users can contribute | Open collaboration domains |
| `SpecificUsersAndGroups` | Selected users/groups only | Controlled access domains |

---

## Navigation

Navigate to the domains collection using absolute path:

```
fab cd .domains
```

Navigate to a specific domain using relative path:

```
fab cd ../.domains/finance.Domain
```

## Domain Management


!!! info "A domain can only have a parent if that parent domain has no parent itself. This creates a maximum two-level hierarchy"

### Create Domain
#### Create a domain
```
fab create .domains/marketing.Domain
```

#### Create a domain with a parent domain for hierarchical organization

```
fab create .domains/sales-americas.Domain -P parentDomainName=sales,description="Sales domain for Americas region"
```

#### Create a child domain using full domain reference

```
fab create .domains/sales-emea.Domain -P parentDomainName=sales.Domain
```


### Check if a specific domain exists and is accessible

```
fab exists .domains/finance.Domain
```


### Get Domain
#### Get Domain Details
```
fab get .domains/finance.Domain
```

#### Get Domain using query and export properties to a local directory

```
fab get .domains/finance.Domain -q . -o /tmp
```

### List Domains


#### Display existing domains in a simple format.

```
fab ls .domains
```

#### Show domains with detailed information.

```
fab ls .domains -l
```


### Update Domain

!!! note "Domain property updates require Fabric admin role"

**Supported Properties:**

- `contributorsScope`: Who can contribute to the domain
- `description`: Domain description
- `displayName`: Domain display name


#### Update the display name of a domain

```
fab set .domains/finance.Domain -q displayName -i "accounting"
```

#### Update who can contribute to the domain

```
fab set .domains/finance.Domain -q contributorsScope -i "AdminsOnly"
```

### Remove Domain

#### Remove a domain with interactive confirmation
```
fab rm .domains/test-domain.Domain
```

#### Remove a domain without confirmation prompts

```
fab rm .domains/deprecated-domain.Domain -f
```

## Domain Operations
### Assign Domain To Workspace

```
fab assign .domains/finance.Domain -W finance-workspace.Workspace
```

### Unassign Domain From Workspace

```
fab unassign .domains/finance.Domain -W finance-workspace.Workspace
```