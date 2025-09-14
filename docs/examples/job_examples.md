# Job Examples

This page demonstrates how to run, monitor, and schedule jobs in Microsoft Fabric using the CLI. Jobs enable automation of notebooks, data pipelines, Spark job definitions, and table maintenance operations.

To explore all job commands and their parameters, run:

```
fab job -h
```

---

## Job Execution

### Synchronous Job Execution

#### Run Job and Wait for Completion

Execute a job synchronously, waiting for it to complete before returning control.

```
fab job run ws1.Workspace/pip1.DataPipeline
```

#### Run Job with Timeout

Execute a job with a specific timeout limit in seconds.

```py
# Run with 120 second timeout (job cancelled when timeout reached)
fab job run ws1.Workspace/sjd1.SparkJobDefinition --timeout 120
```

#### Run Job with Timeout (No Cancellation)

Configure the CLI to continue jobs even after timeout.

```py
# Configure to not cancel jobs on timeout
fab config set job_cancel_ontimeout false

# Job will continue running even after timeout
fab job run ws1.Workspace/sjd1.SparkJobDefinition --timeout 120
```

### Asynchronous Job Execution

#### Start Job Without Waiting

Launch a job asynchronously and return immediately without waiting for completion.

```
fab job start ws1.Workspace/pip1.DataPipeline
```

### Jobs with Parameters
Run `.Notebook` or `.DataPipeline` jobs using parameters `-P`.

**Supported `P` Parameter Types:**

- `.Notebook`: `string`, `int`, `float`, `bool`
- `.DataPipeline`: `string`, `int`, `float`, `bool`, `object`, `array`, `secureString`

#### Run Notebook with Parameters

Execute a notebook job with custom parameters of different types.

```
fab job run ws1.Workspace/nb1.Notebook -P string_param:string=new_value,int_param:int=10,float_param:float=0.1234,bool_param:bool=true
```

#### Run Data Pipeline with Basic Parameters

Execute a pipeline with standard parameter types.

```
fab job run ws1.Workspace/pip1.DataPipeline -P string_param:string=new_value,int_param:int=10,float_param:float=0.1234,bool_param:bool=true
```

#### Run Pipeline with Complex Parameters

Execute a pipeline with object, array, and secure string parameters.

```
fab job run ws1.Workspace/pip1.DataPipeline -P 'obj_param:object={"key":{"nested_key":2},"simple_key":"value"},array_param:array=[1,2,3],secstr_param:secureString=secret'
```

### Cancel Job Instances

#### Cancel Running Job

Stop a currently running job instance.

```
fab job run-cancel ws1.Workspace/nb1.Notebook --id <schedule_id>
```

## Job Monitoring

### List Jobs

**Supported Items:**

- `.Notebook`, `.DataPipeline`, `.SparkJobDefinition`, `.Lakehouse`

#### List Job Execution History

Display all job runs for a specific item.

```
fab job run-list ws1.Workspace/nb1.Notebook
```

#### List Scheduled Job Runs

Display job runs that were triggered by schedules.

```
fab job run-list ws1.Workspace/nb1.Notebook --schedule
```

### Get Job Status

#### Check Job Instance Status

Get detailed status information for a specific job run.

```
fab job run-status ws1.Workspace/nb1.Notebook --id <schedule_id>
```

#### Check Scheduled Job Status

Get status information for a scheduled job.

```
fab job run-status ws1.Workspace/nb1.Notebook --id <schedule_id> --schedule
```

## Job Scheduling

### Create Job Schedules

#### Create Cron-based Schedule

Schedule a job to run every 10 minutes with cron scheduling.

```
fab job run-sch ws1.Workspace/pip1.DataPipeline --type cron --interval 10 --start 2024-11-15T09:00:00 --end 2024-12-15T10:00:00 --enable
```

#### Create Daily Schedule

Schedule a job to run daily at specific times.

```
fab job run-sch ws1.Workspace/pip1.DataPipeline --type daily --interval 10:00,16:00 --start 2024-11-15T09:00:00 --end 2024-12-16T10:00:00
```

#### Create Weekly Schedule

Schedule a job to run on specific days of the week at designated times.

```
fab job run-sch ws1.Workspace/pip1.DataPipeline --type weekly --interval 10:00,16:00 --days Monday,Friday --start 2024-11-15T09:00:00 --end 2024-12-16T10:00:00
```

#### Create Schedule with Custom Configuration

Schedule a job using raw JSON configuration for advanced settings.

```
fab job run-sch ws1.Workspace/pip1.DataPipeline -i '{"enabled": true, "configuration": {"startDateTime": "2024-04-28T00:00:00", "endDateTime": "2024-04-30T23:59:00", "localTimeZoneId": "Central Standard Time", "type": "Cron", "interval": 10}}'
```

### Update Job Schedules

#### Disable Job Schedule

Turn off a scheduled job without deleting the schedule.

```
fab job run-update ws1.Workspace/pip1.DataPipeline --id <schedule_id> --disable
```

#### Update Schedule Frequency

Modify an existing schedule to run every 10 minutes and enable it.

```
fab job run-update ws1.Workspace/pip1.DataPipeline --id <schedule_id> --type cron --interval 10 --start 2024-11-15T09:00:00 --end 2024-12-15T10:00:00 --enable
```

#### Update Daily Schedule Times

Change the execution times for a daily schedule.

```
fab job run-update ws1.Workspace/pip1.DataPipeline --id <schedule_id> --type daily --interval 10:00,16:00 --start 2024-11-15T09:00:00 --end 2024-12-16T10:00:00
```

#### Update Weekly Schedule

Modify a weekly schedule with new days and times.

