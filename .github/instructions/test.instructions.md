---
applyTo: "test/**/*.py"
---


## `test.instructions.md`

```markdown
# Tests Instructions — `tests/**/*.py`

This guide defines how **every test** in Fabric CLI should be designed, implemented. It complements `../copilot-instructions.md` and applies specifically to the `tests/**` tree.

- Audience: command authors and reviewers
- Scope: command design, argument parsing, path semantics, network calls, output, errors, performance, security, docs, and examples


---

## 1) Test taxonomy

### Unit tests (fast, isolated)

- Location: `tests/test_core/**`, `tests/test_utils/**`
- Scope: argument parsing, validators (GUID/JSON/path), navigation helpers, output format selection, error mapping
- No network; pure Python

### Command E2E (mocked)

- Location: `tests/test_commands/**`
- Scope: CLI command entrypoints with **mocked HTTP** or **VCR.py cassettes** (with strict scrubbing)
- Validate: correct API routes, pagination behavior, error surfaces (`FabricCLIError` + code), **output via helpers**
- Include at least one case per command using **hidden entities** (e.g., `.capacities`, `.gateways`) [3]

> Live/recorded E2Es exist in ADO (maintainer‑only) and are **not** part of the public repo. [2]

---

## 2) Structure & naming

- **File names**: `test_<area>_<verb>.py` (e.g., `test_items_ls.py`, `test_gateways_get.py`)
- **Test names**: `test_<behavior>__<condition>` (double underscore between behavior and condition)
- **Parametrization**: prefer `@pytest.mark.parametrize` for path variations (absolute, relative, nested, hidden)

---

## 3) Tools & libraries

- **pytest** for test runner
- **VCR.py** (optional) for cassette‑based mocked E2E (with scrubbing)
- Or **requests-mock**/**responses** for inline mocks if preferred by the module under test
- **mypy** and **black** are enforced via pre‑commit in CI
- **capsys** or **capsysbinary** to capture CLI stdout/stderr in unit tests

---

## 4) Running tests

```bash
# Unit tests
python3 -m pytest -q tests/test_core tests/test_utils

# Mocked command E2E (playback)
python3 -m pytest -q tests/test_commands --playback

# Full local pass (fast suites only)
python3 -m pytest -q
```

The --playback flag is a convention: when present, tests must not attempt live network I/O. If your test suite doesn’t implement a flag parser, condition on os.getenv("FAB_PLAYBACK", "1").


## 5) Fixtures

Create shared fixtures under tests/conftest.py:

- tmp_home: redirects CLI config to a temporary home (~/.config/fab → a tmp folder). Ensure cleanup.
- auth_stub: prevents real token acquisition; populates expected on‑disk non‑sensitive auth state.
- http_mock: either a responses/requests-mock session or a VCR.py cassette context.
- capsys_text: convenience wrapper to decode stdout/stderr to UTF‑8.

## 6) Mocking patterns

### A. Using responses (inline HTTP mocks)

```python
import json, pytest, responses
from fabric_cli.__main__ import main  # or an entrypoint that dispatches argv
from fabric_cli import constants as fab_const

@responses.activate
def test_ls_semantic_models_under_workspace__json_output(capsys, tmp_home, auth_stub):
    # Mock list items under workspace
    responses.add(
        responses.GET,
        "https://api.fabric.microsoft.com/v1/workspaces/123/items",
        json={"value": [{"name": "sm1", "type": "SemanticModel"}]},
        status=200,
    )

    # Call CLI
    argv = ["ls", "/ws.Workspace"]
    with pytest.raises(SystemExit) as ex:
        main(argv)  # if main exits; otherwise call directly
    assert ex.value.code == 0 or ex.value.code is None

    out = capsys.readouterr().out
    data = json.loads(out)
    assert any(x["type"] == "SemanticModel" for x in data["value"])

```

### B. Using VCR.py (cassette playback with scrubbing)

