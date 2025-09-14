# `ln` / `mklink` Command

Create a shortcut.

**Usage:**

```
fab ln <path> --type <type> [--target <target>] [-i <input>] [-f]
```

**Parameters:**

- `<path>`: Path for the shortcut.
- `--type <type>`: Shortcut type.
- `--target <target>`: Target path. Optional.
- `-i, --input <input>`: Input value. Optional.
- `-f, --force`: Force shortcut creation without confirmation. Optional.

!!! info "Use `--target` for internal OneLake shortcuts; for external ones, use `--type` (adlsGen2, amazonS3, dataverse, googleCloudStorage, oneLake, s3Compatible) and input inline payload with `-i`"

**Example:**

```
fab ln ws1.Workspace/shortcut --type lakehouse --target ws2.Workspace/lh.Lakehouse
```
