# Job Management Commands

The `job` commands provide tools for starting, running, monitoring, and scheduling tasks for various Fabric items like notebooks and pipelines.

**Supported Types:**

- `.Notebook`
- `.DataPipeline`
- `.SparkJobDefinition`
- `.Lakehouse` (table maintenance jobs)

## Available Commands

| Command         | Description                | Usage                                                                 |
|-----------------|---------------------------|-----------------------------------------------------------------------|
| `job start`     | Start an item (async)     | `job start <path> [-P <params>] [-C <config>] [-i <json_inline_or_path>]` |
| `job run`       | Run an item (sync)        | `job run <path> [-P <params>] [-C <config>] [-i <json_inline_or_path>] [--timeout <seconds>]` |
| `job run-cancel`| Cancel an item run        | `job run-cancel <path> [--id <id>] [--wait]`                          |
| `job run-list`  | List item or scheduled job runs | `job run-list <path> [--schedule]`                              |
| `job run-status`| Get job run details       | `job run-status <path> [--id <id>] [--schedule]`                      |
| `job run-sch`   | Schedule a job            | `job run-sch <path> [-i <json_inline_or_path>*] [--type <type>] [--interval <interval>] [--days <days>]` |
| `job run-update`| Update a scheduled job    | `job run-update <path> [--id <id>] [-i <json_inline_or_path>] [--type <type>] [--enable/--disable]` |

---

### start

Start an item asynchronously and return immediately with a job ID.

**Usage:**

```
fab job start <path> [-P <params>] [-C <config>] [-i <json_inline_or_path>]
```

**Parameters:**

- `<path>`: Path to the resource.
- `-P, --params`: Parameters in name:type=value format, comma-separated. Optional.
- `-C, --config`: JSON configuration for notebooks. Optional.
- `-i, --input`: JSON payload for additional configuration. Optional.

**Examples:**
```
fab job start pipeline1.datapipeline
fab job start notebook1.notebook -P param1:string=value1,param2:int=42
fab job start notebook1.notebook -C '{"spark.executor.memory": "4g"}'
```

---

### run

Run an item synchronously and wait for completion.

**Usage:**

```
fab job run <path> [-P <params>] [-C <config>] [-i <json_path>] [--timeout <seconds>] [--polling_interval <seconds>]
```

**Parameters:**

- `<path>`: Path to the resource.
- `-P, --params`: Parameters in name:type=value format, comma-separated. Optional.
- `-C, --config`: JSON configuration for notebooks. Optional.
- `-i, --input`: JSON payload for additional configuration. Optional.
- `--timeout`: Maximum time to wait for completion in seconds. Optional.
- `--polling_interval`: Custom job status polling interval in seconds. Optional.

**Examples:**

```
fab job run notebook1.notebook --timeout 3600
fab job run notebook1.notebook -P input_date:string=2024-01-01
```

---

### run-sch

Create a scheduled job.

**Usage:**

```
fab job run-sch <path> [parameters]
```

**Parameters:**

- `<path>`: Path to the resource.
- `--type`: Schedule type (cron, daily, weekly). Optional.
- `--interval`: Minutes or time list. Optional.
- `--days`: Days of the week (for weekly schedules). Optional.
- `--start`: Start date/time in UTC. Optional.
- `--end`: End date/time in UTC. Optional.
- `--enable`: Enable the schedule immediately. Optional.
- `-i, --input`: JSON configuration file. Optional.

**Examples:**

```
fab job run-sch notebook1.notebook --type daily --interval "09:00,15:00"
fab job run-sch pipeline1.datapipeline --type weekly --interval "19:00" --days "Monday,Wednesday"
fab job run-sch notebook1.notebook -i schedule_config.json
```

---

### run-list

List job runs or scheduled jobs.

**Usage:**

```
fab job run-list <path> [--schedule]
```

**Parameters:**

- `<path>`: Path to the resource.
- `--schedule`: Show scheduled jobs instead of runs. Optional.

---

### run-status

Get detailed status of a job run.

**Usage:**

```
fab job run-status <path> --id <job_id> [--schedule]
```

**Parameters:**

- `<path>`: Path to the resource.
- `--id`: Job or schedule ID.
- `--schedule`: Check scheduled job status. Optional.

---

### run-cancel

Cancel a running job.

**Usage:**

```
fab job run-cancel <path> --id <job_id> [--wait]
```

**Parameters:**

- `<path>`: Path to the resource.
- `--id`: Job ID to cancel.
- `-w, --wait`: Wait for cancellation to complete. Optional.

---

For more examples and detailed scenarios, see [Job Management Examples](../../examples/job_examples.md).
