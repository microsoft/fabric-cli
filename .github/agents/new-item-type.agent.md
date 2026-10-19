---
name: New Item Type
description: Guide and assist with onboarding a new Microsoft Fabric item type into the Fabric CLI
argument-hint: Tell me which Fabric item type you want to add (e.g., "Add support for DataActivator")
tools: ['runInTerminal', 'terminalLastCommand', 'search', 'fetch', 'read_file'] 
---

# New Item Type Onboarding Agent

> **Important:** If you are unsure about any detail -- such as the correct API URI, portal slug, whether the item supports definitions, OneLake folders, jobs, or any other capability -- **always ask the requestor for clarification before proceeding**.

## Safety Rules

- **Never hardcode secrets, tokens, or credentials** in payloads or tests
- **Use deterministic test data** -- no real tenant IDs, workspace IDs, or user emails
- **Validate all user-provided parameters** before constructing API payloads
- **Raise `FabricCLIError`** with appropriate error codes for invalid input
- **Follow existing patterns** -- consistency is more important than cleverness

---

## Prerequisites

Before starting, gather the following information about the new item type:

| Information | Example | Required |
|-------------|---------|----------|
| **Display name** (PascalCase) | `Map` | Yes |
| **API plural URI** | `maps` | Yes |
| **Portal URI slug** | `maps` | Yes |
| **Has definition/payload** | Yes / No | Yes |
| **Definition formats** | `ipynb`, `TMDL`, etc. | If has definition |
| **OneLake folders** | `Tables`, `Files` | If applicable |
| **Supports jobs** | Yes / No | Yes |
| **Job type name** | `RunNotebook`, `Pipeline` | If supports jobs |
| **Creation parameters** | `enableSchemas`, `connectionId` | If applicable |
| **Required creation params** | Subset of above | If applicable |
| **Optional creation params** | Subset of above | If applicable |
| **Import format handling** | Standard / Custom | Yes |

### API Support Matrix

Determine which Fabric REST APIs the new item type supports. This directly impacts which CLI commands to enable:

| API | CLI Commands Enabled | How to Verify |
|-----|---------------------|---------------|
| **Get Item Definition** (`getItemDefinition`) | `export`, `cp` (as source), `mv` (as source) | Check REST API docs for `POST /workspaces/{id}/{items}/{id}/getDefinition` |
| **Update Item Definition** (`updateItemDefinition`) | `cp` (as target when item exists), `mv` (update after create) | Check REST API docs for `POST /workspaces/{id}/{items}/{id}/updateDefinition` |
| **Create with Definition** (`createItem` with `definition` body) | `import`, `cp` (as target), `mv` (create at destination) | Check REST API docs for `POST /workspaces/{id}/{items}` with `definition` in body |

> **Rule of thumb:** If the item supports all three definition APIs (`getItemDefinition`, `updateItemDefinition`, and `createItem` with definition), it should be added to `export`, `import`, `cp`, and `mv` commands in `command_support.yaml`. If it supports only `getItemDefinition`, add it only to `export`.

If the contributor doesn't know all values, help them find the information from the [Fabric REST API docs](https://learn.microsoft.com/en-us/rest/api/fabric/).

---

## Common Patterns by Item Complexity

Use this table to determine which steps apply to the new item type before reading the steps themselves.

### Simple Item (no definition, no params)

Only needs Steps 1-3, 9 (add to the standard multi-case match), 10a (review `command_support.yaml` for `unsupported_items`), 11 (ALL_ITEM_TYPES + basic_item_parametrize), 12, and 13.

**Examples:** `Dashboard`, `Datamart`

### Item with Definition Support (most common)

Needs Steps 1-4, 9, 10 (export + import + cp + mv), 11 (ALL_ITEM_TYPES + basic_item_parametrize + mv params + export params + set metadata params), 12, and 13.

**Examples:** `Map`, `CopyJob`, `Dataflow`, `GraphQLApi`, `UserDataFunction`

### Item with Creation Parameters

Needs Steps 1-3, 7-9, 10, 11 (ALL_ITEM_TYPES but NOT basic_item_parametrize), 12, and 13.

**Examples:** `Lakehouse` (enableSchemas), `Warehouse` (enableCaseInsensitive), `KQLDatabase` (dbType, eventhouseId)

### Item with OneLake Folders

Needs Steps 1-3, 5, 9, 10, 11, 12, and 13.

