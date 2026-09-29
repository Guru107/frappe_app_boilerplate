#!/usr/bin/env python3
"""Diff this repo's template baseline against upstream frappe/utils/boilerplate.py.

Fetches the current upstream app generator, compares it section by section
(top-level functions, classes and template-string assignments) against the
vendored baseline in docs/upstream/boilerplate.py, and — when they differ —
writes a markdown drift report naming the changed sections and the repo files
they map to. The drift workflow (.github/workflows/upstream-drift.yml) turns
that report into a needs-triage issue.

Exit code is 0 whether or not drift exists (drift is reported, never an
error) and 1 only when the check itself could not run (fetch or parse
failure), so a broken check never masquerades as "no drift".

Requires only Python 3 (3.9+).
"""

from __future__ import annotations

import argparse
import ast
import sys
import urllib.request
from pathlib import Path
from typing import NoReturn

# The single edit point for the upstream source (also overridable via --url).
UPSTREAM_URL = "https://raw.githubusercontent.com/frappe/frappe/develop/frappe/utils/boilerplate.py"
UPSTREAM_HISTORY_URL = "https://github.com/frappe/frappe/commits/develop/frappe/utils/boilerplate.py"

BASELINE_FILE = "docs/upstream/boilerplate.py"
DEFAULT_REPORT_FILE = "drift-report.md"

# Which repo surface each upstream top-level section feeds. Template sections
# drive a generated file; generator functions drive rename.py (this repo's
# re-implementation of the input/layout decisions). Unlisted sections are
# reported without a mapping so a human reviews them manually.
SECTION_FILE_MAP = {
	"init_template": ["frappe_app_boilerplate/__init__.py"],
	"pyproject_template": ["pyproject.toml"],
	"precommit_template": [".pre-commit-config.yaml"],
	"hooks_template": ["frappe_app_boilerplate/hooks.py"],
	"patches_template": ["frappe_app_boilerplate/patches.txt"],
	"gitignore_template": [".gitignore"],
	"github_workflow_template": [".github/workflows/ci.yml"],
	"linter_workflow_template": [".github/workflows/linter.yml"],
	"readme_template": ["README.md"],
	"readme_ci_section": ["README.md"],
	"PATCH_TEMPLATE": ["frappe_app_boilerplate/patches/ (bench new-patch scaffolding)"],
	"PatchCreator": ["frappe_app_boilerplate/patches/ (bench new-patch scaffolding)"],
	"APP_TITLE_PATTERN": ["rename.py (title validation)"],
	"is_valid_title": ["rename.py (title validation)"],
	"is_valid_email": ["rename.py (email validation)"],
	"get_license_options": ["license.txt", "rename.py (license choices)"],
	"get_license_text": ["license.txt", "rename.py (license fetch)"],
	"make_boilerplate": ["rename.py (generator entry point)"],
	"_get_user_inputs": ["rename.py (prompted metadata)"],
	"_create_app_boilerplate": ["repo layout + rename.py (file set written by bench new-app)"],
	"_create_github_workflow_files": [".github/workflows/ (which workflows bench new-app ships)"],
	"copy_from_frappe": ["files copied out of the frappe repo — review manually"],
}


def fail(message: str) -> NoReturn:
	print(f"error: {message}", file=sys.stderr)
	sys.exit(1)


def fetch_upstream(url: str) -> str:
	request = urllib.request.Request(url, headers={"User-Agent": "frappe-app-boilerplate-drift-check"})
	try:
		with urllib.request.urlopen(request, timeout=30) as response:
			return response.read().decode("utf-8")
	except OSError as exc:
		fail(f"could not fetch {url}: {exc}")


def top_level_sections(source: str, origin: str) -> dict[str, str]:
	"""Map each named top-level definition/assignment to its source segment."""
	try:
		tree = ast.parse(source)
	except SyntaxError as exc:
		fail(f"could not parse {origin}: {exc}")
	sections = {}
	for node in tree.body:
		name = None
		if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
			name = node.name
		elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
			name = node.targets[0].id
		elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
			name = node.target.id
		if name is None:
			continue
		segment = ast.get_source_segment(source, node)
		if segment is not None:
			sections[name] = segment
	return sections


