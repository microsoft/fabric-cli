# Resource Types

This page provides an overview of all available resource types in Microsoft Fabric CLI, including item types and virtual item types. Understanding these types helps you navigate, manage, and automate resources efficiently.

---

## Item Types

Item types are the primary content resources within Fabric workspaces. Each type has a unique extension and supports specific operations.

| Extension              | Description                        |
|------------------------|------------------------------------|
| `.Notebook`            | Analytical notebooks               |
| `.SparkJobDefinition`  | Spark job definitions              |
| `.DataPipeline`        | Data integration pipelines         |
| `.Report`              | Power BI reports                   |
| `.SemanticModel`       | Data models                        |
| `.KQLDatabase`         | Kusto databases                    |
| `.KQLDashboard`        | Kusto dashboards                   |
| `.KQLQueryset`         | Kusto query collections            |
| `.Lakehouse`           | Data lakehouse storage             |
| `.Warehouse`           | Data warehouses                    |
| `.SQLDatabase`         | SQL databases                      |
| `.MirroredDatabase`    | Mirrored databases                 |
| `.MirroredWarehouse`   | Mirrored data warehouses           |
| `.Eventhouse`          | Real-time analytics databases      |
| `.Eventstream`         | Real-time data streams             |
| `.Dashboard`           | Interactive dashboards             |
| `.Datamart`            | Self-service data marts            |
| `.CopyJob`             | Data copy operations               |
| `.Environment`         | Spark environments                 |
| `.MLExperiment`        | Machine learning experiments       |
| `.MLModel`             | Machine learning models            |
| `.MountedDataFactory`  | Mounted Data Factory resources     |
| `.PaginatedReport`     | Paginated reports                  |
| `.Reflex`              | Application development platform   |
| `.SQLEndpoint`         | SQL connection endpoints           |
| `.VariableLibrary`     | Variable libraries                 |
| `.GraphQLApi`          | GraphQL API endpoints              |

---

## Workspace Virtual Item Types

Workspace virtual item types are infrastructure or system resources that exist within the context of a specific workspace. They are not visible as regular items but are essential for advanced management and automation within a workspace.

| Extension                  | Description                        |
|----------------------------|------------------------------------|
| `.ExternalDataShare`       | Cross-tenant data sharing          |
| `.ManagedIdentity`         | Service authentication             |
| `.ManagedPrivateEndpoint`  | Private network access             |
| `.SparkPool`               | Dedicated Spark compute resources  |

---

## Tenant Virtual Item Types

Tenant virtual item types are infrastructure or system resources that exist at the tenant (organization) level. They provide shared capabilities and governance across all workspaces.

| Extension        | Description                        |
|------------------|------------------------------------|
| `.Capacity`      | Fabric capacity resources          |
| `.Connection`    | Data source connections            |
| `.Domain`        | Fabric domains                     |
| `.Gateway`       | On-premises data gateways          |
| `.Workspace`     | Fabric workspaces                  |

---


See how to describe types using [Describe (desc) command](../examples/desc_examples.md).