**Examples:** `Lakehouse` (Files, Tables), `Warehouse` (Files, Tables), `KQLDatabase` (Tables, Shortcut)

### Item with Job Support

Needs Steps 1-3, 6, 9, 10, 11, 12, and 13.

**Examples:** `Notebook` (RunNotebook), `DataPipeline` (Pipeline), `SparkJobDefinition` (sparkjob)

### Full-Featured Item (all capabilities)

Needs all steps 1-13.

**Example:** `Notebook` -- has definition formats, job support, and custom creation payload.

---

## Existing Item Types to Study

| Item Type | Enum | Complexity | Good Reference For |
|-----------|------|------------|-------------------|
| `Dashboard` | `DASHBOARD` | Simple | Minimal integration |
| `Map` | `MAP` | Standard with definitions | Definition support (export/import/mv/cp), no creation params, no jobs/folders |
| `Lakehouse` | `LAKEHOUSE` | Medium | Creation params, OneLake folders, jobs |
| `Notebook` | `NOTEBOOK` | Full | Definitions, jobs, custom payload |
| `SemanticModel` | `SEMANTIC_MODEL` | Medium | Definition formats (TMDL/TMSL), payload templates |
| `Report` | `REPORT` | Medium | Dependency creation (auto-creates SemanticModel) |
| `MirroredDatabase` | `MIRRORED_DATABASE` | Complex | Multiple payload variants, connection params |
| `MountedDataFactory` | `MOUNTED_DATA_FACTORY` | Medium | Required params, custom payload |

---

## Phases

Follow these four phases in order. Do not start writing code until you have completed the Gather and Classify phases.

1. **Gather** -- Collect all prerequisite information from the requestor (see Prerequisites table above). If anything is missing or unclear, ask before continuing.
2. **Classify** -- Use the Common Patterns table above to determine the item's complexity level and which steps apply.
3. **Execute** -- Walk through only the applicable steps from the Integration Checklist below.
4. **Validate** -- Run the verification commands from the Verification Table to confirm completeness.

---

## Integration Checklist

Every new item type requires changes across these files. Walk the contributor through each step in order:

### Step 1 -- Register the Item Type Enum

**File:** `src/fabric_cli/core/fab_types.py`

Add the new member to the `ItemType` enum class, in the `# API` section, maintaining alphabetical order within that section.

```python
# In class ItemType(_BaseItemType):
# API section
NEW_ITEM = "NewItem"
```

**Rules:**
- The enum member name uses `UPPER_SNAKE_CASE`
- The enum value uses `PascalCase` matching the Fabric API's `type` field exactly
- Place it alphabetically among the other `# API` entries

### Step 2 -- Add API Format Mapping

**File:** `src/fabric_cli/core/fab_types.py`

Add an entry to the `format_mapping` dictionary. This maps the item type to its Fabric REST API URI segment.

```python
# In format_mapping dict:
ItemType.NEW_ITEM: "newItems",
```