```
fab job run-update ws1.Workspace/pip1.DataPipeline --id <schedule_id> --type weekly --interval 10:00,16:00 --days Monday,Friday --start 2024-11-15T09:00:00 --end 2024-12-16T10:00:00 --enable
```

#### Update Schedule with Custom Configuration

Update a schedule using raw JSON for complex configurations.

```
fab job run-update ws1.Workspace/pip1.DataPipeline --id <schedule_id> -i '{"enabled": true, "configuration": {"startDateTime": "2024-04-28T00:00:00", "endDateTime": "2024-04-30T23:59:00", "localTimeZoneId": "Central Standard Time", "type": "Cron", "interval": 10}}'
```

### Monitor Scheduled Jobs

#### List All Scheduled Jobs

View all scheduled job runs and their status.

```
fab job run-list ws1.Workspace/nb1.Notebook --schedule
```

#### Check Schedule Status

Get detailed information about a specific job schedule.

```
fab job run-status ws1.Workspace/nb1.Notebook --id <schedule_id> --schedule
```

### Disable Job Schedules

#### Permanently Disable Schedule

Disable a job schedule to prevent future executions.

```
fab job run-update ws1.Workspace/pip1.DataPipeline --id <schedule_id> --disable
```

## Specialized Job Types

### Notebook Jobs

#### Run Notebook with Configuration File

Execute a notebook with configuration loaded from a JSON file.

```
fab job start ws1.Workspace/nb1.Notebook -C ./config_file.json
```

#### Run Notebook with Inline Configuration

Execute a notebook with inline JSON configuration for Spark settings.

```
fab job start ws1.Workspace/nb1.Notebook -C '{"conf":{"spark.conf1": "value"}, "environment": {"id": "<environment_id>", "name": "<environment_name>"}}'
```

#### Run Notebook with Default Lakehouse

Execute a notebook with a specified default lakehouse configuration.

```
fab job run ws1.Workspace/nb1.Notebook -C '{"defaultLakehouse": {"name": "<lakehouse-name>", "id": "<lakehouse-id>", "workspaceId": "<(optional) workspace-id-that-contains-the-lakehouse>"}}'
```

#### Run Notebook with Workspace Pool

Execute a notebook using a specific workspace Spark pool.

```
fab job start ws1.Workspace/nb1.Notebook -C '{"defaultLakehouse": {"name": "<lakehouse-name>", "id": "<lakehouse-id>"}, "useStarterPool": false, "useWorkspacePool": "<workspace-pool-name>"}'
```

#### Run Notebook with Configuration and Parameters

Combine configuration and parameters in a single job execution.

```
fab job run ws1.Workspace/nb1.Notebook -P string_param:string=new_value -C '{"environment": {"id": "<environment_id>", "name": "<environment_name>"}}'
```

#### Run Notebook with Raw JSON Input

Execute a notebook using raw JSON payload for complete control.

```py
# Inline JSON
fab job run ws1.Workspace/nb1.Notebook -i '{"parameters": {"string_param": {"type": "string", "value": "new_value"}}, "configuration": {"conf":{"spark.conf1": "value"}}}'

# From file
fab job run ws1.Workspace/nb1.Notebook -i ./input_file.json
```

See [notebook run payload options](https://learn.microsoft.com/fabric/data-engineering/notebook-public-api#run-a-notebook-on-demand) for complete configuration parameters.

### Data Pipeline Jobs

#### Run Pipeline with Raw JSON Parameters

Execute a pipeline using raw JSON input for parameters.

```py
# Asynchronous with basic parameters
fab job start ws1.Workspace/pip1.DataPipeline -i '{"parameters": {"string_param": "new_value", "int_param": 10}}'

# Synchronous with complex parameters
fab job run ws1.Workspace/pip1.DataPipeline -i '{"parameters": {"float_param": 0.1234, "bool_param": true, "obj_param": {"key": "value"}, "array_param": [1, 2, 3], "secstr_param": "secret"}}'
```

See [pipeline run payload options](https://learn.microsoft.com/fabric/data-factory/pipeline-rest-api#run-on-demand-item-job) for complete configuration parameters.

### Spark Job Definitions

#### Run Basic Spark Job

Execute a Spark job definition without additional configuration.

```
fab job run ws1.Workspace/sjd1.SparkJobDefinition
```

#### Run Spark Job with Payload Configuration

Execute a Spark job with specific environment and lakehouse settings.

```
fab job start ws1.Workspace/sjd1.SparkJobDefinition -i '{"commandLineArguments": "param01 TEST param02 1234", "environmentArtifactId": "<environment-id>", "defaultLakehouseArtifactId": "<lakehouse-id>", "additionalLakehouseIds": ["<lakehouse-id>"]}'
```

### Table Maintenance Jobs

!!! tip "For easier table maintenance operations, see [Table Management Examples](./table_examples.md) for user-friendly commands"

#### Run Complete Table Optimization

Execute V-Order, Z-Order, and Vacuum operations on a table.

```
fab job run ws1.Workspace/lh1.Lakehouse -i '{"tableName": "orders", "optimizeSettings": {"vOrder": true, "zOrderBy": ["account_id"]}, "vacuumSettings": {"retentionPeriod": "7.01:00:00"}}'
```

#### Run Table Optimization Only

Execute V-Order and Z-Order operations without vacuum.

```
fab job run ws1.Workspace/lh1.Lakehouse -i '{"tableName": "orders", "optimizeSettings": {"vOrder": true, "zOrderBy": ["account_id"]}}'
```

#### Run Vacuum Operation Only

Execute only vacuum operation to clean up old files.

```
fab job run ws1.Workspace/lh1.Lakehouse -i '{"tableName": "orders", "vacuumSettings": {"retentionPeriod": "7.01:00:00"}}'
```
