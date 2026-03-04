### Use Case / Problem

Currently, there's no way to search for Fabric items across workspaces from the CLI. 
Users must either:
- Navigate to each workspace individually with `ls`
- Use the Fabric portal's OneLake catalog UI
- Make direct API calls

This creates friction when users need to quickly locate items by name or description across their tenant.

### Proposed Solution

Add a new `find` command to search across all accessible workspaces.


### Command Syntax

```
# Basic search
fab find "sales report"

# Filter by item type
fab find "revenue" -P type=Lakehouse

# Multiple types (bracket syntax)
fab find "monthly" -P type=[Report,Warehouse]

# Exclude types
fab find "data" -P type!=Dashboard
fab find "data" -P type!=[Dashboard,Datamart]

# Detailed view (shows IDs for scripting)
fab find "sales" -l

# Combine filters
fab find "finance" -P type=[Warehouse,Lakehouse] -l

# JMESPath client-side filtering
fab find "sales" -q "[?type=='Lakehouse']"
```

### Flags

| Flag            | Description                                                                    |
| --------------- | ------------------------------------------------------------------------------ |
| `-P`/`--params` | Parameters in key=value format. Supported: `type=` (eq) and `type!=` (ne)     |
| `-l`/`--long`   | Show detailed output with IDs                                                  |
| `-q`/`--query`  | JMESPath expression for client-side filtering                                  |

### Search Matching

The search query matches against any of these fields:

- `displayName` - Item name
- `workspaceName` - Workspace containing the item
- `description` - Item description

### Default Output (interactive mode)
```
fab > find 'sales report'
Searching catalog for 'sales report'...

50 item(s) found (more available)

name             type       workspace          description
───────────────  ─────────  ─────────────────  ─────────────────────────────────
Sales Report Q1  Report     Finance Reports    Quarterly sales analysis for Q1
Sales Report Q2  Report     Finance Reports    Monthly sales summary
...

Press any key to continue... (Ctrl+C to stop)

34 item(s) found

name             type       workspace          description
───────────────  ─────────  ─────────────────  ─────────────────────────────────
Sales Data       Lakehouse  Analytics Team     Raw sales data lakehouse
...

84 total item(s)
```



### Long Output (`-l`/`--long`)

```
Searching catalog for 'sales report'...

3 item(s) found

Name: Sales Report Q1
ID: 0acd697c-1550-43cd-b998-91bfb12347c6
Type: Report
Workspace: Finance Reports
Workspace ID: 18cd155c-7850-15cd-a998-91bfb12347aa
Description: Quarterly sales analysis for Q1

Name: Sales Report Q2
ID: 1bde708d-2661-54de-c009-02cgc23458d7
Type: Report
Workspace: Finance Reports
Workspace ID: 29de266d-8961-26de-b009-02cgc23458bb
```

Note: Empty fields (e.g., Description) are hidden for cleaner output.



Users can then reference items using the standard CLI path format:

```
fab get "Finance Reports.Workspace/Sales Report Q1.Report"
```



### Output Format Support

The command supports the global `--output_format` flag:

- `--output_format text` (default): Table or key-value output
- `--output_format json`: JSON output for scripting

### Error Handling

The command uses structured errors via `FabricCLIError`:

| Error            | Code                          | Message                                                         |
| ---------------- | ----------------------------- | --------------------------------------------------------------- |
| Unsupported type | `ERROR_UNSUPPORTED_ITEM_TYPE` | "Item type 'Dashboard' is not searchable via catalog search API" |
| Unknown type     | `ERROR_INVALID_ITEM_TYPE`     | "Unknown item type: 'FakeType'. Valid types: ..."                |
| Invalid param    | `ERROR_INVALID_INPUT`         | "Invalid parameter format: 'foo'. Expected key=value."           |
| Unknown param    | `ERROR_INVALID_INPUT`         | "Unknown parameter: 'foo'. Supported: type"                      |
| API failure      | (from response)               | "Catalog search failed: {error message}"                         |
| Empty results    | (info)                        | "No items found."                                                |

### Pagination

Pagination is handled automatically based on CLI mode:

- **Interactive mode**: Fetches 50 items per page. After each page, if more results are available, prompts "Press any key to continue... (Ctrl+C to stop)". Displays a running total at the end.
- **Command-line mode**: Fetches all pages automatically (1,000 items per page). All results are accumulated and displayed as a single table.

### Alternatives Considered

- **`ls` with grep**: Requires knowing the workspace, doesn't search descriptions
- **Admin APIs**: Requires admin permissions, overkill for personal discovery
- **Portal search**: Not scriptable, breaks CLI-first workflows

### Impact Assessment

- [x] This would help me personally
- [x] This would help my team/organization
- [x] This would help the broader fabric-cli community
- [x] This aligns with Microsoft Fabric roadmap items

### Implementation Attestation

- [x] I understand this feature should maintain backward compatibility with existing commands
- [x] I confirm this feature request does not introduce performance regressions for existing workflows
- [x] I acknowledge that new features must follow fabric-cli's established patterns and conventions

### Implementation Notes

