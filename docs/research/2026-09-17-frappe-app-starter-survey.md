# Frappe App Starter Survey — what "rock solid" looks like in September 2026

Research date: 2026-09-17. All claims traced to primary sources (frappe/* repos, docs.frappe.io,
frappe.io). Time-sensitive facts carry their verification date.

---

## 1. The official template: what `bench new-app` generates today

Source: `frappe/utils/boilerplate.py` on `frappe/frappe@master`
(https://github.com/frappe/frappe/blob/master/frappe/utils/boilerplate.py), read 2026-09-17.

**Interactive prompts** (`_get_user_inputs`): app title (validated against
`APP_TITLE_PATTERN`), description, publisher, email (validated), license (choice list fetched
live from `https://api.github.com/licenses`, fallback `agpl-3.0/gpl-3.0/mit/custom`),
`create_github_workflow` (bool, **default False**), and branch name (defaults to the branch of
the frappe app in the current bench via `get_app_branch("frappe")`).

**Directory tree created** (`_create_app_boilerplate`):

- `<app>/<app>/<scrubbed_app_title>/` (module dir) — now also gets an **empty `.frappe` marker
  file** inside it (newer addition).
- `templates/` + `templates/pages/` + `templates/includes/`, `www/`, `config/`,
  `public/css`, `public/js`, `patches/` (all with `__init__.py` where applicable), plus
  `public/.gitkeep` (comment: without it `bench build` won't symlink the app's assets).
- `modules.txt` is written by `frappe.deprecation_dumpster.boilerplate_modules_txt` (i.e. the
  old inline template was retired into the "deprecation dumpster" module).
- `__init__.py` contains only `__version__ = "0.0.1"`.

**Files written:**

- `pyproject.toml` (`pyproject_template`): `requires-python = ">=3.14"`, `dynamic = ["version"]`,
  `flit_core >=3.4,<4` build backend, `frappe` **commented out** of dependencies
  (`# "frappe~=16.0.0" # Installed and managed by bench.`), a `[tool.bench.dev-dependencies]`
  section, a `[deploy.dependencies.apt]` section (apt packages installed when hosted on
  Frappe Cloud), and a full ruff config: line-length 110, `target-version = "py314"`, select
  `F,E,W,I,UP,B,RUF`, explicit ignore list, `typing-modules = ["frappe.types.DF"]`, tab
  indentation, double quotes, `docstring-code-format = true`.
- `.pre-commit-config.yaml` (`precommit_template`): `pre-commit-hooks v6.0.0`
  (trailing-whitespace, check-merge-conflict, check-ast, check-json/toml/yaml,
  debug-statements), `ruff-pre-commit v0.14.10` as **three separate hooks** (import sorter
  `--select=I --fix`, linter, formatter), `mirrors-prettier v2.7.1` (js/vue/scss) and
  `mirrors-eslint v8.44.0` (js, `--quiet`) — both with excludes for `public/dist/`,
  `node_modules`, `.*boilerplate.*`, `templates/includes/`, `public/js/lib/`. `ci:
  autoupdate_schedule: weekly`.
- `license.txt` — full license text fetched from the GitHub Licenses API at generation time.
- `.editorconfig` and `.eslintrc` — **copied verbatim from the frappe app itself**
  (`copy_from_frappe`), so these drift with the framework.
- `README.md` (`readme_template`): bench get-app/install instructions + pre-commit section
  (claims tools "ruff, eslint, prettier, pyupgrade" — pyupgrade is **not** actually in the
  generated pre-commit config; minor template bug).
- `.gitignore` (python/node/IDE; includes `.aider*`, `.helix/`), git repo initialized with
  initial commit `feat: Initialize App` (conventional-commit style).

**`hooks.py` template** (`hooks_template`) — commented stubs for every hook, plus these
**active by default**:

- `use_json_request_body = True` (native `application/json` request bodies)
- `export_python_type_annotations = True`
- `require_type_annotated_api_methods = True`

Notable stub hooks in the template: `required_apps`, `add_to_apps_screen` (with
`has_permission` route guard), `app_include_css/js`, `web_include_*`, `website_theme_scss`,
`webform_include_*`, `page_js`, `doctype_js/list_js/tree_js/calendar_js`,
`app_include_icons` (SVG icons in desk), `home_page`, `role_home_page`, `website_generators`,
`importable_doctypes`, `jinja`, `before_install/after_install`,
`before_uninstall/after_uninstall`, `before_app_install/after_app_install` +
uninstall variants, `after_build`, `notification_config`, `permission_query_conditions`,
`has_permission`, `doc_events`, `scheduler_events`, `before_tests`, `extend_doctype_class`
(mixins — distinct from `override_doctype_class`), `override_whitelisted_methods`,
`override_doctype_dashboards`, `auto_cancel_exempted_doctypes`, `ignore_links_on_delete`,
`before_request/after_request`, `before_job/after_job`, `after_file_upload`,
`user_data_fields`, `auth_hooks`, `default_log_clearing_doctypes`,
`ignore_translatable_strings_from`.

**Generated CI** (only if `create_github_workflow` = yes), `_create_github_workflow_files`:

- `.github/workflows/ci.yml` (`github_workflow_template`): services = 2× `redis:alpine`
  (cache 13000, queue 11000) + `mariadb:11.8`; steps = checkout@v6 → **"Find tests"**
  (`grep -rn "def test" > /dev/null`, fails the build if no tests exist) → python 3.14 →
  node 24 → pip + yarn caching → `pip install frappe-bench` →
  `bench init --skip-redis-config-generation --skip-assets` → `bench get-app
  $GITHUB_WORKSPACE` → `bench setup requirements --dev` → `bench new-site` → `install-app`
  → `bench build` → `set-config allow_tests true` → `run-tests --app <app>`. Concurrency
  group with cancel-in-progress.
- `.github/workflows/linter.yml` (`linter_workflow_template`): `pre-commit/action@v3.0.0`,
  then clone `frappe/semgrep-rules` and run
  `semgrep ci --config ./frappe-semgrep-rules/rules --config r/python.lang.correctness`,
  plus a separate `deps-vulnerable-check` job running `pip-audit --desc on .`.

**Also in the same file:** a `PatchCreator` class (used by `bench make-patch`) that interactively
creates `patches/<doctype>/...` files **and appends the dotted path to `patches.txt`**
(template `PATCH_TEMPLATE`, enforces identifier filenames, prevents duplicates).

### Decision points this surfaces

- Reuse the boilerplate output verbatim as the baseline (it already matches this repo's
  ruff/pre-commit/CI almost 1:1), or deliberately deviate (e.g. drop eslint 8, add more
  semgrep configs)?
- Adopt the newer active-by-default hooks (`use_json_request_body`,
  `export_python_type_annotations`, `require_type_annotated_api_methods`) as part of the
  starter's "rock solid" bar?
- Keep the "Find tests" CI gate (forces every generated app to ship at least one test)?
- Track upstream drift: `.editorconfig`/`.eslintrc`/boilerplate templates change with
  frappe — does the starter re-sync periodically, and how (script vs manual)?

---

## 2. Current Frappe version landscape (as of 2026-09-17)

**Current stable: v16.** Latest tags from the GitHub Releases API
(https://api.github.com/repos/frappe/frappe/releases, fetched 2026-09-17):

- `v16.34.0` — published 2026-09-15, target branch `version-16`
- `v15.121.0` — published 2026-09-15, target branch `version-15`

Releases are cut roughly weekly by `frappe-pr-bot` per major-version branch; notes are
LLM-summarized (disclosed in the release body).

**Support/EOL picture** (https://frappe.io/support-versions, fetched 2026-09-17 — official
warranty/support page for ERPNext & Frappe Framework *and* Frappe HR):

| Version | EOL | Branch |
|---|---|---|
| v14 | **31 Jan 2026 — already EOL** | `version-14` |
| v15 | End of 2027 (planned) | `version-15` |
| v16 | End of 2029 (planned) | `version-16` |
| bleeding edge | n/a | `develop` |

v16 stable shipped 2026-01-12 (postponed from 2025-12-06; per the official release-date
thread https://discuss.frappe.io/t/erp-v16-clarifications/158512 — community forum, semi-primary).
Python 3.14 / Node 24 / MariaDB 11.8 is the v16 CI stack (boilerplate ci.yml, hrms ci.yml);
v15-era apps still run Python 3.10 / Node 18 (insights compat-matrix.yml gates on this).

**The app ecosystem is mid-migration**, which is exactly why "version-conditional support"
matters. From the same support page: Frappe Insights stable = v3 (`version-3` branch);
Frappe CRM, Helpdesk, Learning stable branches still target **Frappe v15**, with v16 support
on `develop`. Lending stable targets v15.

**How real apps gate per version:**

- Runtime version check (the pattern the Marketplace docs prescribe):
  `Version(frappe.__version__).major >= N` via `semantic_version`
  (https://docs.frappe.io/cloud/marketplace/app-authoring-guidelines).
- Dependency pinning per branch: `frappe/hrms` `pyproject.toml` has
  `[tool.bench.frappe-dependencies]` with `frappe = ">=17.0.0-dev,<18.0.0"` and same for
  erpnext — i.e. the develop branch pins to the next major; release branches pin to theirs.
  (https://github.com/frappe/hrms/blob/master/pyproject.toml)
- Patches organized by major version: `frappe/hrms` has `hrms/patches/v14_0/`, `v15_0/`,
  `v16_0/`, `post_install/` directories (repo tree).
- CI compatibility matrix: `frappe/insights` `.github/workflows/compat-matrix.yml` runs a
  scheduled (daily cron) matrix of `insights_branch: [main, version-3, develop]` ×
  `frappe_branch: [version-15, version-16]`, switching Python (3.10 vs 3.14) and Node
  (18 vs 24) per Frappe branch, and runs only a smoke test module
  (`insights.tests.test_basic_workflow`) per cell.
- `develop_version = "17.x.x-develop"` marker in `erpnext/hooks.py`.

### Decision points this surfaces

- Which Frappe majors does the starter target: v16 only (current stable, matches CONTEXT.md),
  v15+v16 (what most of the ecosystem still needs), or develop?
- Does the starter encode version support as data (a compat matrix workflow like insights)
  or just as runtime `Version(...)` gates?
- Adopt `[tool.bench.frappe-dependencies]` pinning (and a branch strategy: `develop` tracks
  frappe develop, `version-N` branches track stable)?
- Version-foldered patches (`patches/v16_0/`) as the starter's patch convention?

---

## 3. Marketplace requirements (fetched 2026-09-17)

**`https://docs.frappe.io/cloud/marketplace/marketplace-guidelines`** (page last updated
2026-02-16), requirements verbatim-ish:

- Apps should provide value to users
- Apps should not persuade the user away from Frappe Cloud
- Publisher should provide valid contact information
- Apps should support the **current stable version** of Frappe/ERPNext
- Apps must have a logo, description and screenshots meeting the recommendations
- App Name must be **unique across the Marketplace** (can't reuse even for a non-fork)
- App Title ≤ 255 chars
- Short description: 40–80 chars, single sentence, no app name/title repetition, only
  capitalize proper nouns
- Long description: usage/features; **no installation instructions** (FC handles those);
  screenshots go in the screenshot section
- Logo: ≥ 200×200 px, will be cropped square, avoid text in the logo
- Category selection
- **Support URL** and **Privacy Policy URL** required
- "Please prepare a short demo video of the app" for FC review

**`https://docs.frappe.io/cloud/marketplace/app-authoring-guidelines`** (updated 2026-02-16):

1. Recommend a **settings DocType** to configure global app behaviour.
2. Support the current stable Frappe/ERPNext; version-specific code via
   `Version(frappe_version).major >= 13` (`semantic_version`) — note the example still uses
   v13/v12, i.e. the snippet is stale but the mechanism is current.
3. **Don't override base functionality** (e.g. don't replace `/login`, `/update` pages).
4. Extend via **hooks**.
5. **Passing CI is mandatory for approval** ("it is mandatory to have a passing GitHub
   Actions (or similar) CI"); the page links the workflows of
   `Arus-Info/ERPNext-Australian-Localisation` (`.github/workflows` at a pinned commit) as
   the reference `ci.yml` + `linters.yml`.
6. Suggests running semgrep locally with the `frappe/semgrep-rules` rules +
   `r/python.lang.correctness`.

**vs. this repo's CONTEXT.md:** accurate. Two nuances worth adding: (a) CI passing is
*mandatory*, not just recommended; (b) the "don't override base functionality" rule is a
distinct guideline from "extend via hooks" — CONTEXT.md folds both into "hook-based
extension only", which is fine but the override ban is broader than code (it covers
overriding core *pages*).

### Decision points this surfaces

- Which Marketplace artifacts live in the repo (logo asset, screenshot dir, description
  template) vs. stay publisher-side at submission time?
- Does the starter enforce the "unique app name" constraint anywhere (rename script,
  checklist)?
- Treat the referenced `Arus-Info` workflows or the generated boilerplate workflows as the
  CI reference? (They differ; the boilerplate's is the natural baseline.)

---

## 4. How mature first-party apps are structured

Verified active maintenance: all three below have workflows/tags/branches updated in 2026
(hrms: mariadb 11.8 + python 3.14 CI; insights: compat matrix vs version-15/16; builder:
still shipping, though its CI stack is older).

### frappe/hrms (https://github.com/frappe/hrms)

- **Layout extras over `bench new-app`**: `overrides/` (doctype class overrides),
  `mixins/`, `regional/` (India, UAE), `api/`, `setup.py` (install-time setup, separate
  from `install.py`), `uninstall.py`, `tests/` (shared test utils), `docker/` +
  `docker/init.sh` (dev environment, see §6), `frontend/` + `roster/` (two Vite/Vue SPAs),
  `frappe-ui/` submodule, `desktop_icon/*.json` and `workspace_sidebar/*.json` (v16 desk
  chrome), `locale/*.po` (38 languages — **gettext .po, not translations/*.csv**),
  `public/build.json` (esbuild bundle manifest), `hrms.png` logo at root and in package.
- **hooks.py** (read in full): `required_apps = ["frappe/erpnext"]` (org/app form),
  `add_to_apps_screen` with `has_permission`, `app_home`, `app_logo_url`, bundled
  `app_include_js = ["hrms.bundle.js"]` / `app_include_css = "hrms.bundle.css"`,
  `doctype_js` targeting **erpnext** doctypes, `override_doctype_class` (Employee,
  Timesheet, Payment Entry, Project), large `doc_events` map (incl. tuple-keyed multi-doctype
  entries — erpnext uses that pattern too), `scheduler_events` incl. `hourly_long` /
  `daily_long` keys, `before_tests = "hrms.tests.test_utils.before_tests"`,
  `regional_overrides`, `override_doctype_dashboards`, `ignore_links_on_delete`,
  `company_data_to_be_ignored`, `global_search_doctypes`,
  `ignore_translatable_strings_from = ["frappe", "erpnext"]`,
  `export_python_type_annotations` + `require_type_annotated_api_methods`. **No `fixtures`
  hook.**
- **pyproject.toml**: ruff config extended with isort sections (`frappe` / `erpnext` /
  `hrms` as separate import sections — a nice pattern for multi-app import ordering),
  `[project.urls]`, `[tool.frappe.testing.function_type_validation]`,
  `[tool.bench.frappe-dependencies]` pins.
- **Testing**: per-doctype `test_<doctype>.py` + `test_records.json` in each doctype dir;
  test class chain `HRMSTestSuite` (`hrms/tests/utils.py`) → `ERPNextTestSuite`
  (`erpnext.tests.utils`) → framework `IntegrationTestCase`; `BootStrapTestData` helper;
  shared factories imported across test modules (e.g. `make_employee` from
  `erpnext...test_employee`).
- **CI** (`.github/workflows/ci.yml`): PRs + **daily cron**; 3-way matrix sharding via
  `bench --site test_site run-parallel-tests --app hrms --total-builds ${{ strategy.job-total }}
  --build-number ${{ matrix.container }} --lightmode`; mariadb 11.8 service; python 3.14,
  node 24; compileall + merge-conflict grep gate; install via `.github/helper/install.sh`;
  coverage only on non-PR events, artifacts → codecov wrap-up job (`codecov.yml` at root).
- **Other workflows** (12 files): `linters.yml` (**commitlint** via npx
  `@commitlint/config-conventional` on PR commits + pre-commit + semgrep — **no pip-audit**
  here), `docs_checker.yml`, `generate-pot-file.yml` (weekly cron regenerating the
  translation template), `initiate_release.yml`, `on_release.yml`, `release_notes.yml`,
  `labeller.yml`, `patch.yml`, `run-individual-tests.yml`, `stale.yml`, `build_image.yml`.
  Root files: `commitlint.config.js`, `codecov.yml`, `crowdin.yml`.
- **Pre-commit** (`.pre-commit-config.yaml`): *older* than the boilerplate's —
  pre-commit-hooks v4.0.1 (incl. `no-commit-to-branch --branch develop`), prettier v3.1.0,
  ruff-pre-commit v0.3.7 (linter+format only, no separate isort hook), **no eslint**.
  Evidence that even first-party apps lag the generated template here.

### frappe/insights (https://github.com/frappe/insights)

- Workflows: `server-tests.yml` (against `FRAPPE_BRANCH: develop`, mariadb 10.6, py3.14/node24,
  compileall gate), **`compat-matrix.yml`** (see §2 — the only first-party app found with an
  explicit version-compat matrix), `lint.yml`, `build.yml`, `frontend-build.yml`,
  `generate-pot-file.yml`, `playwright.yml` (browser E2E), `make-release-pr.yml`,
  `release.yml`.
- **Uses the `fixtures` hook** (dict-with-filters form):
  `fixtures = [{"dt": "Insights Data Source v3", "filters": {"name": "Site DB"}}]`
  (`insights/hooks.py`).
- **Testing**: `insights/tests/base.py` defines `InsightsIntegrationTestCase(IntegrationTestCase)`
  with explicit `frappe.db.commit()` policies (`COMMIT_AFTER_CLASS_SETUP` etc., with
  `# nosemgrep` suppressions) because its data sources open their own DB connections — a
  worked example of subclassing the framework base class per app.

### frappe/builder (https://github.com/frappe/builder)

- Ships `docker/` + `scripts/init.sh` dev setup, `frontend/` Vite+Vue app, **Cypress** e2e
  (`frontend/cypress/`, `ui-tests.yml`), `docker-image.yml`, `on_release.yml`,
  `release_notes.yml`.
- hooks.py shows website-layer hooks a starter might stub: `website_route_rules`,
  `page_renderer`, `website_path_resolver`, `get_web_pages_with_dynamic_routes`,
  `get_website_user_home_page`, `scheduler_events` with a **`cron`** key
  (`"*/10 * * * *": [...]`), `add_to_apps_screen`.
- **Cautionary data point**: its `server-tests.yml` is stale (actions/checkout@v3, python
  3.10, node 18, mariadb 10.8) — "first-party" ≠ "current tooling". hrms is the best
  maintained of the three.

**`fixtures` hook usage across the org** (`gh search code "fixtures = [" --owner frappe`):
`lms`, `insights`, `drive`, `press`, `frappe_io`, `lending`, `translator` and others use it;
`erpnext`, `hrms`, `builder` do not.

### Decision points this surfaces

- Which "mature app" features belong in a *generic* starter: `overrides/` + `mixins/` dirs?
  `api/` dir? `setup.py`/`install.py` split? regional pattern? (hrms is ERPNext-coupled —
  most of its hooks only make sense for apps extending another app.)
- Pre-commit: track the boilerplate's newer pins (ruff 3-hook split) or hrms's leaner set?
  Add commitlint (hrms has it, boilerplate doesn't)?
- CI: single-job (boilerplate) vs sharded parallel tests + coverage + daily cron (hrms) vs
  compat matrix (insights)? Which Frappe branch does CI test against — the app branch's
  matching stable, or develop?
- Ship a per-app test base class (`<App>TestSuite(IntegrationTestCase)`) and shared
  factories from day one?
- Ship release-automation workflows (initiate_release / release_notes / on_release,
  generate-pot-file, crowdin) or keep the starter minimal?

---

## 5. Testing infrastructure (current official story)

**Framework code** (frappe/frappe@master):

- `frappe/tests/classes/unit_test_case.py` — `UnitTestCase(unittest.TestCase)`: no DB
  setup/teardown; custom Frappe assertions (`assertQueryEqual`, HTML/SQL normalization),
  context managers for user switching and time freezing; infers `cls.doctype` from the test
  module path.
- `frappe/tests/classes/integration_test_case.py` — `IntegrationTestCase(UnitTestCase)`:
  site init (`TEST_SITE = "test_site"`), primary/secondary DB connection management,
  query-count and Redis-call monitoring context managers, **lazy test-record creation in
  `setUpClass` via `make_test_records(cls.doctype)`** (doctype inferred from module location;
  dependencies auto-discovered through Link fields), commit-then-rollback-per-class
  isolation.
- Both re-exported from `frappe.tests` (`from .classes import *` in
  `frappe/tests/__init__.py`), so the import is `from frappe.tests import IntegrationTestCase`.
- The old home (`frappe/tests/utils.py`, former `FrappeTestCase`) **no longer exists** on
  develop — the module was reorganized into `frappe/tests/classes/` +
  `frappe/testing/` (new runner: `TestConfig`/`TestRunner`/`discover_all_tests` in
  `frappe/testing/`, plus `frappe/parallel_test_runner.py`, `frappe/coverage.py`,
  `frappe/test_runner.py` at package root). Deprecations are being funneled through
  `frappe/deprecation_dumpster.py` (a pattern the boilerplate itself now uses).

**Docs** (`https://docs.frappe.io/framework/user/en/testing`, updated 2026-05-10) **lag the
code**: the page still teaches plain `unittest.TestCase` with `frappe.flags.test_events_created`
guards and doesn't mention `IntegrationTestCase`/`UnitTestCase`. Documented facts that remain
valid: test files must be `test_*.py`; test records auto-built from Link dependencies;
`bench setup requirements --dev` first; `frappe.in_test` global (replacing
`frappe.flags.in_test`, explicitly marked for deprecation); run flags
`--app/--doctype/--module-def/--module/--test/--skip-test-records/--profile/--verbose`;
parallel runs via `run-parallel-tests --build-id/--total-builds` or `--use-orchestrator`
(with the `frappe/test-orchestrator` service, env `CI_BUILD_ID`/`ORCHESTRATOR_URL`).
`allow_tests` site config is required (boilerplate ci.yml sets it; also referenced in the
v16.33.0 release note restricting `/_test` pages to developer mode / allow_tests).

**What real apps do**: subclass `IntegrationTestCase` once per app (hrms:
`HRMSTestSuite(ERPNextTestSuite)`; insights: `InsightsIntegrationTestCase` with commit
policies), keep `test_records.json` beside each doctype, share factory functions from test
modules, and use `before_tests` hooks.py entry for global test bootstrap.

### Decision points this surfaces

- Standardize on `IntegrationTestCase` (imported from `frappe.tests`) as the starter's test
  base, with `UnitTestCase` for DB-free units?
- Ship an app-level `<App>TestSuite` base + `before_tests` stub in the template?
- Ship one example doctype with `test_records.json` + a passing test (also satisfies the
  "Find tests" CI gate)?
- Document `allow_tests` + `bench setup requirements --dev` as contributor prerequisites?

---

## 6. Developer-environment story (no bench in the app repo)

There is no official devcontainer *inside* app repos; the official paths are:

- **frappe/frappe_docker** (https://github.com/frappe/frappe_docker):
  `devcontainer-example/devcontainer.json` + `docker-compose.yml` (VS Code devcontainer:
  `frappe/bench`-based compose stack, forwards 8000/9000/6787, `remoteUser: frappe`,
  workspace `/workspace/development`), `development/installer.py`, `development/vscode-example/`
  (launch/settings/tasks), and docs at `docs/development.md`,
  `docs/bench-console-and-vscode-debugger.md`. Images: `images/bench/Dockerfile`
  (the `frappe/bench` dev image), `images/custom|layered|production/Containerfile` for
  production builds.
- **App-local docker compose**: hrms (`docker/docker-compose.yml` + `docker/init.sh`) and
  builder (`docker/` + `scripts/init.sh`) both ship a 3-service stack (mariadb, redis,
  `frappe/bench:latest`) whose init script runs `bench init`, points hosts at container
  names, get-apps the app, creates a site with `developer_mode 1`, and `bench start`s.
  This is the lightest "clone and code" story observed.
- **Classic local bench** is still the default assumption everywhere (every CI does
  `pip install frappe-bench && bench init ...` on a bare runner).
- **Postgres**: `frappe_docker/overrides/compose.postgres.yaml` exists and the framework
  has `frappe/database/postgres/` (per repo tree), but **every observed CI uses MariaDB** —
  MariaDB is the de-facto standard; Postgres is a secondary option.

### Decision points this surfaces

- Does the starter ship a devcontainer (copy/adapt frappe_docker's example) or an
  app-local `docker/` compose like hrms/builder, or just document "bring your own bench"?
- MariaDB-only in starter CI/dev docs, or document Postgres as experimental?
- Any value in shipping the VS Code debug configs (`development/vscode-example`) into the
  starter?

---

## 7. Packaging & distribution details real apps handle

- **pyproject.toml**: flit_core backend, `dynamic = ["version"]` with `__version__` in
  `<app>/__init__.py` (boilerplate init_template); frappe never a pip dependency (commented
  out on purpose); `[tool.bench.dev-dependencies]`; `[tool.bench.frappe-dependencies]`
  for cross-app pins (hrms); `[deploy.dependencies.apt]` for Frappe Cloud system packages
  (boilerplate template); `[project.urls]` (hrms).
- **Assets/esbuild**: bundle-style includes (`app_include_js = "hrms.bundle.js"`,
  `app_include_css = "erpnext.bundle.css"`) with a `public/build.json` manifest (hrms);
  built by `bench build` (frappe's own esbuild config lives in `frappe/esbuild/`).
  `app_include_icons` / `web_include_icons` for SVG icon sheets (erpnext). The boilerplate
  gitkeep comment confirms `public/` must exist for asset symlinking.
- **Translations — sources disagree / in transition**: the docs page
  (https://docs.frappe.io/framework/user/en/translations, updated 2026-02-17) still
  describes the **CSV-in-`translations/`** workflow (`bench get-untranslated`,
  `bench update-translations`), but the framework repo has a `frappe/gettext/` module +
  `babel_extractors.csv` + `crowdin.yml`, and hrms ships **`locale/*.po`** (38 files) with a
  weekly `generate-pot-file.yml` workflow and `crowdin.yml`; insights likewise has
  `generate-pot-file.yml`. Evidence says **gettext .po in `locale/` is the current (v16)
  direction** and the docs page is stale. Boilerplate generates neither directory.
  Related hooks: `ignore_translatable_strings_from`, `translated_search_doctypes`.
- **Fixtures**: `fixtures = [...]` hook (list of doctype names or `{"dt": ..., "filters":
  ...}` dicts) — used by lms/insights/drive/press/lending; exported via
  `bench export-fixtures`. Not used by erpnext/hrms/builder. (No first-party usage of a
  "sync_customizations" alternative observed; customization export is fixture-based.)
- **patches.txt**: `[pre_model_sync]` / `[post_model_sync]` sections (boilerplate
  `patches_template`); patches must be registered there to run; `bench make-patch`
  (PatchCreator in boilerplate.py) automates file creation + registration. hrms groups patch
  files into versioned subdirs (`patches/v16_0/`, `post_install/`).
- **App identity/desk presence**: `required_apps` (org/app form), `add_to_apps_screen`
  (name/logo/title/route/has_permission[/sequence_id]), `app_logo_url`, `app_home`,
  `desktop_icon/*.json` + `workspace_sidebar/*.json` (hrms — the v16 desk sidebar/icon
  config lives in the app repo as JSON).
- **Release mechanics**: framework releases are semver tags (`v16.34.0`) cut weekly by bot
  per `version-N` branch, with LLM-generated notes and mergify backports (frappe release
  bodies). First-party apps replicate this: hrms `initiate_release.yml` / `on_release.yml` /
  `release_notes.yml`, insights `make-release-pr.yml` / `release.yml`, builder
  `on_release.yml` / `release_notes.yml`. `develop_version` hook marks develop builds
  (erpnext). Semantic versioning per major branch is the de-facto expectation; Marketplace
  submission itself is manual via the FC dashboard (descriptions/logo/URLs/demo video per §3)
  — no repo-side manifest found.
- **Other hooks worth stubbing**: `before_migrate`/`after_migrate` (hrms),
  `setup_wizard_complete` (hrms), `boot_session`/`extend_bootinfo` (erpnext),
  `website_route_rules`, `calendars`, `treeviews`, `email_css`, `sounds`,
  `default_log_clearing_doctypes`, `get_translated_dict`, `has_upload_permission`.

### Decision points this surfaces

- Translations: scaffold `locale/` + a `generate-pot-file` workflow (v16 direction) or wait
  for docs to settle?
- Ship `fixtures` examples, and/or an `export-fixtures` how-to?
- Adopt bundle naming (`<app>.bundle.js` + `public/build.json`) as the asset convention?
- Include release-automation workflows (and which: release PR, notes, image build)?
- Include `desktop_icon/` + `workspace_sidebar/` JSON stubs for v16 desk presence?

---

## 8. Starter/boilerplate precedents

- **There is no official cookiecutter/copier template** for server-side Frappe apps from the
  frappe org. `bench new-app` (§1) *is* the generator, and the Marketplace guidelines treat
  its output as the expected baseline.
- **frappe/frappe-ui-starter** (https://github.com/frappe/frappe-ui-starter): official GitHub
  template repo, but only for the **Vue 3 + Frappe UI frontend** of a custom app — a
  complement to `bench new-app`, not a replacement. (This is the upstream of the `frontend/`
  + `frappe-ui/` pattern seen in hrms/builder/insights.)
- **Community templates** (GitHub search, 2026-09-17 — all small/low-adoption, treat as
  secondary sources):
  - `proceduretech/frappe-cookiecutter` — cookiecutter, last commit 2023-11, **stale**
    (v14/v15-era).
  - `Jehad-Alariqi/frappe_app_template` — "Template of a custom Frappe app", updated
    2026-02; individual author, minimal adoption.
  - `seclution/frappe_app_template` — 2025-06 fork of the same idea.
  - `bhushan-barbuddhe/frappe_github_automation` — self-described "production-ready
    template for enterprise-grade Frappe applications" (found via web search; not evaluated
    in depth).
- The Marketplace docs' de-facto "reference implementation" is a shipping community app:
  `Arus-Info/ERPNext-Australian-Localisation` (linked for its `ci.yml`/`linters.yml`).
- **Gap**: nothing maintained, org-endorsed, or widely adopted sits between "bare
  `bench new-app`" and "fork hrms". A curated starter that tracks the boilerplate's drift
  and adds the mature-app ingredients (§4–§7) is unoccupied space.

### Decision points this surfaces

- Form factor: keep this repo as a GitHub **template repository** (native "Use this
  template"), add a **rename script** (app name is baked into ~every file/hook/CI string),
  or go further with copier/cookiecutter (no ecosystem precedent — would be novel)?
- Scope: stay a *server-side app* starter and defer frontends to frappe-ui-starter, or
  bundle an optional `frontend/` variant?
- How to track upstream boilerplate drift (scheduled diff job vs manual)?

---

## Things I could not verify

- Whether `FrappeTestCase` still exists as a deprecated alias on the v15/v16 release
  branches (verified only that `frappe/tests/utils.py` is gone on `develop`/master and the
  classes now live in `frappe/tests/classes/`).
- The exact Frappe version that introduced `frappe/gettext/` + `locale/*.po` (evidence is
  circumstantial: present on master, hrms/insights ship it, docs still describe CSV).
- Insights' `pyproject.toml` pins and `release.yml` contents (repo-read timeouts); its
  default branch layout differed from zread's index (`insights/tests/base.py` only readable
  via raw API).
- Whether Frappe Cloud Marketplace submission has any repo-side manifest/automation (nothing
  found; appears dashboard-manual).
- Current state of `frappe/wiki` (dropped from the survey; hrms/insights/builder used
  instead).
