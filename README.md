# Frappe App Boilerplate

Frappe App Boilerplate

<!-- TEMPLATE-ONLY:BEGIN -->

## Using this template

A rock-solid starter for custom Frappe/ERPNext apps: exact `bench new-app`
layout, Marketplace-ready from day one, with strict tooling enforced from the
first commit.

1. Click **Use this template** on GitHub and clone your new repo.
2. Run the rename script with your app name (snake_case, validated against the
   same rule `bench new-app` enforces):

   ```bash
   python3 rename.py my_awesome_app --title "My Awesome App" \
       --publisher "Your Name" --email you@example.com --license mit
   ```

   Only the app name is required; the other flags default to the current
   metadata. The script rewrites every name-bearing surface — package and
   module directories, `modules.txt`, `pyproject.toml`, hooks strings,
   workflows, pre-commit and markdownlint configs, DocTypes and their tests —
   and deletes the template-only machinery (the rename-verification workflow,
   the upstream drift-tracking tooling, and this README section). It refuses
   to run a second time, so an already-renamed app can't be corrupted by
   accident.
3. Delete the example DocType (`*_example/`, marked DELETE ME AFTER RENAME)
   and commit. Commit messages must follow
   [Conventional Commits](https://www.conventionalcommits.org/) — commitlint
   is enforced on pull requests.
4. Install into a bench (see Installation below) and push. CI runs your tests
   on Frappe v15 and v16 plus a soft-link install smoke leg — green from the
   first push.

### Deliberate omissions

This starter deliberately ships without:

- **A dev environment** (no devcontainer, docker compose, or editor configs).
  Environment creation is the developer's responsibility;
  [frappe_docker](https://github.com/frappe/frappe_docker) is the usual
  starting point.
- **A frontend** (no `frontend/`, Vue, or Frappe UI). Use the official
  [frappe-ui-starter](https://github.com/frappe/frappe-ui-starter) if your
  app needs one.
- **Translations** (no `locale/`, POT files, or i18n workflows) — deliberately
  absent; Frappe's translation machinery bolts on later without any starter
  support. Add it when your app needs it.
- **Release automation**. Derived apps version and release themselves; see
  [hrms's workflows](https://github.com/frappe/hrms/tree/develop/.github/workflows)
  for a reference implementation.
- **ERPNext-coupled structure** (no `required_apps`, `overrides/`, `mixins/`,
  or `regional/`). The shell is dependency-agnostic by design — layer your
  app on erpnext/hrms/any framework module yourself; ERPNext-extending
  patterns are available as commented hook stubs in `hooks.py`.

### Maintaining this starter

- **Dual-version stance** (ADR 0002): one Python floor (3.14), a two-leg CI
  matrix against Frappe `version-15` and `version-16`, with version
  differences absorbed by shims (the app-level test base class) and
  `semantic_version` gates. To drop v15 at EOL, delete `"version-15"` from the
  matrix in `.github/workflows/ci.yml` — that list is the single edit point.
- **Upstream drift**: `.github/workflows/upstream-drift.yml` runs weekly
  (Mondays 05:17 UTC) and on manual dispatch. It diffs the vendored baseline
  (`docs/upstream/boilerplate.py`) against upstream's live
  `frappe/utils/boilerplate.py` and opens — or updates — a `needs-triage`
  issue on drift, closing it automatically once the baseline matches again.
  Single edit points: the cron line (schedule) and the `UPSTREAM_URL` env var
  (upstream source). To resolve drift, re-vendor the baseline and re-sync the
  repo's template surfaces.
- **Releasing the starter itself**: push semver tags (`vX.Y.Z`) on `main`
  manually. There is deliberately no release automation — the starter is a
  template repo, not a package installed from an index.

<!-- TEMPLATE-ONLY:END -->

## Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench --site your_site install-app frappe_app_boilerplate
```

Symlink-based development benches work identically via
`bench get-app --soft-link`; CI proves both modes on pushes to `main` and
every pull request.

## Contributing

This app uses `pre-commit` for code formatting and linting. Please
[install pre-commit](https://pre-commit.com/#installation) and enable it for
this repository:

```bash
cd apps/frappe_app_boilerplate
pre-commit install
```

Pre-commit runs ruff (import sort, lint, format), prettier, eslint, gitleaks
(secrets scanning), and markdownlint-cli2. Commit messages must follow
Conventional Commits (commitlint is enforced on pull requests).

## CI

The following GitHub Actions workflows are configured:

- **CI** (`.github/workflows/ci.yml`, pushes to `main` + PRs): installs the app
  and runs the test suite on Frappe `version-15` and `version-16` (Python
  3.14 / Node 24 on both legs), plus a `bench get-app --soft-link` install
  smoke leg on v16.
- **Linters** (`.github/workflows/linter.yml`, PRs): Frappe semgrep rules +
  `r/python.lang.correctness` + `p/bandit`, basedmypy type checking,
  pip-audit, gitleaks, markdownlint, and commitlint.

## License

agpl-3.0