- Uses Catalog Search API (`POST /v1/catalog/search`)
- Type filtering via `-P type=Report,Lakehouse` using key=value param pattern; supports negation (`type!=Dashboard`) and bracket syntax (`type=[Report,Lakehouse]`)
- Type names are case-insensitive (normalized to PascalCase internally)
- Interactive mode: pages 50 at a time with continuation tokens behind the scenes
- Command-line mode: fetches all pages automatically (1,000 per page)
- Descriptions truncated to terminal width in compact view; full text available via `-l`
- The API currently does not support searching: Dashboard
- Note: Dataflow Gen1 and Gen2 are currently not searchable; only Dataflow Gen2 CI/CD items are returned (as type 'Dataflow'). Scorecards are returned as type 'Report'.
- Uses `print_output_format()` for output format support
- Uses `show_key_value_list=True` for `-l`/`--long` vertical layout
- Structured error handling with `FabricCLIError` and existing error codes

---

### Comment: Design update — pagination and type filter refactor

Updated the implementation based on review feedback and alignment with existing CLI patterns:

#### Removed flags
- `--type` — replaced by `-P type=<ItemType>[,<ItemType>...]` (consistent with `-P` key=value pattern used in `mkdir`)
- `--max-items` — removed; pagination is now automatic
- `--next-token` — removed; continuation tokens are handled behind the scenes

#### New pagination behavior

**Interactive mode**: Fetches 50 items per page. After each page, if more results exist, prompts:
```
Press any key to continue... (Ctrl+C to stop)
```
Uses Ctrl+C for cancellation, consistent with the existing CLI convention (`fab_auth.py`, `fab_interactive.py`, `main.py` all use `KeyboardInterrupt`). Displays a running total at the end.

**Command-line mode**: Fetches up to 1,000 items in a single request (`pageSize=1000`). All results displayed at once — no pagination needed.

#### Updated command syntax
```bash
# Basic search
fab find 'sales report'

# Filter by type (using -P)
fab find 'data' -P type=Lakehouse

# Multiple types
fab find 'dashboard' -P type=Report,SemanticModel

# Detailed output
fab find 'sales' -l

# Combined
fab find 'finance' -P type=Warehouse,Lakehouse -l
```

#### Updated flags

| Flag              | Description                                                                  |
| ----------------- | ---------------------------------------------------------------------------- |
| `-P`/`--params`   | Parameters in key=value format. Supported: `type=<ItemType>[,<ItemType>...]` |
| `-l`/`--long`     | Show detailed output with IDs                                                |

The issue body above has been updated to reflect these changes.

---

### Comment: Bracket syntax for `-P` lists and `-q` JMESPath support

Two additions to the `find` command:

#### 1. Bracket syntax for `-P` type lists

Multiple values for a parameter can now use bracket notation:

```bash
# Single type (unchanged)
fab find 'data' -P type=Lakehouse

# Multiple types — new bracket syntax
fab find 'data' -P type=[Lakehouse,Notebook]

# Legacy comma syntax still works
fab find 'data' -P type=Lakehouse,Notebook
```

Filter generation:
- Single value: `Type eq 'Lakehouse'`
- Multiple values: `(Type eq 'Lakehouse' or Type eq 'Notebook')`
- Multi-value expressions are wrapped in parentheses for correct precedence when additional filter fields are added later

#### 2. `-q`/`--query` JMESPath client-side filtering

Consistent with `ls`, `acls`, `api`, and `fs` commands, `find` now supports JMESPath expressions for client-side filtering:

```bash
# Filter results to only Reports
fab find 'sales' -q "[?type=='Report']"

# Project specific fields
fab find 'data' -q "[].{name: name, workspace: workspace}"
```

JMESPath is applied after API results are received, per-page in interactive mode.

#### Internal change: positional arg renamed

The positional search text argument's internal `dest` was renamed from `query` to `search_text` to avoid collision with `-q`/`--query`. The CLI syntax is unchanged — `fab find 'search text'` still works.

---

### Comment: Type negation, case-insensitive matching, pagination fixes

Several improvements to the `find` command:

#### 1. Type negation with `!=`

```bash
# Exclude a single type
fab find 'data' -P type!=Dashboard

# Exclude multiple types
fab find 'data' -P type!=[Dashboard,Datamart]
```

Filter generation:
- Single negation: `Type ne 'Dashboard'`
- Multiple negation: `(Type ne 'Dashboard' and Type ne 'Datamart')`

#### 2. Case-insensitive type matching

Type names in `-P` are now case-insensitive. All of these work:

```bash
fab find 'data' -P type=lakehouse
fab find 'data' -P type=LAKEHOUSE
fab find 'data' -P type=Lakehouse
```

Input is normalized to the canonical PascalCase before validation and filter building.

#### 3. Command-line mode fetches all pages

Command-line mode now paginates automatically across all pages instead of stopping at one page of 1000. Results are accumulated and displayed as a single table.

#### 4. Description truncation

Long descriptions are truncated with `…` to fit the terminal width, preventing the table separator from wrapping to a second line. Full descriptions are available via `-l`/`--long` mode.

#### 5. Empty continuation token fix

The API returns `""` (empty string) instead of `null` when there are no more pages. This was causing interactive mode to send an empty token on the next request, which the API treated as a fresh empty search. Fixed by treating empty string tokens as end-of-results.
