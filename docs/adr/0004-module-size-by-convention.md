# 4. Keep module size a review convention, not a linter rule

## Status

Accepted

## Context

This repo is agent-forward (AGENTS.md, CodeGraph, agent skills): agents read
whole files, so oversized modules are genuinely expensive in its primary
workflow, and 2000-line DocType controllers are the classic failure mode of
growing Frappe apps. A natural ask is a CI-enforced file-length rule.

Three facts argue against the rule:

1. **The toolchain can't express it cleanly.** Ruff never ported pylint's
   `C0302` (`too-many-lines`); the PLR refactor tier (which includes
   function-level `PLR0915` too-many-statements) is deliberately excluded
   from our ruff selection because it fights Frappe idioms and duplicates
   C90. A file-length gate would require a bespoke script — a one-off tool
   in a repo whose bar is curated, CI-enforced check categories.
2. **Frappe conventions legitimately produce long files.** `hooks.py` is a
   declarative registry, DocType `*.json` files are generated artifacts,
   test modules and patches grow by accretion. A rule's main output would be
   an exemption list, and a gate that mostly gets waived teaches people to
   waive gates.
3. **No first-party prior art.** Neither frappe core nor hrms/erpnext
   enforces file length; the starter's pitch is curating what mature apps
   do, exceeding them only where a check is cheap and high-signal.

The existing static-analysis stack already pressures the underlying problem:
C90 caps function complexity, SIM/ANN/basedmypy push small typed units.

## Decision

Module size is a **review convention documented in AGENTS.md**, not a
linter rule: split a Python module when it gains a second responsibility,
and treat ~400–500 lines of hand-written code as the threshold that should
trigger the question. `hooks.py`, DocType `*.json`, test modules, and
patches are exempt by nature.

AGENTS.md survives `rename.py` into every derived app, so the convention
propagates to consumers automatically — that propagation, not CI
enforcement, is the mechanism.

## Consequences

- Agents and humans get a concrete, quotable number (400–500 lines) plus a
  responsibility-based trigger, without any tooling or exemption-list
  maintenance.
- Nothing fails CI over file length; compliance relies on code review
  (human or agent). Accepted: the cost of a false-positive-prone gate
  exceeds the cost of occasional drift.
- If a future Frappe-major toolchain gains a cheap file-length check (e.g.
  ruff ports `C0302`), this decision can be revisited — the convention's
  threshold is the ready-made value for it.
