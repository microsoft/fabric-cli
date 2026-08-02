# Implementation Plan — Feature 1694265 (fabric-cli)

This plan decomposes the repo-specific [design spec](design-spec.md) into independently reviewable workstreams. The parent ADO item is User Story 1694265.

## Delivery Principles

- Land policy and compatibility tests before changing provider behavior.
- Keep all providers noninteractive below the coordinator.
- Preserve existing direct authentication while adding Azure CLI.
- Do not merge slices that depend on unresolved security or host-integration gates.
- Track requirement and test-plan evidence from the first implementation pull request.

## Proposed Task Breakdown

| Slice | Proposed ADO Task | Implementation scope | Primary files | Depends on | Exit criteria |
| ---: | --- | --- | --- | --- | --- |
| 1 | Add shared executor, authentication coordinator, and interaction policy | Unify command-line, auth, REPL, and batch dispatch; classify interaction; resolve effective source; map readiness exits; guarantee exactly-once handler execution | `main.py`, `core/fab_interactive.py`, new coordinator/executor modules, `core/fab_decorators.py` | None | All execution surfaces use one policy; local commands bypass auth; unattended commands do not prompt; readiness errors exit 4 |
| 2 | Add Azure CLI provider and explicit login contract | Add `azure-identity`; parser flags and conflicts; provider protocol; trusted executable behavior; timeout; sanitization; one-scope allowlist | `pyproject.toml`, `parsers/fab_auth_parser.py`, `commands/auth/fab_auth.py`, new provider modules, `errors/auth.py` | Slice 1 interface alignment | Explicit attended and unattended login paths validate Fabric without invoking Azure CLI login or accepting arbitrary scopes |
| 3 | Implement identity binding and atomic auth state | Versioned source state; legacy migration; runtime-only environment override; locking; atomic writes; permissions; pinned identity; process cache and concurrency | `core/fab_auth.py`, `core/fab_state_config.py`, `utils/fab_secure_io.py`, new state/cache modules | Slices 1-2; Q4 for principal validation | Failed replacement preserves prior state; fresh tokens match binding; no delegated token reaches disk |
| 4 | Implement shared chooser and exactly-once continuation | Progressive eligible-user discovery; default defer; alternate direct options; direct-terminal chooser; attended-host abstraction; separate-login fallback | Coordinator, `commands/auth/fab_auth.py`, `utils/fab_ui.py`, host interaction abstraction | Slices 1 and 3; Q5 for host transport | Default Enter defers; cancellation and defer write no state; successful consent invokes one handler/request |
| 5 | Implement passive/active status, stable errors, and source-local logout | Passive status; `--check`; audience selection; compatibility output; all stable errors; stream separation; capability checks; scoped logout | Auth parser/commands, `core/fab_constant.py`, `errors/auth.py`, output models, `commands/fs/fab_fs_open.py` | Slices 1-3 | Passive status makes zero provider calls; active status checks one audience; logout preserves unrelated and Azure CLI state |
| 6 | Integrate HTTP, SDK bridge, deploy, and batch paths | Source-aware request acquisition; headless credential factory; deploy preflight before catch-all; claims behavior; fail-fast batch counts; Power BI route compatibility | `client/fab_api_client.py`, `core/fab_msal_bridge.py`, deploy command, `main.py` | Slices 1-5 | No replay; SDK callbacks stay headless; deploy readiness exits 4; Power BI remains mapped to Fabric scope |
| 7 | Complete release matrix, docs, telemetry, and Skills pilot | Full regression matrix; telemetry safety; docs/examples; feature gates; rollout and rollback evidence; representative Skills runs | Tests, docs, telemetry integration, release configuration | Slices 1-6; Q2-Q3 | All parent test-plan rows have evidence; direct sources regress cleanly; rollout and rollback are approved |

## Dependency Graph

```text
Slice 1 ──┬──> Slice 2 ──> Slice 3 ──┬──> Slice 4 ──┐
          │                          └──> Slice 5 ──┼──> Slice 6 ──> Slice 7
          └─────────────────────────────────────────┘

Q4 gates identity validation in Slice 3.
Q5 gates attended-host integration in Slice 4.
Q2 and Q3 gate rollout completion in Slice 7.
```

## Pull Request Sequence

1. **Policy and compatibility harness:** interaction classifier, executor contract, current-behavior regression tests, and stable error categories.
2. **Provider foundation:** provider protocol, Azure CLI parser contract, allowlist, timeout, sanitization, and mocked provider tests.
3. **State and binding:** versioned migration, runtime override model, locking, atomic write, cache, and approved principal validation.
4. **User interaction:** direct chooser and continuation first; attended-host transport only after Q5.
5. **Status and lifecycle:** passive/active status, compatibility output, capability checks, and source-local logout.
6. **Integration surfaces:** HTTP, SDK bridge, deploy, batch, claims, and Power BI route regression.
7. **Release hardening:** platform matrix, docs, telemetry, Skills pilot, flags, and rollback.

Each pull request should link to its ADO task and update the requirement/test evidence ledger.

## Validation Matrix

| Layer | Required coverage |
| --- | --- |
| Parser | New flags, conflicts, required tenant/no-prompt combinations, audience allowlist |
| Policy | Direct terminal, approved attended host, undeclared host, JSON, pipe, batch, CI, callback, status, logout |
| Provider | Installed/signed-in states, timeout, sanitized error, audience mapping, refresh, concurrency, drift |
| State | Migration, permissions, atomicity, lock contention, failed replacement, environment precedence |
| Execution | CLI, auth commands, REPL, batch fail-fast, exactly-once continuation |
| Integration | HTTP routes, SDK credential, deploy preflight, user capabilities, claims handling |
| Regression | MSAL user, SPN secret/certificate/federation, managed identity, raw tokens |
| Release | Windows/Linux/macOS, guest/no-subscription, Skills pilot, feature gates, rollback |

## Task Creation Readiness

Before creating ADO work items:

- The Feature Registry artifacts must be present on its default branch.
- This repo's `Features/1694265/design-spec.md` must be reviewed and merged to the code repo's default branch.
- The ADO organization, project, hierarchy, area path, iteration, and owners must be confirmed.
- Existing closed Task 1728448 remains decision history and is not reused.

After the readiness gate passes, create the seven work items through the `manage-tasks` workflow so each ADO ID is used to generate its local `task-<ID>.md` file.
