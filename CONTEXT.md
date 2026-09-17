# Context: Frappe App Boilerplate

A glossary of terms used in this repo. Implementation details live in code and
`docs/adr/`, not here.

## Glossary

**Marketplace-ready**
An app that satisfies the *documented* Frappe Marketplace requirements
(https://docs.frappe.io/cloud/marketplace/app-authoring-guidelines,
https://docs.frappe.io/cloud/marketplace/marketplace-guidelines): a **mandatory**
passing CI, a Settings DocType for global config, version-conditional support for
the current stable Frappe (v16 as of Sept 2026; v15 supported to end-2027),
hook-based extension (no core overrides — the ban covers overriding core *pages*
like `/login`, not just code), a unique app
name, and — supplied by the publisher at submission time, not baked into the
repo — a logo, screenshots, a 40–80 character short description, a Support
URL, and a Privacy Policy URL. It does **not** mean "passes every static
analysis tool we could think of" — that's a separate, stricter bar this repo
also holds itself to, but it isn't what the Marketplace requires.

**Settings DocType**
The single (`issingle: 1`) DocType a Frappe app uses to hold its own global
configuration, per the Marketplace authoring guideline "have a settings
doctype in your app to configure global behaviour of your app's
functionality." In this repo it is `Frappe App Boilerplate Settings`.

**Strict tooling**
This repo's own bar, beyond what Marketplace requires: every category of
static check (formatting, linting, typing, security, secrets, commit
hygiene, docstrings, stylesheets, markdown) has a configured, CI-enforced
tool — see `docs/adr/0001-security-scanning-via-semgrep.md` for how
security scanning specifically is composed.