```python
import json, pytest, vcr
from fabric_cli.__main__ import main

vcr_recorder = vcr.VCR(
    cassette_library_dir="tests/cassettes",
    filter_headers=["Authorization", "x-ms-client-request-id"],
    before_record_request=lambda r: r,   # optional query/path scrubbing
    before_record_response=lambda r: r,  # optional body scrubbing
)

@pytest.mark.playback
def test_ls_capacities_hidden_collection__table_output(capsys, tmp_home, auth_stub):
    with vcr_recorder.use_cassette("ls_capacities_hidden.yaml"):
        argv = ["ls", "-a", ".capacities", "-o", "table"]
        rc = main(argv) or 0
        assert rc == 0
        out = capsys.readouterr().out
        assert "Capacity" in out
```

#### VCR scrubbing policy (required)

- Filter headers: Authorization, Cookie, x-ms-client-request-id, x-ms-activity-id, any *token*
- Replace any UPNs/emails, tenant/subscription IDs, GUIDs that identify private tenants
- Base64 payloads: either drop nodes or replace with "***redacted***"
- URLs: keep routes but scrub query secrets; allow stable IDs only if they’re fake fixtures

Any cassette failing scrubbing must be rejected in PR review.

## 7) What to test for each command

- Happy path: correct route(s), correct projection/filters, output helper usage, stable JSON keys
- Errors:
  - Invalid path → FabricCLIError with ERROR_INVALID_INPUT (or reused code)
  - 404/403 → mapped FabricAPIError with request ID in message
  - Bad JSON input → CommonErrors.invalid_json_format()
- Pagination: when applicable, verify combining pages or honoring --top/--skip
- Hidden entities: at least one ls/get case referencing dot‑prefixed collections

## 8) Determinism & flake prevention

- No real time in outputs (freeze time if needed).
- Randoms/UUIDs are seeded and/or replaced with deterministic placeholders.
- Retries: when testing retry logic, stub with virtual time or a small counter; do not sleep.
- Parallel safe: tests must not share temp files; use tmp dirs/unique names per test.

## 9) Privacy & security

- Never record or commit secrets/tokens/PII.
- Ensure cassettes and fixtures contain mock tenants and non-identifying IDs.
- On failure, test logs must not print tokens, cookies, or environment variables.
- A PR is **rejected** if a test leaks private information or attempts live auth in public CI.

## 10) Local developer workflow

```bash
# 1) Format & types
black src/ tests/
mypy src/ tests/ --ignore-missing-imports

# 2) Unit
pytest -q tests/test_core tests/test_utils

# 3) Commands (playback/mocked)
pytest -q tests/test_commands --playback

# Optional: run a single test
pytest -q tests/test_commands/test_items_ls.py::test_ls_semantic_models_under_workspace__json_output

```

## 13) Examples to copy


### A. Parser unit test

```python
import pytest
from fabric_cli.commands.items.list import attach_items_parsers
from argparse import ArgumentParser

def test_items_ls_parser__has_all_flag_and_output_modes():
    parser = ArgumentParser()
    subs = parser.add_subparsers()
    attach_items_parsers(subs)
    ns = parser.parse_args(["ls", "-a", "/ws.Workspace", "-o", "json"])
    assert getattr(ns, "all") is True
    assert ns.output == "json"
    assert ns.path == "/ws.Workspace"
```

### B. Error mapping test

```python
import pytest, responses
from fabric_cli.__main__ import main

@responses.activate
def test_get_item__404_maps_to_fabric_api_error(capsys):
    responses.add(
        responses.GET,
        "https://api.fabric.microsoft.com/v1/items/does-not-exist",
        json={"error": {"code": "ResourceNotFound", "message": "not found"}},
        headers={"x-ms-activity-id": "RID-123"},
        status=404,
    )
    rc = main(["get", "/ws.Workspace/ghost.Notebook"]) or 1
    assert rc != 0
    err = capsys.readouterr().err
    assert "ResourceNotFound" in err and "RID-123" in err

```