def mapped_files(section: str) -> str:
	files = SECTION_FILE_MAP.get(section)
	if not files:
		return "_(no mapped file — review manually)_"
	return ", ".join(f"`{f}`" if not f.startswith(("(", "files")) else f for f in files)


def section_table(title: str, sections: list[str]) -> str:
	if not sections:
		return ""
	lines = [f"### {title}", "", "| Section | Repo file(s) to re-sync |", "| --- | --- |"]
	for section in sections:
		lines.append(f"| `{section}` | {mapped_files(section)} |")
	lines.append("")
	return "\n".join(lines)


def build_report(url: str, baseline: str, upstream: str) -> str:
	baseline_sections = top_level_sections(baseline, BASELINE_FILE)
	upstream_sections = top_level_sections(upstream, url)

	changed = sorted(
		name
		for name in baseline_sections.keys() & upstream_sections.keys()
		if baseline_sections[name] != upstream_sections[name]
	)
	added = sorted(upstream_sections.keys() - baseline_sections.keys())
	removed = sorted(baseline_sections.keys() - upstream_sections.keys())

	parts = [
		"## Upstream drift detected: `frappe/utils/boilerplate.py`",
		"",
		f"The vendored baseline `{BASELINE_FILE}` no longer matches the current upstream app",
		"generator, so the starter's template-derived files may be stale.",
		"",
		f"**Upstream diff:** {UPSTREAM_HISTORY_URL} — compare the newest revision against the baseline.",
		"",
	]
	parts.append(section_table("Changed sections", changed))
	parts.append(section_table("Added upstream sections (decide whether the starter should adopt them)", added))
	parts.append(section_table("Removed upstream sections (drop their counterparts here)", removed))
	if not (changed or added or removed):
		parts += [
			"No template-section changes detected — the drift is in imports, comments or module",
			"scaffolding. Review the upstream diff linked above directly.",
			"",
		]
	parts += [
		"### Resolving this drift",
		"",
		"1. Review the upstream diff for the sections listed above.",
		"2. Re-sync the mapped repo files, re-applying this repo's intentional hardening on top",
		"   (dual-version CI matrix, expanded ruff config, strict tooling — see `docs/adr/`).",
		"3. Refresh the baseline so it matches upstream again:",
		"",
		f"   `curl -sfL {url} -o {BASELINE_FILE}`",
		"",
		"4. Close this issue — or leave it: the next drift run closes it automatically once the",
		"   baseline matches upstream again.",
		"",
	]
	return "\n".join(parts)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Diff the vendored boilerplate.py baseline against upstream and report drift.",
	)
	parser.add_argument("--url", default=UPSTREAM_URL, help="upstream raw source URL")
	parser.add_argument("--baseline", default=BASELINE_FILE, help="path to the vendored baseline copy")
	parser.add_argument("--report", default=DEFAULT_REPORT_FILE, help="markdown report output path")
	return parser.parse_args(argv)


def main() -> int:
	args = parse_args()
	baseline_path = Path(args.baseline)
	report_path = Path(args.report)

	try:
		baseline = baseline_path.read_text(encoding="utf-8")
	except OSError:
		fail(f"baseline {args.baseline} not found — vendor it with: curl -sfL {args.url} -o {args.baseline}")

	upstream = fetch_upstream(args.url)

	if upstream == baseline:
		report_path.unlink(missing_ok=True)
		print("no drift: baseline matches upstream frappe/utils/boilerplate.py")
		return 0

	report = build_report(args.url, baseline, upstream)
	report_path.write_text(report, encoding="utf-8")
	print(f"drift detected — report written to {args.report}")
	return 0


if __name__ == "__main__":
	sys.exit(main())