**Rules:**
- The value is the **plural camelCase** form used in the REST API URL: `https://api.fabric.microsoft.com/v1/workspaces/{id}/{value}`
- Check the [Fabric REST API reference](https://learn.microsoft.com/en-us/rest/api/fabric/) for the correct value
- Maintain alphabetical order by `ItemType` member name

### Step 3 -- Add Portal URI Mapping

**File:** `src/fabric_cli/core/fab_types.py`

Add an entry to the `uri_mapping` dictionary. This maps the item type to its Fabric Portal URL segment for the `fab open` command.

```python
# In uri_mapping dict:
ItemType.NEW_ITEM: "newitems",
```

**Rules:**
- The value is the **lowercase** slug used in the portal URL: `https://app.fabric.microsoft.com/groups/{ws_id}/{value}/{item_id}`
- Check the Fabric portal URL by opening an item of this type in the browser
- Maintain alphabetical order by `ItemType` member name

### Step 4 -- Add Definition Format Mapping (if applicable)

**File:** `src/fabric_cli/core/fab_types.py`

If the item type supports `export`/`import` with definition payloads, add an entry to `definition_format_mapping`.

```python
# In definition_format_mapping dict:
ItemType.NEW_ITEM: {"default": ""},
```

**Rules:**
- `"default"` key is required -- it defines the query parameter appended when no explicit format is requested
- Additional keys map user-specified format names to query strings (e.g., `"TMDL": "?format=TMDL"`)
- If the item has no definition support, skip this step
- Maintain alphabetical order by `ItemType` member name

### Step 5 -- Add OneLake Folders (if applicable)

**File:** `src/fabric_cli/core/fab_types.py`

If the item type exposes OneLake folders (e.g., `Tables`, `Files`), add:

> **Ask the requestor:** "Does this item type expose OneLake folders (e.g., Tables, Files)? If so, which folders does it expose, and are any of them writable?" Do not guess -- OneLake folder configuration varies per item type and incorrect values will cause runtime errors.

1. A new `Enum` class for the folders:
```python
class NewItemFolders(Enum):
    TABLES = "Tables"
    FILES = "Files"
```

2. An entry in `ItemFoldersMap`:
```python
ItemType.NEW_ITEM: [folder.value for folder in NewItemFolders],
```

3. If any folders are writable via OneLake, add to `ItemOnelakeWritableFoldersMap`.

### Step 6 -- Add Job Type Mapping (if applicable)

**File:** `src/fabric_cli/core/fab_types.py`

If the item type supports on-demand job execution (e.g., running a notebook, triggering a pipeline), add:

> **Ask the requestor:** "Does this item type support on-demand job execution? If so, what is the exact job type name used by the Fabric REST API (e.g., `RunNotebook`, `Pipeline`)?" The job type string must match the API exactly -- do not infer it.

1. A new member to the `FabricJobType` enum if the job type doesn't already exist:
```python
class FabricJobType(Enum):
    NEW_JOB = "NewJobType"
```

2. An entry in `ITJobMap`:
```python
ItemType.NEW_ITEM: FabricJobType.NEW_JOB,
```

**Rules:**
- The job type value must match the Fabric REST API's job type string exactly

### Step 7 -- Add Creation Parameters (if applicable)

**File:** `src/fabric_cli/utils/fab_cmd_mkdir_utils.py`

In the `get_params_per_item_type()` function, add a case for the new item type:

```python
case ItemType.NEW_ITEM:
    required_params = ["paramA"]       # params that MUST be provided
    optional_params = ["paramB"]       # params that MAY be provided
```

### Step 8 -- Add Creation Payload Logic (if applicable)

**File:** `src/fabric_cli/utils/fab_cmd_mkdir_utils.py`

In the `add_type_specific_payload()` function, add a case for the new item type:

```python
case ItemType.NEW_ITEM:
    # Option A: Inline payload
    payload_dict["definition"] = {
        "parts": [{
            "path": "content.json",
            "payload": "<base64-encoded-default-content>",
            "payloadType": "InlineBase64",
        }]
    }

    # Option B: File-based payload template
    payload_folder = "Blank.NewItem"
    payload_path = os.path.join(
        project_root, "commands", "fs", "payloads", payload_folder
    )
    payload_dict["definition"] = _create_payload(payload_path, params)

    # Option C: creationPayload (no definition)
    payload_dict["creationPayload"] = {"someProperty": value}
```

If using Option B, create the payload template directory:
- `src/fabric_cli/commands/fs/payloads/Blank.NewItem/`
- Place template files inside (JSON, PBIR, etc.)

### Step 9 -- Add Import Payload Handling

**File:** `src/fabric_cli/core/hiearchy/fab_item.py`

In the `get_payload()` method, add the new item type. Choose the appropriate pattern:

**Standard pattern** (most items) -- add to the existing multi-case match:
```python
case (
    ItemType.REPORT
    | ItemType.KQL_DASHBOARD
    | ...
    | ItemType.NEW_ITEM    # <-- Add here
):
    return {
        "type": str(self.item_type),
        "folderId": self.folder_id,
        "displayName": self.short_name,
        "definition": definition,
    }
```

**Custom pattern** (items with format-specific handling) -- add a dedicated case:
```python
case ItemType.NEW_ITEM:
    return {
        "type": str(self.item_type),
        "folderId": self.folder_id,
        "displayName": self.short_name,
        "definition": {
            "format": input_format or "default",
            "parts": definition["parts"],
        },
    }
```

### Step 10 -- Update Command Support Configuration

**File:** `src/fabric_cli/core/fab_config/command_support.yaml`

This file controls which CLI commands are enabled for each item type. Add the new item type's snake_case name to the appropriate command sections based on the API Support Matrix from the Prerequisites.

> **This step applies to ALL item types, not just items with definition support.** Sub-step 10a (`unsupported_items` review) always applies. Sub-steps 10b-10e apply only to items with definition support.

#### 10a. Check `unsupported_items` lists (always)

Review the `unsupported_items` sections for `rm`, `get`, `set`, and `mkdir`. If the new item type does **not** support one of these operations via the Fabric REST API, add it to the relevant `unsupported_items` list. Check existing entries (e.g., `dashboard`, `paginated_report`) for reference.

> **Ask the requestor:** "Can this item type be deleted (rm), read with detailed properties (get), updated (set), and created (mkdir) via the standard items API?" Add the item to `unsupported_items` for any command it does not support.

```yaml
# Example: item cannot be deleted or created via API
      rm:
        unsupported_items:
          # ... existing items ...
          - new_item    # <-- Add here if rm is NOT supported
      mkdir:
        unsupported_items:
          # ... existing items ...
          - new_item    # <-- Add here if mkdir is NOT supported
```

#### 10b. Add to `export` (if the item supports `getItemDefinition` API)

```yaml
commands:
  fs:
    subcommands:
      export:
        supported_items:
          # ... existing items ...
          - new_item    # <-- Add here, maintain alphabetical order
```

#### 10c. Add to `import` (if the item supports `createItem` with definition)

```yaml
      import:
        supported_items:
          # ... existing items ...
          - new_item    # <-- Add here
```

#### 10d. Add to `mv` (if the item supports all three definition APIs)

```yaml
      mv:
        supported_items:
          # ... existing items ...
          - new_item    # <-- Add here
```

#### 10e. Add to `cp` (if the item supports all three definition APIs)

```yaml
      cp:
        supported_items:
          # ... existing items ...
          - new_item    # <-- Add here
```

**Rules:**
- Use `snake_case` for item type names (e.g., `semantic_model`, `data_pipeline`, `copy_job`)
- The `mv` and `cp` commands require **both** export (getItemDefinition) **and** import (createItem with definition) support because they work by exporting from source and importing to destination
- If the item does NOT support `import` (e.g., `graph_query_set`), add it to the `import` section's `unsupported_items` list
- The `export` list often includes extra items like `eventhouse` and `kql_database` that support export but not import/mv/cp
- Check existing items in each section for reference patterns

### Step 11 -- Add to Test Parametrization Lists

**File:** `tests/test_commands/conftest.py`

Add the new item type to the parametrized test lists so that existing tests automatically cover the new item type.

> **IMPORTANT: Do NOT create VCR cassette recording files.** Only modify the parametrization lists in `conftest.py`. The recording files under `tests/test_commands/recordings/` are generated separately by running the tests against a live environment and should never be hand-crafted or generated by this agent.

#### 11a. Add to `ALL_ITEM_TYPES`

This list drives the comprehensive test suite (cd, ls, exists, rm, get, set, mkdir).

```python
ALL_ITEM_TYPES = [
    ItemType.DATA_PIPELINE,
    ItemType.ENVIRONMENT, ItemType.EVENTHOUSE, ItemType.EVENTSTREAM,
    # ... existing items ...
    ItemType.USER_DATA_FUNCTION, ItemType.DIGITAL_TWIN_BUILDER, ItemType.GRAPH_QUERY_SET,
    ItemType.NEW_ITEM,    # <-- Add here at the end
]
```

#### 11b. Add to `basic_item_parametrize`

This list drives tests for "basic" items -- items that have **no special creation parameters, no OneLake folders, and no special properties**. Add the new item type here **only if** it is a basic item (i.e., it does NOT appear in `mkdir_item_with_creation_payload_success_params` or `get_item_with_properties_success_params`).

```python
basic_item_parametrize = pytest.mark.parametrize("item_type", [
    ItemType.DATA_PIPELINE, ItemType.ENVIRONMENT, ItemType.EVENTSTREAM,
    # ... existing items ...
    ItemType.USER_DATA_FUNCTION, ItemType.DIGITAL_TWIN_BUILDER, ItemType.GRAPH_QUERY_SET,
    ItemType.NEW_ITEM,    # <-- Add here at the end
])
```

#### 11c. Add to `mv_item_to_item_success_params` (if mv is supported)

If the item type was added to `mv` in `command_support.yaml`, also add it here:

```python
mv_item_to_item_success_params = pytest.mark.parametrize("item_type", [
    ItemType.DATA_PIPELINE, ItemType.KQL_DASHBOARD, ItemType.KQL_QUERYSET,
    # ... existing items ...
    ItemType.NEW_ITEM,    # <-- Add here
])
```

Similarly update `mv_item_within_workspace_rename_success_params` if applicable.

#### 11d. Add to `get_item_with_properties_success_params` (if the item has special properties)

If the item type has extended properties returned by `fab get -v`, add it:

```python
get_item_with_properties_success_params = pytest.mark.parametrize("item_type,expected_properties", [
    # ... existing items ...
    (ItemType.NEW_ITEM, ["properties", "someSpecificProperty"]),
])
```

#### 11e. Add to export test parametrize lists (if export is supported)

If the item type was added to `export` in `command_support.yaml`, add it to all export-related test lists:

```python
# Export with file extension check
export_item_with_extension_parameters = pytest.mark.parametrize("item_type,expected_file_extension", [
    # ... existing items ...
    (ItemType.NEW_ITEM, ".json"),    # <-- Add here with expected extension
])

# Export item types
export_item_types_parameters = pytest.mark.parametrize("item_type", [
    # ... existing items ...
    ItemType.NEW_ITEM,    # <-- Add here
])

# Export default format (expected file count)
export_item_default_format_parameters = pytest.mark.parametrize("item_type,expected_file_count", [
    # ... existing items ...
    (ItemType.NEW_ITEM, 2),    # <-- Add here with expected count
])

# Export invalid format
export_item_invalid_format_parameters = pytest.mark.parametrize("item_type,invalid_format", [
    # ... existing items ...
    (ItemType.NEW_ITEM, ".txt"),    # <-- Add here
])
```

#### 11f. Add to `set_item_metadata_for_all_types_success_item_params` (if applicable)

If the item type supports `fab set` for metadata (displayName, description), add it:

```python
set_item_metadata_for_all_types_success_item_params = pytest.mark.parametrize("item_type", [
    # ... existing items ...
    ItemType.NEW_ITEM,    # <-- Add here
])
```

### Step 12 -- Add Changelog Entry

Create a changelog entry file in `.changes/unreleased/` using the changie format:

**File:** `.changes/unreleased/new-items-YYYYMMDD-HHMMSS.yaml`

```yaml
kind: new-items
body: Add support for NewItem item type
time: 2026-01-15T10:30:00.000000000Z
custom:
    Author: your-github-username
    AuthorLink: https://github.com/your-github-username
```

**Rules:**
- The `kind` must be `new-items` (maps to the `New Items Support` section in the changelog)
- The `body` should be a concise description of what was added
- The `time` should be the current UTC timestamp in RFC 3339 format
- The `Author` should be the contributor's GitHub username
- The file name format is `new-items-YYYYMMDD-HHMMSS.yaml` (e.g., `new-items-20260115-103000.yaml`)

Alternatively, if `changie` is installed, run:
```bash
changie new --kind new-items --body "Add support for NewItem item type" --custom Author=your-github-username
```

### Step 13 -- Update Documentation Pages

#### 13a. Update Resource Types Page

**File:** `docs/essentials/resource_types.md`

Add the new item type to the **Item Types** table, maintaining alphabetical order:

```markdown
| Extension              | Description                        |
|------------------------|------------------------------------|
| ...                    | ...                                |
| `.NewItem`             | Description of the new item type   |
| ...                    | ...                                |
```

#### 13b. Update Item Examples Page

**File:** `docs/examples/item_examples.md`

Add the new item type to the **supported item type lists** in the following sections (only if the item supports the corresponding command):

1. **Copy Item** -- Add `.NewItem` to the "Supported Item Types for Copy" list (if `cp` is supported)
2. **Export Item** -- Add `.NewItem` to the "Exportable Item Types" list (if `export` is supported)

For example, add to the copy section:
```markdown
- `.MirroredDatabase`, `.Reflex`
- `.NewItem`, `.MountedDataFactory`, `.CopyJob`, `.VariableLibrary`
```

And to the export section:
```markdown
- `.Reflex`, `.NewItem`, `.MountedDataFactory`, `.CopyJob`, `.VariableLibrary`
```

**Rules:**
- Maintain consistent formatting with existing entries
- Place new items alphabetically or in a logical grouping with similar item types
- Update both the copy and export sections if the item supports both operations

---

## Verification Table

After completing all applicable steps, run these commands to verify each integration point. Replace `NEW_ITEM` with the actual enum member name and `NewItem` with the PascalCase type name.

| Step | Verify with | When |
|------|-------------|------|
| 1. Enum | `grep -n 'NEW_ITEM.*=.*"NewItem"' src/fabric_cli/core/fab_types.py` | Always |
| 2. format_mapping | `grep -n 'ItemType.NEW_ITEM' src/fabric_cli/core/fab_types.py \| grep -i format_mapping` | Always |
| 3. uri_mapping | `grep -n 'ItemType.NEW_ITEM' src/fabric_cli/core/fab_types.py \| grep -i uri_mapping` | Always |
| 4. definition_format | `grep -n 'ItemType.NEW_ITEM' src/fabric_cli/core/fab_types.py \| grep -i definition` | Has definitions |
| 5. OneLake folders | `grep -n 'ItemType.NEW_ITEM' src/fabric_cli/core/fab_types.py \| grep -i folder` | Has OneLake folders |
| 6. Job mapping | `grep -n 'ItemType.NEW_ITEM' src/fabric_cli/core/fab_types.py \| grep -i job` | Has jobs |
| 7. Creation params | `grep -n 'ItemType.NEW_ITEM' src/fabric_cli/utils/fab_cmd_mkdir_utils.py \| grep -i param` | Has creation params |
| 8. Creation payload | `grep -n 'ItemType.NEW_ITEM' src/fabric_cli/utils/fab_cmd_mkdir_utils.py \| grep -i payload` | Has creation payload |
| 9. Import payload | `grep -n 'ItemType.NEW_ITEM' src/fabric_cli/core/hiearchy/fab_item.py` | Always |
| 10. Command support | `grep -n 'new_item' src/fabric_cli/core/fab_config/command_support.yaml` | Always (check both supported_items and unsupported_items) |
| 11a. ALL_ITEM_TYPES | `grep -n 'NEW_ITEM' tests/test_commands/conftest.py \| grep -i all_item` | Always |
| 11b. basic_item | `grep -n 'NEW_ITEM' tests/test_commands/conftest.py \| grep -i basic` | Basic items only |
| 11c. mv params | `grep -n 'NEW_ITEM' tests/test_commands/conftest.py \| grep -i mv` | Has mv support |
| 11d. properties params | `grep -n 'NEW_ITEM' tests/test_commands/conftest.py \| grep -i properties` | Has special properties |
| 11e. export params | `grep -n 'NEW_ITEM' tests/test_commands/conftest.py \| grep -i export` | Has export support |
| 11f. set metadata | `grep -n 'NEW_ITEM' tests/test_commands/conftest.py \| grep -i metadata` | Has set support |
| 12. Changelog | `ls .changes/unreleased/ \| grep -i newitem` | Always |
| 13a. Resource types | `grep -n 'NewItem' docs/essentials/resource_types.md` | Always |
| 13b. Item examples | `grep -n 'NewItem' docs/examples/item_examples.md` | Has cp or export |
| Tests pass | `python -m pytest tests/ -q` | Always |

---

## Reference: Complete Onboarding Example (Map Item Type)

Here is a real example of onboarding the `Map` item type, which is an **item with definition support** (supports export, import, mv, cp but has no special creation parameters, no OneLake folders, no jobs):

### Files Changed

| File | Changes |
|------|---------|
| `src/fabric_cli/core/fab_types.py` | Added `MAP = "Map"` enum, `"maps"` in format_mapping, `"maps"` in uri_mapping, `{"default": ""}` in definition_format_mapping |
| `src/fabric_cli/core/hiearchy/fab_item.py` | Added `ItemType.MAP` to the standard multi-case match in `get_payload()` |
| `src/fabric_cli/core/fab_config/command_support.yaml` | Added `map` to `export`, `import`, `mv`, `cp` supported_items |
| `tests/test_commands/conftest.py` | Added `ItemType.MAP` to `ALL_ITEM_TYPES`, `basic_item_parametrize`, `mv_item_to_item_success_params`, `mv_item_within_workspace_rename_success_params`, `set_item_metadata_for_all_types_success_item_params`, `export_item_with_extension_parameters`, `export_item_types_parameters`, `export_item_default_format_parameters`, `export_item_invalid_format_parameters` |
| `.changes/unreleased/new-items-*.yaml` | Changelog entry for Map item type |
| `docs/essentials/resource_types.md` | Added `.Map` row to the Item Types table |
| `docs/examples/item_examples.md` | Added `.Map` to copy and export supported types lists |

