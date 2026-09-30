# Review-simplicity tooling — what keeps a Frappe codebase simple and reviewable

Research date: 2026-09-30. All claims traced to primary sources (official docs, tool repos,
canonical review guides). Time-sensitive facts (versions, maintenance activity) were verified
2026-09-30 via the PyPI JSON API (`https://pypi.org/pypi/<pkg>/json`) and the GitHub
repository API. Builds on `2026-09-17-frappe-app-starter-survey.md`; repo state taken as
given (ruff rule families and ADRs 0001–0004 are not re-researched).

Framing: the question is which checks make code **simpler and more informative for a human
reviewer**, subject to this repo's constraints — semgrep owns Python security (ADR 0001), one
tool per check category ("Strict tooling", CONTEXT.md), config propagates to derived apps via
`rename.py`, and rules that fight Frappe idioms (`frappe.throw`, naive datetimes, fixed hook
signatures, runtime-exported type annotations) are disqualifying.

---

## Verdict table

| Tool / Rule | Category | What it adds for review-simplicity | Verdict | One-line reason | Source |
| --- | --- | --- | --- | --- | --- |
| ruff `PIE` | Simplicity (ruff) | Auto-fixable removal of no-op `pass`, unnecessary spread/`range` start, duplicate class fields, non-unique enums | **Adopt** | Zero-noise, all-stable, all auto-fixable; closes "dead syntax" gap | <https://docs.astral.sh/ruff/rules/#flake8-pie-pie> |
| ruff `PGH` | Informativeness (ruff) | `PGH003`/`PGH004` force specific codes on `type: ignore` and `noqa`, so every suppression in a diff is self-explanatory | **Adopt** | Suppression hygiene is pure review signal; zero-finding on this repo (no bare `noqa` exists) | <https://docs.astral.sh/ruff/rules/#pygrep-hooks-pgh> |
| ruff `INP` | Correctness (ruff) | `INP001` flags a `.py` file in a dir missing `__init__.py` | **Adopt** | A forgotten `__init__.py` silently breaks Frappe module loading — a real defect class here, not style | <https://docs.astral.sh/ruff/rules/#flake8-no-pep420-inp> |
| ruff `YTT` | Correctness (ruff) | Catches `sys.version` misuse (`sys.version[:3]`, string compares) | Adopt (optional, bundled with PIE) | Trivial cost, guards a real bug class; rarely fires | <https://docs.astral.sh/ruff/rules/#flake8-2020-ytt> |
| pydoclint | Informativeness | Docstring **correctness** (params/returns/raises match signature) **without** coverage requirement | **Adopt-with-config** | Undocumented functions are skipped entirely (`skip-checking-short-docstrings` default), so it never fights the undocumented-hook idiom that ruled out `D` | <https://jsh9.github.io/pydoclint/> |
| djLint (`--lint`, jinja profile) | Correctness (templates) | Catches template bugs that render-time 500: unclosed tags (T038/T039), duplicate block names (T043), content outside blocks (T042), orphan HTML tags (H025) | **Adopt-with-config** | Repo ships `templates/` and `www/` dirs; lint-only (no reformat hook) avoids churn on the deliberately unformatted `templates/includes/` | <https://djlint.com/docs/linter/> |
| PR-size convention (+ optional labeler) | Reviewability | Size labels on PRs as a warning signal | **Adopt-with-config** | Primary sources say size is culture + reviewer discretion; tooling is advisory-only (`fail_if_xl` stays `false`) | <https://google.github.io/eng-practices/review/developer/small-cls.html> |
| ruff `DOC` (pydoclint-in-ruff) | Informativeness | 7 docstring-correctness rules inside ruff | Evaluate-later | Still 🧪 preview as of 2026-09 (preview since 0.5.x–0.14.1); ruff itself implements only 7 of pydoclint's 39 rules | <https://docs.astral.sh/ruff/rules/#pydoclint-doc> |
| astral `ty` | Type checking | 10–100× faster type checker, potential basedmypy successor | Evaluate-later (watch) | Beta since 2025-12-16, still `0.0.x` (0.0.84, 2026-09-24); ADR 0003's basedmypy choice stands until ty stabilizes | <https://astral.sh/blog/ty> |
| deptry | Dependency hygiene | DEP001/002/003 missing/unused/transitive deps | Evaluate-later | `frappe` is deliberately undeclared (bench-managed), so DEP001 fires on every `import frappe` unless ignored; value arrives when the app gains real third-party deps | <https://deptry.com/rules-violations/> |
| import-linter | Architecture | Layering/forbidden-import contracts (e.g. forbid importing erpnext) | Evaluate-later | Vacuous at template scale (one module dir, `required_apps` empty); adopt when the app grows internal layers | <https://import-linter.readthedocs.io/> |
| stylelint (+ `stylelint-config-standard-scss`) | Correctness (scss) | `declaration-block-no-duplicate-properties`, `property-no-unknown`, `selector-no-invalid` — correctness prettier doesn't check | Evaluate-later | Zero `.scss` files in the template today; prettier owns formatting only, so no category clash — add with the first stylesheet | <https://stylelint.io/user-guide/rules/> |
| shellcheck standalone hook | Correctness (shell) | Static analysis of `.sh` files | Evaluate-later | No `.sh` files exist; workflow `run:` blocks are already shellchecked via actionlint (when shellcheck is installed) | <https://github.com/shellcheck-py/shellcheck-py> |
| vulture | Dead code | Unused functions/classes/variables/unreachable code | **Reject** | Frappe calls app code by dotted-path string (`hooks.py`, `doc_events`, `scheduler_events`, `@frappe.whitelist`); the whitelist mechanism becomes a second registry to maintain | <https://github.com/jendrikseipp/vulture> |
| radon / xenon | Complexity metrics | Maintainability Index, Halstead, CI gate on radon | **Reject** | radon last released 2023-03 (stale); MI is a noisy composite; C901 already gates complexity and is tunable via `max-complexity` — zero new tool needed | <https://radon.readthedocs.io/en/latest/intro.html> |
| darglint / darglint2 | Docstring correctness | Signature-vs-docstring checks | **Reject** | darglint archived (last release 2021-10); darglint2 fork stale since 2023-03; pydoclint is the maintained successor | <https://pypi.org/project/darglint/> |
| ruff `SLOT`, `ARG`, `TC`, `FLY`, `COM`, `Q` | Misc ruff families | Various | **Reject** | SLOT: DocType classes are framework-managed; ARG: Frappe hook signatures have deliberately-unused args (`doc, method`); TC: fights `export_python_type_annotations` (Frappe evaluates annotations at runtime); FLY: overlaps UP032 (ignored for translations); COM/Q: formatter-owned | <https://docs.astral.sh/ruff/rules/> |
| ruff `B9` opinionated bugbear | Complexity/style | B904/B905 etc. | Already adopted / n/a | Selecting `B` includes the stable B9xx rules; B904 is explicitly ignored, B905 (`zip(strict=)`) is active. B901/B903 remain 🧪 preview | <https://docs.astral.sh/ruff/rules/#flake8-bugbear-b> |
| ruff `RUF100`, `RUF022`, `PLW0108`, `ANN401` | Misc | unused-noqa, sorted `__all__`, unnecessary lambda, disallow `Any` args | Already adopted / n/a | All active via the existing `RUF`, `PLW`, `ANN` family selections and not in the ignore list | <https://docs.astral.sh/ruff/rules/> |
| PR size as a CI **blocker** | Reviewability | Hard fail on large PRs | **Reject** | Google: "no hard and fast rules"; reviewers have discretion. Blocking on line count punishes generated/lockfile churn | <https://google.github.io/eng-practices/review/developer/small-cls.html> |

