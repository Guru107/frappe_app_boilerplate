# 5. Docstring correctness over coverage; no dead-code or complexity-metric tooling

## Status

Accepted

## Context

Following the research in
`docs/research/2026-09-30-review-simplicity-tooling.md` (primary-sourced),
three tooling categories were evaluated for keeping the codebase simple and
review-friendly, each closing a category that would otherwise be
re-proposed:

1. **Docstrings.** The ruff `D` (pydocstyle) family was rejected at
   adoption time because docstring *coverage* gates fight Frappe's
   undocumented-hook idiom. But coverage was never the only axis:
   docstring *correctness* (documented parameters actually matching the
   signature) is review signal with no coverage cost — undocumented
   functions are simply skipped. The candidates were pydoclint, darglint,
   darglint2, and ruff's preview `DOC` family.
2. **Dead-code detection (vulture).** Attractive for simplicity, but Frappe
   is an inversion-of-control framework: DocType controller hooks,
   `hooks.py` entries, and whitelisted endpoints are bound by dotted-path
   string and all *look* unused to static analysis. Vulture's whitelist
   mechanism would become a second registry duplicating `hooks.py`.
3. **Complexity metrics (radon / xenon).** Radon is unmaintained since
   2023; its maintainability index is a length-dominated composite, and
   file length is deliberately a review convention here (ADR 0004). Ruff's
   C901 with a tunable `max-complexity` is the zero-new-tool gate already
   in place.

## Decision

1. Adopt **pydoclint** (Google style, `skip-checking-short-docstrings`) for
   docstring correctness-without-coverage. darglint (archived 2021) and
   darglint2 (stale fork, 2023) are rejected; ruff `DOC` is preview-only
   and covers a fraction of the rules — when it stabilizes, it *replaces*
   pydoclint (one tool per category).
2. **Reject vulture.** No dead-code detector is adopted; ruff's F/PIE
   families cover the statically-reachable subset, and framework-bound code
   is reviewed by humans.
3. **Reject radon/xenon.** C901 remains the only complexity gate.

## Consequences

- The earlier `D` rejection is narrowed in meaning: it was a rejection of
  *coverage*, never of *correctness*. The pyproject comment records this.
- Future proposals for vulture, radon, darglint, or a docstring-coverage
  gate should be pointed here, not re-debated.
- If ruff `DOC` stabilizes, pydoclint is removed in the same commit that
  selects `DOC` — one tool per category.
