# AGENTS.md

Frappe app (built by `bench new-app`), not a standalone Python package. It only
runs inside a [bench](https://github.com/frappe/bench) environment alongside
Frappe, MariaDB, and two Redis instances — there is no local dev server,
virtualenv, or `pytest` flow in this repo.

Domain terms (Marketplace-ready, Settings DocType, strict tooling) are defined
in `CONTEXT.md`; security-scanning rationale in `docs/adr/0001-security-scanning-via-semgrep.md`.

## CodeGraph

This repo is indexed by CodeGraph (`.codegraph/` at the root). Reach for it
BEFORE grep/find or reading files when you need to understand or locate code:
`codegraph explore "<symbol names or question>"` (shell, always works) or the
`codegraph_explore` MCP tool returns the relevant symbols' verbatim source plus
call paths in one call. Don't re-verify its results with grep.

## Commands

| Task | Command |
| --- | --- |
| Lint + format everything | `pre-commit run --all-files` |
| Tests | `bench --site test_site run-tests --app frappe_app_boilerplate` |
| One test module | add `--module frappe_app_boilerplate.path.to.module` |
| One test | add `--test <test_name>` |
| Security scan (as CI) | `semgrep ci --config <frappe-semgrep-rules>/rules --config r/python.lang.correctness` |
| Dependency audit | `pip-audit --desc on .` |

- Tests require a bench with the app installed and
  `bench --site test_site set-config allow_tests true`. Full setup sequence is
  in `.github/workflows/ci.yml` (bench init → get-app → new-site → install-app
  → bench build).
- README says CI runs on `develop`; the workflow actually triggers on `main` + PRs. Trust the workflow.

## Layout

- `frappe_app_boilerplate/` is the Python package; `hooks.py` is the extension
  point (all Frappe hooks; `use_json_request_body`, `export_python_type_annotations`,
  and `require_type_annotated_api_methods` are active, the rest commented stubs).
  Never patch Frappe core; hook-based extension only.
- `frappe_app_boilerplate/frappe_app_boilerplate/` is the module dir named in
  `modules.txt`; DocTypes go in a `doctype/<name>/` subdir under it. Ships the
  Settings DocType (`frappe_app_boilerplate_settings/`) and one example DocType
  (`boilerplate_example/`, marked DELETE ME AFTER RENAME).
- All tests subclass `BoilerplateTestSuite` (`frappe_app_boilerplate/tests/`),
  the app-level base class absorbing the v15/v16 `FrappeTestCase` /
  `IntegrationTestCase` divergence (ADR 0002). Never subclass framework test
  classes directly.
- DB patches: create `frappe_app_boilerplate/patches/<name>.py` AND register it
  in `patches.txt` under `[pre_model_sync]` or `[post_model_sync]`, or it never runs.
- Frappe is a bench-managed dependency (commented out in `pyproject.toml` on
  purpose). Don't add it to `dependencies`.

## Style & tooling quirks

- Python ≥ 3.14 (ruff `target-version = "py314"`). Ruff: **tab indentation**,
  double quotes, line-length 110, `E501`/`F401` ignored.
- Pre-commit runs ruff (import-sort + lint + format), prettier (js/vue/scss),
  eslint 8, gitleaks (secrets), and markdownlint-cli2 (config in
  `.markdownlint-cli2.jsonc`). CI additionally runs commitlint
  (config-conventional) on PR commits. Prettier/eslint exclude `public/dist/`,
  `templates/includes/`, `public/js/lib/`, and any path containing
  `boilerplate` — files there are intentionally unlinted (may contain jinja or
  vendored bundles).
- No Bandit: ADR 0001 deliberately consolidated Python security scanning into
  semgrep. Suppress findings with `# nosemgrep`, not `# nosec`. Don't add a
  second security scanner without revisiting the ADR. Note: the ADR mentions
  `p/bandit`/`p/security-audit` configs, but `linter.yml` only runs the frappe
  rules + `r/python.lang.correctness` today — the workflow is the truth.

## Agent skills

### Issue tracker

Issues are tracked as GitHub issues via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles are used as-is (`needs-triage`, `needs-info`,
`ready-for-agent`, `ready-for-human`, `wontfix`). See
`docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