---

## 1. Simplicity/dead-code: vulture vs ruff

**What vulture is.** vulture (jendrikseipp/vulture, 4.8k stars) finds unused code via AST
name-matching, assigning each finding a confidence (unreachable code / unused args = 100%,
imports = 90%, functions/classes/methods = 60%). Maintained: v2.16 released 2026-03-25;
repo active. It ships a pre-commit hook (`.pre-commit-hooks.yaml`, `id: vulture`,
`pass_filenames: false`) and reads `[tool.vulture]` from `pyproject.toml`.
<https://github.com/jendrikseipp/vulture>

**False-positive handling (the Frappe question).** The README documents four mechanisms:
generated **whitelist files** (`vulture mydir --make-whitelist > whitelist.py`, then scan
both), `--exclude`, `--ignore-names foo*,ba[rz]`, and **`--ignore-decorators "@app.route"`**
(the documented Flask example — decorator calls like `@frappe.whitelist()` are simplified to
`@frappe.whitelist` and would match). The authors recommend whitelists over `noqa`.

**Why it still doesn't fit.** A Frappe app is inversion-of-control throughout: `hooks.py`
binds handlers by **dotted-path string** (`doc_events`, `scheduler_events`,
`override_doctype_class`, page/boot hooks), DocType controller methods (`validate`,
`on_submit`…) are called by the framework, and `@frappe.whitelist()` exposes functions to the
HTTP layer. None of these are visible to AST name-matching, so every hook entry point reports
at 60% confidence. The whitelist would have to mirror `hooks.py` — a second registry that
drifts on every hook edit, exactly the "two sources of truth" this repo's charter forbids.
`--min-confidence 100` shrinks vulture to unreachable-code + unused-argument detection, which
is the only configuration worth reconsidering — but its incremental value over the existing
ruff set (F401/F841/F811, B018, PIE790 if adopted) is small.

