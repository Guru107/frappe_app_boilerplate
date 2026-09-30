# 1. Consolidate Python security scanning into Semgrep instead of adding Bandit

## Status

Accepted

## Context

We want strict Python static-security analysis, beyond the Frappe-specific
`frappe/semgrep-rules` ruleset already run in `linter.yml`. The frappe
ruleset only catches Frappe-framework misuse (e.g. unsafe `frappe.db.sql`
interpolation, missing permission checks) — it does not cover general Python
security issues (hardcoded credentials, weak crypto, `subprocess
shell=True`, insecure deserialization, SSRF-prone HTTP calls, etc.), which
is Bandit's traditional territory.

The two obvious options were:

1. Add `bandit` as a second, independent tool (its own config file,
   `# nosec` suppression syntax, separate pre-commit hook, separate CI step).
2. Extend the semgrep invocation we already run with the `p/bandit` registry
   ruleset (a semgrep-native port of Bandit's checks), optionally alongside
   `p/security-audit` for broader coverage.

## Decision

Use semgrep's `p/bandit` (and `p/security-audit`) registry rulesets as an
additional `--config` on the existing `semgrep ci` invocation in
`linter.yml`, rather than installing and running `bandit` as a separate
tool.

## Consequences

- One security-scanning tool, one config surface, one suppression syntax
  (`# nosemgrep`) instead of two. **Amended 2026-09-30:** path-level
  exclusion via `.semgrepignore` is also permitted, but only for files that
  cannot carry an inline suppression — today exactly one: the vendored,
  byte-exact drift baseline under `docs/upstream/`.
- **Scope note (amended 2026-09-17):** this ADR covers *Python code* security
  scanning only. **Secrets scanning** (API keys, tokens committed to the
  repo) is a separate category of check with its own dedicated tool; adding
  one does not violate this ADR's "no second scanner" rule, because semgrep
  (with the frappe rules + correctness rules) does not scan for secrets.
- We depend on the semgrep registry's `p/bandit` port staying reasonably in
  sync with upstream Bandit's checks; if it drifts noticeably, revisit this
  decision and add Bandit directly.
- A future contributor searching for "why isn't Bandit in this repo" needs
  this record — the omission is deliberate, not an oversight.
