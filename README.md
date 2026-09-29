# Frappe App Boilerplate

Frappe App Boilerplate

<!-- TEMPLATE-ONLY:BEGIN -->

## Using this template

Click **Use this template** on GitHub, clone your new repo, then run the
rename script with your app name (snake_case, validated against the same rule
`bench new-app` enforces):

```bash
python3 rename.py my_awesome_app --title "My Awesome App" \
    --publisher "Your Name" --email you@example.com --license mit
```

Only the app name is required; the other flags default to the current
metadata. The script rewrites every name-bearing surface — package and module
directories, `modules.txt`, `pyproject.toml`, hooks strings, workflows,
pre-commit and markdownlint configs, DocTypes and their tests — and removes
the template-only verification workflow. It refuses to run a second time, so
an already-renamed app can't be corrupted by accident. Afterwards, delete the
example DocType (`*_example/`, marked DELETE ME) and commit.

<!-- TEMPLATE-ONLY:END -->

## Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench install-app frappe_app_boilerplate
```

## Contributing

This app uses `pre-commit` for code formatting and linting. Please
[install pre-commit](https://pre-commit.com/#installation) and enable it for
this repository:

```bash
cd apps/frappe_app_boilerplate
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

## CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules)
  and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.

## License

agpl-3.0