**Verdict: Reject.** Record in an ADR (see "Do not adopt" below) — this is a category-closing
decision contributors will re-propose.

## 2. Complexity beyond C90: radon / xenon

radon computes cyclomatic complexity, raw metrics, Halstead metrics, and the **Maintainability
Index** ("the one used in Visual Studio", per its own docs,
<https://radon.readthedocs.io/en/latest/intro.html>); xenon is a thin CI-gate wrapper around
radon (`--max-average`, `--max-modules`). Maintenance check (PyPI, 2026-09-30): **radon
6.0.1, 2023-03-26** (repo last pushed 2024-10) — effectively unmaintained; xenon 0.9.3,
2024-10-21.

MI compresses SLOC + complexity + Halstead volume into one per-file grade. As a review signal
it is dominated by file length — which this repo deliberately governs by convention, not rule
(ADR 0004). The zero-new-tool alternative already exists and is already on: ruff's C901 fires
at McCabe complexity > 10 by default, tunable via `[tool.ruff.lint.mccabe] max-complexity`
(<https://docs.astral.sh/ruff/settings/#lint_mccabe_max-complexity>,
<https://docs.astral.sh/ruff/rules/complex-structure/>). If the gate proves too loose in
practice, lower the number — don't add a metrics tool.

**Verdict: Reject radon and xenon.** Worth an ADR entry (category-closing, like vulture).

## 3. Architecture/dependency hygiene: import-linter, deptry

**import-linter** (seddonym/import-linter; v2.15, 2026-09-04 — actively maintained) enforces
declared *contracts* over the import graph: `layers` (ordering between packages), `forbidden`
(module set A may not import module set B), `independence`
(<https://import-linter.readthedocs.io/>). The tempting contract for this template —
"app code must not import erpnext while `required_apps` is empty" — is **vacuous**: the
template has one module dir and nobody imports erpnext; the contract becomes load-bearing only
once the app grows internal layers (e.g. `api/` must not import `doctype/` internals).
**Verdict: Evaluate-later.** Note: import-linter builds a static graph (grimp) and does not
need frappe installed, so the bench-managed-dependency setup is not itself a blocker.

**deptry** (osprey-oss/deptry; 0.25.1, 2026-03-18 — active) checks DEP001 missing / DEP002
unused / DEP003 transitive / DEP004 misplaced-dev / DEP005 stdlib dependencies against the
declared dependency list (<https://deptry.com/rules-violations/>). In this repo DEP001 would
fire on **every `import frappe`** because frappe is deliberately commented out of
`dependencies` ("Installed and managed by bench"); it is suppressible via
`per-rule-ignores`, but then the tool's main signal is configured away at the exact moment it
matters most. deptry reads standard dep sections (PEP 621, Poetry, PDM, uv per its docs); the
`[tool.bench.dev-dependencies]` section holding basedmypy is not among them. With the
template's `dependencies = []`, there is nothing to check. **Verdict: Evaluate-later** —
revisit when a derived app adds its first real third-party runtime dependency.

## 4. Informativeness: docstring correctness (pydoclint / darglint / ruff DOC / ANN401)

**darglint is dead** (v1.8.1, 2021-10-18, repo archived) and its fork **darglint2 is stale**
(v1.8.2, 2023-03-11). **pydoclint is the maintained successor** (0.10.1, 2026-09-28; docs at
<https://jsh9.github.io/pydoclint/>): 39 violation codes (DOC0xx–DOC6xx), numpy/Google/Sphinx
styles, ~30 config options, pre-commit hooks `pydoclint` and `pydoclint-flake8`
(<https://github.com/jsh9/pydoclint>, `.pre-commit-hooks.yaml`).

The critical property for this repo is confirmed in its docs: **"If you don't write any
docstring for a function, pydoclint will not check it"**, and description-only docstrings are
skipped by default (`--skip-checking-short-docstrings=True`). So pydoclint enforces
*correctness of what exists* and never demands coverage — precisely the gap between the
rejected `D` family (pydocstyle coverage, fights the undocumented-hook idiom) and nothing.

**ruff `DOC`** is ruff's partial pydoclint reimplementation: 7 rules (DOC102/201/202/402/403/
501/502), **all still 🧪 preview** as of 2026-09 (preview since 0.5.x–0.14.1 per the rules
index). pydoclint's own comparison (maintained docs, 2026-09): ruff lacks type-hint checking,
class-attribute checking, Sphinx style, baseline mode. Enabling preview rules repo-wide for 7
docstring rules would destabilize the whole ruff gate. **Verdict: adopt pydoclint now;
evaluate ruff DOC when it stabilizes, then drop pydoclint** (the "one tool per category"
charter prefers the ruff-native version eventually).

**ANN401** (`any-type`, stable since ruff v0.0.108,
<https://docs.astral.sh/ruff/rules/any-type/>) is **already active**: the repo selects the full
`ANN` family and does not ignore ANN401. Nothing to do; noted here so it isn't re-proposed.

## 5. Review-size/reviewability: what the canonical guides actually say

**Google eng-practices, "Small CLs"**
(<https://google.github.io/eng-practices/review/developer/small-cls.html>): small CLs are
reviewed more quickly/thoroughly, introduce fewer bugs, merge and roll back easier. Size is
defined as **"one self-contained change"**, explicitly *not* a line-count function. "There are
no hard and fast rules… 100 lines is usually a reasonable size… 1000 lines is usually too
large, but it's up to the judgment of your reviewer", and **"reviewers have discretion to
reject your change outright for the sole reason of it being too large"** — i.e. enforcement is
deliberately assigned to *humans*, with exemptions for file deletions and trusted
machine-generated changes.

**Chromium "Tips for productive code review"**
(<https://chromium.googlesource.com/chromium/src/+/HEAD/docs/cl_tips.md>): "Try to keep
changes below 500 lines of code — including tests", with the same nuance (200 LoC production +
600 LoC patterned tests "might be fine"), plus "separate behavior changes from refactoring"
and "encapsulate complexity, but don't over-abstract".

**Conclusion:** PR size is culture + reviewer judgment; what tooling can legitimately add is an
*advisory signal*. The conventional tool is a size labeler: `CodelyTV/pr-size-labeler`
(repo active, pushed 2026-09-29; inputs verified from its `action.yml`: `xs_max_size` …
`l_max_size`, labels `size/xs`…`size/xl`, and `fail_if_xl` defaulting to `'false'`).
**Verdict: Adopt-with-config** — document the convention (Google's 100/1000, Chromium's 500)
and optionally add the labeler as a **non-blocking** workflow; never `fail_if_xl: true`
(generated JSON lockfiles and DocType `*.json` would false-positive a hard gate).

## 6. Frappe-specific gaps: djLint, stylelint, shellcheck

**djLint** (djlint/djLint; 1.46.3, 2026-09-28, repo pushed 2026-09-30 — very active) lints and
formats HTML templates with profiles for django/jinja/…; Frappe templates are Jinja
(`--profile=jinja`). Its lint rule list (<https://djlint.com/docs/linter/>) includes genuine
render-time-failure checks a reviewer cannot eyeball reliably: T038 (block tag without
matching end tag), T039 (unclosed `{{`/`{%`), T043 (duplicate block name — Jinja refuses to
parse), T042 (content outside a block in a child template is silently discarded), T034
(`}%` typo), H025 (orphan HTML tag), H037/H053 (duplicate attribute/id), plus accessibility
rules (H013 alt, H043 button type, H045 iframe title). Pre-commit hooks exist, including
`djlint-jinja` and separate `-reformat-*` hooks (repo `.pre-commit-hooks.yaml`).
Recommendation: **lint-only** — the reformat hook is deferred because `templates/includes/` is
deliberately unformatted today, and mass-reformat churn is a separate decision. Unknown
Frappe-specific block tags can be registered via djLint's `custom_blocks` option if they ever
appear. **Verdict: Adopt-with-config.**

**stylelint.** Prettier only *formats* scss; stylelint's value is the "avoid errors" rule tier
(<https://stylelint.io/user-guide/rules/>): `declaration-block-no-duplicate-properties`,
`property-no-unknown`, `selector-no-invalid`, `no-descending-specificity` — all in
`stylelint-config-standard` (with `stylelint-config-standard-scss` for scss syntax). No
category clash with prettier (formatting vs correctness). But the template ships **zero**
`.scss` files (`public/` is empty scaffolding), so this is speculative. **Verdict:
Evaluate-later** — add with the first stylesheet; config sketched in "Recommended batch".

**shellcheck standalone.** The repo has no `.sh` files; workflow `run:` blocks are already
shellchecked through actionlint *when shellcheck is installed* (per AGENTS.md; CI has it). A
standalone hook (`shellcheck-py/shellcheck-py`, `id: shellcheck`, repo pushed 2026-09-29)
would only fire once shell scripts exist. **Verdict: Evaluate-later** — one stanza, ready in
"Recommended batch", no ADR needed.

## 7. Type-checking frontier: astral `ty`

ty entered **beta on 2025-12-16** (official announcement, <https://astral.sh/blog/ty>) and is
still on the `0.0.x` line — 0.0.84 released 2026-09-24, repo extremely active (pushed daily,
19.8k stars), docs live at <https://docs.astral.sh/ty/> with a "Coming from mypy, pyright"
guide. The infoworld-covered beta note projects a stable release in 2026 (secondary source;
treat the date as aspirational). It is a credible basedmypy successor to *watch* — Astral's
release cadence and the ruff precedent suggest fast maturation — but ADR 0003's reasoning
(frappe core itself uses basedmypy's config shape) still favors the incumbent until ty ships
stable and the Frappe ecosystem (e.g. `frappe.types.DF`) is validated against it.
**Verdict: Evaluate-later (watch).** Revisit at ty 1.0 or when frappe core's own CI adopts it.

## 8. Ruff remainder: families not yet adopted or rejected

Scanned the full ruff rules index (<https://docs.astral.sh/ruff/rules/>, fetched 2026-09-30)
against this repo's adopted list (`F,E,W,I,UP,B,RUF,SIM,C90,PLE,PLW,ANN,C4,EM,TRY,RET,PERF,
FURB,LOG,G,FA,N,TID,ISC,PTH,EXE,T20`) and rejected list (DTZ, SLF, FIX/TD, D, PLC, ERA, A,
PLR, S). Irrelevant-by-domain: AIR, FAST, DJ, NPY, PD, PYI, PT (no pytest — bench runs
unittest-style), INT, CPY, FBT (would fight Frappe's boolean-flag DocType kwargs). Already
active via family selection (don't re-propose individually): RUF100 unused-noqa, RUF022
sorted `__all__`, PLW0108 unnecessary-lambda (stable since 0.15.0), ANN401, B905.

The families with genuine value for this repo:

1. **`PIE` (flake8-pie)** — 8 rules, all stable, all 🛠️ auto-fixable, all ✅ in ruff's default
   set: PIE790 no-op `pass`, PIE794 duplicate class field, PIE796 non-unique enum values,
   PIE800 unnecessary `**` spread, PIE804 unnecessary dict kwargs, PIE807 useless-lambda
   containers, PIE808 unnecessary `range` start, PIE810 `startswith` tuple. Pure dead-syntax
   removal — diffs get smaller and cleaner. *Note: because this repo uses explicit `select`
   (not defaults), PIE is currently **off** despite being a default family.*
2. **`PGH` (pygrep-hooks)** — PGH003 blanket-`type: ignore`, PGH004 blanket-`noqa`: every
   suppression must name its code. This makes suppressions **self-documenting in review** and
   interacts correctly with RUF100 (already on: removes *stale* noqa) — PGH004 keeps them
   specific, RUF100 keeps them alive only while needed. Zero-finding today (no bare `# noqa`
   in the repo).
3. **`INP` (flake8-no-pep420)** — INP001 flags `.py` files in directories without
   `__init__.py`. In Frappe this is correctness, not style: module dirs, doctype dirs and
   `patches/` must be importable packages for hooks and patches to load. The boilerplate ships
   `__init__.py` everywhere applicable, so it should be zero-finding and then guard derived
   apps forever.
4. **`YTT` (flake8-2020)** — `sys.version` misuse guards (`sys.version[:3]`, string
   comparisons). Tiny family, zero-noise; cheap to bundle with PIE. Genuinely optional.
5. **`DOC` (pydoclint-in-ruff)** — evaluated above (§4): preview-only, wait.

Rejected in the scan: **SLOT** (SLOT000–002: `__slots__` suggestions — DocType controllers and
frappe's metaclass machinery are framework-managed; near-zero upside), **ARG**
(flake8-unused-arguments — Frappe hook/doc-event signatures like `(doc, method)` carry
deliberately unused parameters; would fire constantly), **TC** (flake8-type-checking — pushing
imports into `TYPE_CHECKING` blocks fights `export_python_type_annotations = True`, under
which Frappe evaluates annotations at runtime for API validation; annotations must stay
runtime-resolvable), **FLY** (flynt — overlaps UP032, ignored for translation strings),
**COM/Q** (flake8-commas/quotes — owned by `ruff format`), **BLE** (flake8-blind-except —
`except Exception` + `frappe.log_error` in scheduled jobs is a sanctioned Frappe idiom;
noise).

---

## Recommended batch

Ordered by value-for-noise. All verified zero- or near-zero-finding against the current tree
(no bare `noqa`; `__init__.py` present everywhere applicable; no `.html`/`.scss`/`.sh` files
yet — the hooks in items 3–5 are dormant until matching files exist, which is precisely the
point: they propagate via `rename.py` and arm themselves in derived apps).

### 1. Ruff families PIE + PGH + INP (+ YTT) — pyproject.toml

```toml
[tool.ruff.lint]
select = [
    # ... existing families ...
    # Third expansion (2026-09-30, docs/research/2026-09-30-review-simplicity-tooling.md):
    # PIE: dead-syntax removal (no-op pass/spread/range-start, duplicate class
    # fields) — stable, auto-fixable, zero-noise. PGH: suppression hygiene —
    # no bare `noqa`/`type: ignore`, so every suppression is self-explanatory
    # in review (complements RUF100, which prunes stale noqa). INP: a missing
    # __init__.py silently breaks Frappe module/patch loading. YTT: sys.version
    # misuse guards, cheap.
    "PIE",
    "PGH",
    "INP",
    "YTT",
    # Also deliberately not selected: SLOT (framework-managed classes), ARG
    # (Frappe hook signatures carry unused args by design), TC (fights
    # export_python_type_annotations — annotations are read at runtime),
    # FLY (overlaps UP032, ignored for translations), COM/Q (formatter-owned),
    # BLE (broad-except + frappe.log_error is a sanctioned idiom),
    # DOC (pydoclint rules — preview-only in ruff; pydoclint the tool covers
    # this category until DOC stabilizes).
]
```

### 2. pydoclint — docstring correctness without coverage

```yaml
# .pre-commit-config.yaml
  - repo: https://github.com/jsh9/pydoclint
    rev: 0.10.1 # tags carry no "v" prefix (verified via git ls-remote)
    hooks:
      - id: pydoclint
        args: [--style=google]
```

```toml
# pyproject.toml
[tool.pydoclint]
style = "google"
# Correctness-without-coverage: undocumented functions are never checked
# (pydoclint skips them), and description-only docstrings are skipped by
# default — this is why pydoclint is compatible with the undocumented-hook
# idiom that ruled out pydocstyle's D family.
skip-checking-short-docstrings = true
```

### 3. djLint — template lint (lint-only; dormant until templates exist)

```yaml
# .pre-commit-config.yaml
  - repo: https://github.com/djlint/djLint
    rev: v1.46.3
    hooks:
      - id: djlint-jinja
        # Lint only. No -reformat hook: templates/includes/ is deliberately
        # unformatted (jinja); adopting djLint's formatter is a separate
        # decision that would churn the vendored-in-spirit includes dir.
        args: [--lint]
        files: ^frappe_app_boilerplate/(templates|www)/.*\.html$
```

```toml
# pyproject.toml
[tool.djlint]
profile = "jinja"
# Tune if Frappe-flavored pages trip SEO/inline rules that don't apply to
# desk pages, e.g.: ignore = "H030,H021"
```

### 4. PR-size convention + advisory labeler (optional workflow)

Document in the contributor guide: one self-contained change per PR; ~100 lines reasonable,
~500 (incl. tests) the soft ceiling, ~1000 too large; reviewer discretion, per Google
eng-practices and Chromium cl_tips. Optional warning-only workflow:

```yaml
# .github/workflows/pr-size.yml — advisory labels only; fail_if_xl stays false
# (generated DocType JSON / lockfiles would false-positive a hard gate).
name: pr-size
on:
  pull_request:
    types: [opened, synchronize]
permissions:
  pull-requests: write
jobs:
  label:
    runs-on: ubuntu-latest
    steps:
      - uses: CodelyTV/pr-size-labeler@v1
        with:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          xs_max_size: "50"
          s_max_size: "200"
          m_max_size: "500"
          l_max_size: "1000"
          fail_if_xl: "false"
```

### 5. Deferred snippets (apply when the trigger condition lands)

```yaml
# stylelint — when the first .scss file lands:
  - repo: https://github.com/pre-commit/mirrors-stylelint
    rev: <current>
    hooks:
      - id: stylelint
        additional_dependencies: [stylelint-config-standard-scss]
# .stylelintrc.json: { "extends": ["stylelint-config-standard-scss"] }

# shellcheck — when the first .sh file lands (workflow run: blocks are already
# covered via actionlint):
  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: <current>
    hooks:
      - id: shellcheck
```

(UNVERIFIED: the exact `mirrors-stylelint` hook id and current rev — confirm against
<https://github.com/pre-commit/mirrors-stylelint> at adoption time. The shellcheck hook id is
verified from the repo's `.pre-commit-hooks.yaml`.)

---

## Do not adopt (with reasons — do not re-litigate)

**New rejections from this research:**

| Tool/Rule | Reason | Where to record |
| --- | --- | --- |
| vulture | Inversion-of-control framework: hooks bound by dotted-path string, whitelisted endpoints and DocType controller methods all look dead at 60% confidence; the whitelist file becomes a second registry duplicating `hooks.py`. Only `--min-confidence 100` is viable and its delta over ruff F/PIE is tiny. | **ADR** (category-closing: "dead-code detection") — candidates will re-propose it. Suggest ADR 0005 covering vulture + radon/xenon + the docstring-correctness choice. |
| radon / xenon | radon unmaintained (2023-03); MI is a length-dominated composite (file size is convention, ADR 0004); C901 with tunable `max-complexity` is the zero-new-tool gate already in place. | Same ADR (category-closing: "complexity metrics"). |
| darglint, darglint2 | Archived (2021) / stale fork (2023). Superseded by pydoclint. | Inline comment in pyproject near the ruff `D` rejection note. |
| ruff SLOT, ARG, TC, FLY, COM, Q, BLE | Per-rule-family reasons in §8 (framework-managed classes; unused hook args; runtime-evaluated annotations; UP032 overlap; formatter-owned; broad-except idiom). | Inline pyproject comment (extends the existing "deliberately not selected" list — snippet in Recommended batch §1). |
| ruff DOC (for now) | Preview-only; 7 of pydoclint's 39 rules. Revisit on stabilization, then *replace* pydoclint (one tool per category). | Inline pyproject comment. |
| PR size as CI blocker | Google eng-practices assigns size judgment to reviewers; generated files make line-count gates unsound. | Contributor guide, next to the size convention. |

**Deferrals (evaluate-later, with trigger conditions — not rejections):** ty (trigger: stable
1.0 or frappe core adoption); deptry (trigger: first real third-party runtime dependency in a
derived app); import-linter (trigger: app grows internal layers worth contracting);
stylelint (trigger: first `.scss`); shellcheck standalone (trigger: first `.sh`); vulture at
`--min-confidence 100` only if dead code becomes a observed review problem. Deferrals need no
ADR; a line in CONTEXT.md or the trigger comment in `.pre-commit-config.yaml` suffices.

**Amendment guidance:** the pydoclint adoption changes the *meaning* of the existing `D`
rejection ("undocumented-hook idiom") — the rejection was of *coverage*, not of *correctness*.
Worth one sentence wherever `D` is explained (pyproject comment), or fold into the proposed
ADR 0005. Existing ADRs 0001–0004 need no amendments; nothing here touches them.

---

## Things I could not verify

- Exact current version pins for the deferred pre-commit hooks (`mirrors-stylelint` rev, and
  whether its hook id is still `stylelint`) — marked UNVERIFIED inline; resolve at adoption.
- djLint's behavior on Frappe-specific jinja extensions (e.g. `{% include %}` paths resolved
  against frappe's template search path, web-page context globals): djLint is a static
  template linter and should not need resolution, but real-template runs in a derived app are
  the true test. `custom_blocks` exists for unrecognized block tags.
- Whether ty's stable release will actually land in 2026 (single secondary source,
  infoworld.com, citing the beta announcement; Astral's own blog says only "beta").
- Whether selecting ruff `B` intends to keep preview B901/B903 permanently off (they are
  preview-gated regardless of family selection — status quo confirmed from the rules index).
