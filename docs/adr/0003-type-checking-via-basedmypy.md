# 3. Static type checking via basedmypy, scoped like Frappe core

## Status

Accepted

## Context

This starter's "rock solid" bar includes real static type checking, but the
Frappe ecosystem offers almost no precedent: as of Sept 2026 no first-party
app (hrms, erpnext, insights, builder, crm) runs any type checker in CI or
pre-commit. Frappe core itself (v16) runs `basedmypy` in CI, but
deliberately scoped: `strict = false`, an explicit `files=` list covering
only `frappe/types/*`, and many ignored error codes — the framework's dynamic
nature (runtime DocType classes, dynamic `frappe.get_doc` returns) makes
repo-wide strict typing unachievable. Frappe core also ships
`pypika-stubs` and the `frappe.types.DF` module of DocField-type aliases for
annotating DocType controller fields.

The options were: (a) adopt basedmypy mirroring frappe core's own config;
(b) adopt pyright (better UX, zero ecosystem precedent); (c) skip type
checking (what every first-party app does).

## Decision

Option (a): basedmypy, configured like frappe core — `strict = false`,
`ignore_missing_imports` for framework internals, and an explicit `files=`
list covering the app's own modules rather than the whole tree. Consumers
widen the `files=` list as their app grows; the starter ships with its own
scaffold modules covered, including the example type-annotated whitelisted
API method (which doubles as living documentation of
`require_type_annotated_api_methods`).

## Consequences

- We are pioneering: when the config fights frappe's dynamism, there is no
  app-level precedent to copy, only frappe core's. Escape hatches
  (per-module `disable_error_code`, widening ignores) should be exercised
  before relaxing `strict` further.
- Type checking is CI-enforced from day one, so derived apps inherit the
  habit; removing it later is a one-line CI deletion, so this is reversible
  for consumers even though it shapes the starter's identity.
- Complements, does not replace, the ruff expansion (SIM/C90/selected-PL/ANN)
  decided alongside it; security rules (S) remain with semgrep per ADR 0001.
- **Amended 2026-09-30:** the config proved stricter than frappe core's in
  practice — `disallow_untyped_defs`, `warn_return_any`,
  `warn_unused_ignores`, and `warn_redundant_casts` were enabled after
  verifying they produce zero findings on the shipped code. The Any-related
  relaxations above stay off-limits (they fight framework dynamism); these
  four only demand complete annotations and honest `Any` hygiene, which a
  new app can sustain from day one. The ruff selection was expanded at the
  same time (C4/EM/TRY/RET/PERF/FURB/LOG/G/FA/N/TID/ISC/PTH/EXE/T20 — all
  verified zero-finding; DTZ/SLF/FIX/D/PLC/ERA/A evaluated and rejected for
  fighting Frappe idioms, recorded inline in `pyproject.toml`).
