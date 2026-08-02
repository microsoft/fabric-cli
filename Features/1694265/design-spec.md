# Design Spec — Feature 1694265 (fabric-cli)

> Repo-specific design for adding Azure CLI as an explicit Fabric CLI authentication source.
> The parent [engineering design](https://powerbi@dev.azure.com/powerbi/Trident/_git/PlatformDevFeatureRegistry?path=/Features/active/1694265/engineering-design.md), [implementation handoff](https://powerbi@dev.azure.com/powerbi/Trident/_git/PlatformDevFeatureRegistry?path=/Features/active/1694265/implementation-handoff.md), and [test plan](https://powerbi@dev.azure.com/powerbi/Trident/_git/PlatformDevFeatureRegistry?path=/Features/active/1694265/test-plan.md) define the product contract.

## Scope

Fabric CLI owns the complete client-side implementation:

- Add `azure-cli` as an explicit authentication source while preserving all existing direct Fabric CLI sources.
- Introduce a shared pre-dispatch authentication coordinator for command-line, batch, auth, and REPL execution.
- Acquire Azure CLI tokens noninteractively through `AzureCliCredential`.
- Persist a versioned source and identity binding, but never persist delegated Azure CLI tokens.
- Add passive and active authentication status, stable error/exit behavior, source-local logout, and source-aware SDK/deploy integration.
- Preserve the existing route labels and scopes: `fabric` and `powerbi` use the Fabric scope, `storage` uses the OneLake scope, and `azure` uses the ARM scope.
- Add feature gating, telemetry, documentation, and the cross-platform regression matrix required for rollout.

### Non-goals

- Running or wrapping `az login`, `az logout`, `az account set`, or any Azure CLI context mutation.
- Using `DefaultAzureCredential` or merging Azure CLI tokens into the MSAL cache.
- Persisting Azure CLI access or refresh tokens.
- Supporting arbitrary scopes, claims challenges, SQL, XMLA, Kusto, or non-Public Azure clouds in the first release.
- Normalizing every existing identity mode under the new `--source` syntax.

## Current Architecture

Authentication currently spans several independent paths:

- `fabric_cli.main` special-cases auth commands and uses `_execute_command` only for other one-shot commands.
- `InteractiveCLI.handle_command` parses and invokes handlers independently.
- `FabAuth` combines persistent state, environment loading, provider selection, MSAL acquisition, and interactive renewal.
- `fab_api_client.do_request` acquires tokens during request execution, which can trigger interactive renewal.
- `fab_auth.status` requests three tokens, and `FabAuth.logout` resets unrelated configuration.
- `MsalTokenCredential` supports only the current Fabric CLI provider and remains headless.
- Config-file deploy creates the credential inside a catch-all that maps failures to `DeploymentFailed`.

The implementation must separate policy, coordination, provider behavior, and persistence without regressing existing authentication modes.

## Proposed Design

### Shared parsed-command executor

Create one executor used by one-shot, batch, auth, and REPL surfaces. It will:

1. Classify the parsed command as local, passive auth, active auth, or authenticated.
2. Resolve interaction policy from command flags, output mode, host capability, CI/batch/pipe context, and `FAB_INTERACTION`.
3. Resolve the effective source using runtime environment overrides before the configured source.
4. Run authentication readiness before handler dispatch when required.
5. Invoke the parsed handler at most once and return its exit code without replay.

Local commands such as help, version, passive status, and logout bypass token acquisition. Batch execution fails fast and reports executed, failed, and skipped counts.

### Authentication coordinator

Add a coordinator responsible for source resolution, interaction eligibility, chooser orchestration, candidate validation, atomic binding, and exactly-once continuation. Provider classes remain noninteractive.

Source precedence:

1. Runtime environment credentials for the current process.
2. Persisted configured source.
3. Shared chooser only when no source exists and interaction is allowed.
4. `AuthenticationRequired` for unattended or deferred execution.

The coordinator exposes a small result model containing configured source, effective source, principal capability, readiness state, and optional checked-audience expiration. It does not expose token values.

### Provider boundary

Define a provider protocol used by `FabAuth`, HTTP requests, status checks, and the SDK bridge:

- Acquire exactly one allowlisted audience.
- Return token and expiration metadata.
- Validate tenant and principal against the active binding.
- Clear only process-local cached data for a requested audience.
- Report stable Fabric CLI errors without raw SDK or process output.

Existing MSAL user, service-principal, managed-identity, federation, certificate, and raw-token behavior remain behind the direct `fabric-cli` provider. Interactive MSAL renewal moves out of ordinary provider acquisition and is initiated only by the coordinator when policy allows it.

### Azure CLI provider

Add `azure-identity` as a dependency and implement the provider with `AzureCliCredential`:

- Resolve only a trusted Azure CLI executable through Azure Identity.
- Use disconnected standard input, no shell, a safe working directory, and a bounded 10-second acquisition.
- Pass one resolved `.default` scope per call.
- Allow only `fabric`, `storage`, `azure`, and `powerbi` route labels.
- Keep `powerbi` mapped to the existing Fabric scope.
- Cache successful tokens in process by source, tenant, principal, and audience.
- Coalesce concurrent misses for the same key; refresh inside the configured buffer; never cache failures.
- Clear and reject only the affected token when a claims challenge is returned.

The provider never invokes Azure CLI login, logout, account selection, tenant selection, or subscription selection.

### Command contract

Extend `fab auth` with:

```text
fab auth login --source azure-cli [--tenant <tenant-id>] [--no-prompt]
fab auth status [--check] [--audience fabric|storage|azure|powerbi]
```

Rules:

- Azure CLI source flags conflict with direct source flags.
- Unattended Azure CLI login requires `--tenant` and `--no-prompt`.
- Bare attended login and eligible progressive first use share the existing chooser.
- Progressive discovery offers Azure CLI only for a supported user identity.
- Workload identities require explicit login in the first release.
- Default chooser action is defer; defer returns `AuthenticationRequired` and exit 4 without writing state.
- Cancellation returns exit 2 without writing state.

### Persistent state

Evolve `auth.json` to a versioned source record:

```json
{
  "version": 2,
  "source": "azure-cli",
  "cloud": "AzureCloud",
  "tenant_id": "<canonical-guid>",
  "principal_id": "<stable-object-id>",
  "principal_type": "user",
  "account": "<approved-display-value>",
  "subscription_id": null,
  "subscription_name": null,
  "app_id": "<optional-azure-cli-client-id>",
  "bound_at": "<utc-timestamp>"
}
```

Legacy records migrate idempotently to source `fabric-cli` without deleting the MSAL cache. Candidate source replacement follows validate-then-commit semantics:

1. Validate Fabric readiness and identity.
2. Acquire the interprocess state lock.
3. Recheck the current state.
4. Atomically replace `auth.json`.
5. Preserve unrelated configuration and the prior state if any step fails.

The configuration directory remains owner-only (`0700`) and auth state remains owner-only (`0600`). Runtime environment overrides never modify persistent state.

### Identity binding

The binding pins cloud, canonical tenant ID, stable principal ID, and principal type. Subscription metadata is display-only and nullable. Every fresh token must match the binding before a service request.

The implementation mechanism for establishing stable tenant and principal identity is blocked on security decision Q4. If token-derived validation is approved, it must verify issuer, signature, audience, expiration, `tid`, and `oid`; otherwise the provider must use the approved metadata contract. Missing stable identity fails closed.

### Status and logout

Plain `fab auth status` remains exit 0 and becomes passive: no provider call, no Azure CLI process, and readiness `unknown` when local state is insufficient.

`fab auth status --check --audience <audience>` performs one active check and returns exit 0 when ready or exit 4 for readiness failures. Text output retains the current leading status line and legacy field order. Structured output retains the current envelope and legacy token keys with `"N/A"` during the deprecation window.

Logout clears only Fabric-owned state for the configured source:

- Azure CLI source: binding and in-process token cache.
- Direct source: current Fabric CLI auth state and its MSAL cache.
- All sources: Fabric CLI memory and context caches as required.

Unrelated CLI configuration and Azure CLI state remain unchanged.

### Errors and output

Add structured error definitions through `fabric_cli.errors` and constants through `fab_constant`; do not hardcode user-facing messages in handlers. Readiness errors map to exit 4, usage/conflict/cancellation errors map to exit 2, and unexpected errors remain exit 1.

All output uses existing `fab_ui` text and JSON renderers. JSON stdout contains one document; prompts and diagnostics use the diagnostic stream. Logs and telemetry exclude tokens, claims challenges, process output, command arguments, and identity identifiers.

### HTTP, SDK, deploy, and user capability integration

- `fab_api_client.do_request` requests tokens from the effective provider without allowing interaction or replay.
- Generalize `create_fabric_token_credential` behind its existing public factory so `fabric-cicd` receives a headless credential for the effective source.
- Run Fabric readiness preflight before entering deploy's catch-all so readiness failures preserve exit 4 and are not wrapped as `DeploymentFailed`.
- Replace source-specific `identity_type == "user"` checks with principal-capability checks for browser-open and personal-workspace behavior.

## Dependencies

- `azure-identity` for `AzureCliCredential`.
- Existing `azure-core`, MSAL, secure file utilities, output renderers, and command parser infrastructure.
- Security ownership and approval for executable resolution, principal binding, state, errors, and telemetry.
- Fabric agent-experience decision for the attended-host interaction channel.
- Fabric CLI engineering decision for the feature flag and rollout rings.

## Rollout and Compatibility

- Gate Azure CLI source selection and progressive offers independently where possible.
- Enable explicit unattended login before progressive offers.
- Preserve every existing direct authentication syntax and route mapping.
- Rollback disables Azure CLI selection and offers without destructively rewriting a recoverable source marker.
- Existing scripts consuming status retain legacy token keys as `"N/A"` for one deprecation window.

## Testing Strategy

### Unit tests

- Parser conflicts, source selection, interaction classification, error mapping, and output models.
- Azure CLI executable absence, timeout, sanitized failures, scope allowlist, tenant/principal mismatch, refresh, cache coalescing, and failure non-caching.
- State migration, locking, atomic replacement, permissions, failed replacement preservation, and runtime-only environment precedence.
- Passive status zero-call behavior, active single-audience behavior, and source-local logout.

### Integration tests

- Shared execution across command-line, auth, REPL, JSON, pipe, CI, callbacks, and batch paths.
- Exactly-once handler and request continuation after consent.
- HTTP route-to-scope mapping and no request replay.
- Headless SDK bridge and deploy preflight error preservation.
- Existing direct user, service-principal, certificate, federation, managed-identity, and raw-token suites.

### End-to-end and release tests

- Windows, Linux, and macOS with Azure CLI installed, absent, signed out, user signed in, workload identity, guest tenant, and no subscription.
- Identity drift, Azure CLI context race, timeout, refresh, concurrency, and claims challenge.
- Representative Fabric Skills runs using a prepared Azure CLI identity without a second interactive login.
- Feature-gate enablement, disablement, and rollback.

The parent test plan remains the acceptance evidence ledger for all 59 requirements and 40 mapped tests.

## Open Gates

| Gate | Owner | Blocks |
| --- | --- | --- |
| Q2: Select feature flag and rollout rings | Fabric CLI engineering | Rollout implementation |
| Q3: Assign final security approval owner | Fabric security and Fabric CLI leadership | Design lock |
| Q4: Approve principal identity validation mechanism | Fabric security | Binding implementation |
| Q5: Select attended-host interaction channel | Fabric agent experience and Fabric CLI | Attended-agent release |

## Implementation Plan

See [implementation-plan.md](implementation-plan.md) for the sequenced workstreams, dependencies, and proposed ADO task breakdown.
