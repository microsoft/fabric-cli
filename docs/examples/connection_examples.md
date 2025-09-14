# Connection Examples

This page demonstrates how to manage data connections in Microsoft Fabric using the CLI. Connections provide secure access to external data sources and enable data integration across various platforms.

!!! note "Resource Type"
    Type: `.Connection`

To explore all connection commands and their parameters, run:

```
fab desc .Connection
```

---

## Navigation

Navigate to the connections collection using absolute path.

```
fab cd /.connections
```

Navigate to a specific connection using relative path.

```
fab cd ../.connections/conn1.Connection
```

## Connection Management

### Create Connection

#### Create Basic SQL Connection

Create a connection to SQL database with required parameters only.

```
fab create .connections/conn.Connection -P connectionDetails.type=SQL,connectionDetails.parameters.server=<server>,connectionDetails.parameters.database=sales,credentialDetails.type=Basic,credentialDetails.username=<username>,credentialDetails.password=<password>
```

#### Create Connection with Gateway

Create a connection that uses a specific gateway for secure access.

```
fab create .connections/conn.Connection -P gateway=MyVnetGateway.Gateway,connectionDetails.type=SQL,connectionDetails.parameters.server=<server>,connectionDetails.parameters.database=sales,credentialDetails.type=Basic,credentialDetails.username=<username>,credentialDetails.password=<password>
```

#### Create Connection with All Parameters

Create a connection with comprehensive configuration including privacy level and encryption settings.

```
fab create .connections/conn.Connection -P privacyLevel=Private,connectionDetails.creationMethod=SQL,gatewayId=852aee7c-d056-48dc-891f-9d7110a01b88,connectionDetails.type=SQL,connectionDetails.parameters.server=<server>,connectionDetails.parameters.database=sales,credentialDetails.type=Basic,credentialDetails.username=<username>,credentialDetails.password=<password>,credentialDetails.connectionEncryption=NotEncrypted,credentialDetails.skipTestConnection=False
```

### Check Connection Existence

Check if a specific connection exists and is accessible.

```
fab exists .connections/conn1.Connection
```

### Get Connection

#### Get Connection Details

Retrieve full connection details.

```
fab get .connections/conn1.Connection
```

#### Export Connection Details

Query and export connection properties to a local directory.

```
fab get .connections/conn1.Connection -q . -o /tmp
```

### List Connections

Display all available connections in simple format.

```
fab ls .connections
```

#### List Connections with Details

Show connections with detailed information including connection type, parameters, and configuration.

```
fab ls .connections -l
```

### Update Connection

#### Change Privacy Level

Update the privacy level setting for a connection.

```
fab set .connections/conn.Connection -q privacyLevel -i Organizational
```

#### Update Password

Change the authentication password for a connection.

```
fab set .connections/conn.Connection -q credentialDetails.password -i <new_password>
```

#### Change Gateway

Update the gateway used by a connection.

```
fab set .connections/conn.Connection -q gatewayId -i "00000000-0000-0000-0000-000000000000"
```

### Remove Connection

#### Remove a connection with interactive confirmation

```
fab rm .connections/sql-conn.Connection
```

#### Remove a connection without confirmation prompts

```
fab rm .connections/gateway-conn.Connection -f
```

### Get Connection Permissions

Retrieve full connection permission details.

```
fab acl get .connections/conn.Connection
```

#### Query Connection Permission Principals

Extract principal information using JMESPath query.

```
fab acl get .connections/conn.Connection -q [*].principal
```

#### Export Connection Permission Query

Save connection permission query results to a local directory.

```
fab acl get .connections/conn.Connection -q [*].principal -o /tmp
```

#### Export to Lakehouse from Connection Context

Navigate to connection and export permissions to Lakehouse.

```
fab cd .connections/conn.Connection
fab acl get . -q [*].principal -o /ws1.Workspace/lh1.Lakehouse/Files
```

### List Connection Permissions

Display permissions assigned to a connection.

```
fab acl ls .connections/conn.Connection
```

#### List Detailed Connection Permissions

Show connection permissions with detailed information including roles and principal details.

```
fab acl ls .connections/conn.Connection -l
```