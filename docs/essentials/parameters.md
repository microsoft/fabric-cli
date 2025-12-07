# Command Parameters

The Fabric CLI supports a comprehensive set of command-line parameters that modify command behavior and provide additional functionality. These parameters follow standard CLI conventions with both short and long forms available for most parameters.

To see all available parameters and their descriptions:

```
fab --help
```

For command-specific parameters:

```
fab <command> --help
```

For a complete list of commands, see the [Commands page](../commands/index.md).


##  Dual-option parameters

| Parameter          | Description                                           |
|--------------------|-------------------------------------------------------|
| `-A, --audience`    | Audience for `api` token                              |
| `-a, --all`         | Select or show all                                    |
| `-c, --command`     | Execute `fab` command                                 |
| `-C, --config`      | Set config for `job`                                  |
| `-f, --force`       | Force execution, skip validation                      |
| `-h, --help`        | Show help message                                     |
| `-H, --headers`     | Set HTTP headers for `api` in key=value format        |
| `-i, --input`       | JSON input path or inline                             |
| `-I, --identity`    | Entra identity                                        |
| `-l, --long`        | Display details in `ls` or `dir`                      |
| `-n, --name`        | Specify a name                                        |
| `-o, --output`      | Specify output path                                   |
| `-P, --params`      | Set parameters for `api` and `mkdir` in key=value format          |
| `-p, --password`    | Service principal `clientSecret` for `auth`           |
| `-q, --query`       | Filter JSON output with [JMESPath](https://jmespath.org/)                     |
| `-R, --role`        | Access control role for `acl`                         |
| `-t, --tenant`      | Tenant ID for `auth`                                  |
| `-u, --username`    | Service principal `clientId` for `auth`               |
| `-v, --version`     | `fab` version                                         |
| `-w, --wait`        | Wait for `job`                                        |
| `-W, --workspace`   | Workspace name for `assign` and `unassign`            |
| `-X, --method`      | HTTP method for `api` request                         |

##  Long-only parameters

| Parameter          | Description                                             |
|--------------------|---------------------------------------------------------|
| `--certificate`    | Path to the certificate for `auth`                      |
| `--days`           | Days of the week for `job` schedule                     |
| `--disable`        | Disable `job` schedule                                  |
| `--enable`         | Enable `job` schedule                                   |
| `--end`            | End date in UTC for `job`                               |
| `--extension`      | Specify file extension for `table load`                 |
| `--federated-token` | Federated token for `auth`                        |
| `--file`           | Specify file path for `table load`                      |
| `--format`         | Specify the format for `table load`                     |
| `--id`             | Specify the ID for `job`                                |
| `--interval`       | Specify the interval for `job` schedule                 |
| `--mode`           | Specify the operational mode for `table load`           |
| `--retain_n_hours` | Retain specified hours for `table vacuum`               |
| `--schedule`       | Set the job schedule for `job`                          |
| `--show_headers`   | Turn headers on for `api`                               |
| `--start`          | Start date in UTC for `job`                             |
| `--target`         | Specify the target for `ln`                             |
| `--timeout`        | Specify the timeout of the command in seconds for `job` |
| `--type`           | Specify the type for `ln` or `job`                      |
| `--vorder`         | Apply v-order for `table optimize`                      |
| `--zorder`         | Apply Z-order indexing for `table optimize`             |