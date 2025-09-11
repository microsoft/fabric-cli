---
applyTo: "src/fabric_cli/commands/**"
---

# Commands Instructions — `src/fabric_cli/commands/**`

This guide defines how **tests** for Fabric CLI should be structured, implemented, and validated. It complements `../copilot-instructions.md` and applies specifically to the `tests/**/*.py` tree.

- Audience: test authors, contributors adding or modifying CLI functionality, reviewers validating test coverage and compliance, and CI maintainers ensuring pipelines enforce standards.
- Scope: unit and mocked E2E test design, naming conventions, fixtures, mocking strategies (VCR.py or responses), privacy and security scrubbing, determinism, performance checks, and CI integration requirements.

---

## 1) Command anatomy

**Rules of thumb**

1. **One responsibility** per command/subcommand; compose advanced scenarios via flags, not unrelated behaviors.
2. **Stable UX** across item types: same verbs and flags should behave the same regardless of resource type.
3. **Path-first** UX: the primary positional argument (when relevant) is a **fully-qualified Fabric path** using the dot‑suffix entity names (e.g., `ws.Workspace/Folder.Folder/item.ItemType`). [2][3]
4. **Deterministic output** via `print_output_format(...)` (and `print_error(...)` for failures). Never print JSON manually. [4]
5. **Structured errors** using `FabricCLIError` and standard codes/messages; reuse before adding new ones. [2][6]

**Recommended structure**

src/fabric_cli/commands//.py ^ e.g., list.py, get.py, create.py, set.py, rm.py

Where `<area>` groups by concept (e.g., `workspaces`, `items`, `folders`, `gateways`, `connections`, `domains`, `capacities`, etc.). If a verb spans multiple areas, prefer **shared utilities** under `src/fabric_cli/utils/*` and keep command files thin.

---

## 2) Argument parsing (argparse)

**Conventions**

- **Subparser** per verb (e.g., `ls`, `get`, `set`, `rm`, `import`, `export`, `open`…), created in the area module’s `attach_<area>_parsers(subparsers)` function.
- **Help**: one‑line imperative description; include the dot‑suffix expectation for paths.
- **Flags**:
  - `--output/-o`: `text` (default), `json`.
  - `--select`: server- or client‑side projection; keep safe if server doesn’t support `$select`.
  - `--filter`: server- or client‑side filtering; document semantics.
  - `--all/-a`: include **hidden entities** (dot-prefixed collections). [3]
  - `--top`, `--skip`: client-side pagination fallback when API lacks query params.
  - `--timeout`: per request (seconds), bounded.
  - `--retry`: retries with exponential backoff (bounded).
  - **Auth flags** are **not** per command; the user logs in once with `fab auth login`. Do not add per‑command auth parameters.

**Parsing patterns**

- Prefer explicit, typed arguments (e.g., `--timeout int`, `--top int`) and **validate** on parse (range, GUIDs), failing early with a `FabricCLIError` using a reusable message. [2][6]
- For **paths**, accept:
  - **Absolute**: `/ws.Workspace/.../item.ItemType`
  - **Relative** to current context (interactive mode)
  - Hidden collections by dot-prefix (e.g., `.capacities`, `.gateways`) only when `-a/--all` or explicitly referenced. [3]

---

## 3) Path semantics & hierarchy

- **Dot suffix is required** for entity names in paths (e.g., `.Workspace`, `.Folder`, `.SemanticModel`, `.Lakehouse`). [2][3]
- **Nested folders** are supported (up to ~10 levels) and must resolve deterministically. [2]
- **Hidden entities** (tenant- and workspace-level collections) use **dot‑prefixed** collection names:
  - Tenant: `.capacities`, `.gateways`, `.domains`, `.connections`, …
  - Workspace: `.managedidentities`, `.managedprivateendpoints`, `.externaldatashares`, `.sparkpools`, …
  - `ls -a` shows them; otherwise omit from default listings. [3]

**Resolution contract**

- Resolve the input string to a **typed navigation model** before making API calls (workspace ID, item ID, collection type).
- All API calls must be invoked via **centralized request utilities** (don’t create ad‑hoc `requests` sessions).
- If an ambiguous name is detected (same display name in scope), prefer:
  1) ID‑based resolution if present;
  2) Fail with a **specific** `FabricCLIError` that includes disambiguation hints.

---

## 4) Output & UX

- Use `print_output_format(data, *, columns=None, as_='json' | 'table' | 'text')`. Never `print(json.dumps(...))`. [4]
- For **tables**, specify columns with stable order and human‑friendly headers; keep IDs present but **not** first unless the command is ID-centric.
- Errors must be rendered with `print_error(...)` if the command handles its own exceptions; otherwise allow the global wrapper to format. [2][4]
- Provide **copy‑pasteable** examples in `--help` and add at least one with a **hidden** collection (e.g., capacities).

---

## 5) Errors

- **Always raise** `FabricCLIError` (or a specific subclass) with:
  - Message from `src/fabric_cli/errors/<module>.py` (reused if available)
  - Error code from `constants.py` (reused if available)  
  Example:
  ```python
    from fabric_cli.errors.common import CommonErrors
    from fabric_cli import constants as fab_const
    raise FabricCLIError(CommonErrors.invalid_path(path), fab_const.ERROR_INVALID_INPUT)
  ```
- Map HTTP errors into FabricAPIError/specifics with:
  - HTTP status
  - Fabric error code (if present)
  - Request ID (if available) for supportability
- No bare except Exception: Catch narrow exceptions, add context (path, operation), and re‑raise as CLI errors.

---

## 6) Network calls (correctness, security, performance)

- Use the common API client and common retry/backoff policy; don’t hand‑roll session logic.
- **Timeouts**: provide bounded defaults; allow --timeout to override within limits.
- **Retries**: exponential backoff for transient 5xx/429; do not retry on 4xx (except idempotent discovery if safe).
- **Pagination**: if server doesn’t support $top/$skip, implement client‑side slicing.
- **Security**:
  - Never log tokens, cookies, correlation IDs, or PII.
  - Validate JSON and GUIDs; sanitize user paths; protect file operations (permissions, existence).
  - Respect scopes of the current credential (fail with actionable error if insufficient).
- **Performance**: Cache‑aware list/read flows (honor interactive cache; avoid duplicate GETs).

## 7) Hidden entities behavior

- Hidden collections are included only when:
  - The path explicitly references them (e.g., .capacities, .gateways), or
  - `--all` / `-a` is used for a listing.
- They should appear grouped by collection and clearly typed in output (e.g., Type=Capacity).

## 8) Backward compatibility

- Additive flags only; avoid breaking flag/position changes.
- If a behavior must change, provide a deprecation period and a clear message in help and release notes.

## 9) Docs & help text

- Short imperative description (max 80 chars).
- Examples must include at least:
  - One path with nested folders
  - One example that uses a hidden collection (e.g., .capacities)
  - One with `--output json`
- Align names with Fabric portal terms and dot‑suffixes.