# Table Management Commands

The `table` commands provide tools for working with tables in lakehouses, including data loading, optimization, and schema management.

**Supported Types:**

- `.Lakehouse` (full support)
- `.Warehouse`, `.MirroredDatabase`, `.SQLDatabase`, `.SemanticModel`, `.KQLDatabase` (schema inspection only)

## Available Commands

| Command           | Description                        | Usage                                                                 |
|-------------------|------------------------------------|-----------------------------------------------------------------------|
| `table load`      | Load data into a lakehouse table   | `table load <path> --file <file> [parameters]`                           |
| `table optimize`  | Optimize a Delta table             | `table optimize <path> [--vorder] [--zorder <columns>]`               |
| `table schema`    | Display the schema of a Delta table| `table schema <path>`                                                 |
| `table vacuum`    | Vacuum a Delta table               | `table vacuum <path> [--retain_n_hours <hours>]`                      |

---

### load

Load data into a table from various file formats.

**Usage:**

```
fab table load <path> --file <data_file> [parameters]
```

**Parameters:**

- `<path>`: Path to the table.
- `--file`: Path to the file or directory to load.
- `--extension`: File extension to filter files. Optional.
- `--format`: Format options in key=value format, separated by commas. Optional. Default: `format=csv,header=true,delimiter=','`
- `--mode`: Load mode - `append` or `overwrite`. Optional. Default: `overwrite`

**Examples:**

```
fab table load Tables/employees --file employees.csv
fab table load Tables/sales --file sales_data --format format=parquet --mode append
fab table load Tables/data --file data.csv --format format=csv,delimiter=';',header=true
```

---

### optimize

Optimize table performance using V-Order and/or Z-Order techniques.

**Usage:**

```
fab table optimize <path> [--vorder] [--zorder <columns>]
```

**Parameters:**

- `<path>`: Path to the table.
- `--vorder`: Enable V-Order optimization. Optional.
- `--zorder`: Comma-separated list of columns to Z-Order by. Optional.

**Examples:**

```
fab table optimize Tables/sales --vorder
fab table optimize Tables/customers --zorder customer_id,region
fab table optimize Tables/transactions --vorder --zorder date,product_id
```

---

### schema

Display the schema of a Delta table.

**Usage:**

```
fab table schema <path>
```

**Example:**

```
fab table schema Tables/employees
```

---

### vacuum

Remove old file versions to reclaim storage space.

**Usage:**

```
fab table vacuum <path> [--retain_n_hours <hours>]
```

**Parameters:**

- `<path>`: Path to the table.
- `--retain_n_hours`: Retention period in hours. Optional. Default: 168 (7 days)

**Examples:**

```
fab table vacuum Tables/logs
fab table vacuum Tables/temp_data --retain_n_hours 24
```

---

For more examples and detailed scenarios, see [Table Management Examples](../../examples/table_examples.md).
