#!/usr/bin/env python3
"""Rename this Frappe app template to a real app.

Usage (from anywhere inside the repo):

	python3 rename.py <app_name> [--title TITLE] [--publisher NAME]
		[--email EMAIL] [--license SPDX_ID]

Rewrites every name-bearing surface of the template — the Python package and
module directories, modules.txt, pyproject.toml, hooks strings, workflow
files, the pre-commit and markdownlint configs, the Settings and example
DocTypes, README and docs — and renames paths containing the template name.
Only git-tracked files are touched. The template-only verification workflow
(.github/workflows/rename-verification.yml), the upstream drift-tracking
tooling (.github/workflows/upstream-drift.yml, check_upstream_drift.py, the
vendored baseline docs/upstream/boilerplate.py and its .semgrepignore
exclusion) and the template-only README section are removed, since they
serve the template, not the derived app.

The script refuses to run when no "boilerplate" references remain, so an
already-renamed app cannot be corrupted by running it twice.

Documented exclusions (intentionally left containing "boilerplate"):
this script itself and docs/research/ (a historical survey of upstream
frappe/utils/boilerplate.py).

Requires only Python 3 (3.9+) and git.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import subprocess  # nosemgrep: gitlab.bandit.B404 -- CLI script; git subprocesses are its job (audit heuristic)
import sys
import urllib.request
from email.headerregistry import Address
from pathlib import Path
from typing import NoReturn

# bench rejects app names that (after lowercasing and converting spaces and
# dashes to underscores) start with a digit or contain a dot; this script takes
# the already-normalized snake_case name and enforces the same shape.
APP_NAME_PATTERN = re.compile(r"[a-z][a-z0-9_]*")
# Same pattern frappe/utils/boilerplate.py enforces for the app title.
APP_TITLE_PATTERN = re.compile(r"^(?![\W])[^\d_\s][\w -]+$", flags=re.UNICODE)

CURRENT_APP_NAME = "frappe_app_boilerplate"
CURRENT_TITLE = "Frappe App Boilerplate"
CURRENT_PUBLISHER = "Gurudatt Kulkarni"
CURRENT_EMAIL = "connect@gurudatt.in"
CURRENT_LICENSE = "agpl-3.0"

TEMPLATE_ONLY_BEGIN = "<!-- TEMPLATE-ONLY:BEGIN -->"
TEMPLATE_ONLY_END = "<!-- TEMPLATE-ONLY:END -->"

VERIFICATION_WORKFLOW = ".github/workflows/rename-verification.yml"

# Template-only machinery removed from the derived app: the verification
# workflow and the upstream drift-tracking tooling (workflow, check script,
# vendored baseline, and the baseline's semgrep exclusion). Derived apps
# intentionally diverge from the bench new-app template, so drift against it
# would be pure noise for them.
TEMPLATE_ONLY_PATHS = (
	VERIFICATION_WORKFLOW,
	".github/workflows/upstream-drift.yml",
	"check_upstream_drift.py",
	"docs/upstream/boilerplate.py",
	".semgrepignore",
)

# Paths that intentionally keep "boilerplate" references after a rename: this
# script (it must know the strings it replaces) and the historical research
# notes about upstream's boilerplate generator.
EXCLUDED_FILES = {"rename.py"}
EXCLUDED_DIRS = {"docs/research"}


def fail(message: str) -> NoReturn:
	print(f"error: {message}", file=sys.stderr)
	sys.exit(1)


def scrub(text: str) -> str:
	"""Match frappe.scrub: lowercase, spaces and dashes to underscores."""
	return text.lower().replace(" ", "_").replace("-", "_")


def pascal_case(title: str) -> str:
	"""Turn an app title into the PascalCase prefix used for Python classes."""
	return "".join(word[:1].upper() + word[1:] for word in re.split(r"[ _-]+", title))


def validate_app_name(app_name: str) -> None:
	if not APP_NAME_PATTERN.fullmatch(app_name):
		fail(
			f"invalid app name {app_name!r}. App names must be snake_case: lowercase "
			"letters, digits and underscores, starting with a letter and containing "
			"no dots — the same rule `bench new-app` enforces."
		)


def validate_title(title: str) -> None:
	if not APP_TITLE_PATTERN.match(title):
		fail(
			f"invalid app title {title!r}. App titles must start with a letter and "
			"consist only of letters, numbers, spaces and underscores — the same "
			"rule `bench new-app` enforces."
		)


def validate_email(email: str) -> None:
	try:
		Address(addr_spec=email)
	except ValueError:
		fail(f"invalid email address {email!r}.")


def validate_metadata_value(flag: str, value: str) -> None:
	# These values land inside quoted Python strings in hooks.py; quotes and
	# backslashes would corrupt the file, so reject them instead of escaping.
	if '"' in value or "\\" in value:
		fail(f"{flag} must not contain double quotes or backslashes.")


def run_git(args: list[str], error_message: str, cwd: Path | None = None) -> str:
	try:
		out = subprocess.run(
			["git", *args],
			cwd=cwd,
			check=True,
			capture_output=True,
			text=True,
		)
	except OSError:
		fail(error_message)
	except subprocess.CalledProcessError:
		fail(error_message)
	return out.stdout


def repo_root() -> Path:
	out = run_git(
		["rev-parse", "--show-toplevel"],
		"rename.py must be run inside a git repository (git is the only dependency).",
	)
	return Path(out.strip())


def tracked_files(root: Path) -> list[str]:
	out = run_git(["ls-files", "-z"], "could not list git-tracked files.", cwd=root)
	return [path for path in out.split("\0") if path]


def is_excluded(rel_path: str) -> bool:
	# Template-only paths are excluded from rewriting/moving because they are
	# deleted outright further below (docs/upstream/boilerplate.py's filename
	# would otherwise be renamed and leak the vendored baseline into the
	# derived app).
	return (
		rel_path in EXCLUDED_FILES
		or rel_path in TEMPLATE_ONLY_PATHS
		or any(rel_path == d or rel_path.startswith(f"{d}/") for d in EXCLUDED_DIRS)
	)


def ensure_renameable(root: Path, files: list[str]) -> None:
	needle = b"boilerplate"
	for rel_path in files:
		if is_excluded(rel_path):
			continue
		try:
			content = (root / rel_path).read_bytes()
		except OSError:
			continue
		if needle in content.lower():
			return
	fail(
		"no 'boilerplate' references remain — this app has already been renamed. "
		"Refusing to run a second time."
	)


def build_replacements(
	args: argparse.Namespace, scrub_title: str, pascal_title: str
) -> list[tuple[str, str]]:
	app_name: str = args.app_name
	title: str = args.title
	replacements = [
		("frappe_app_boilerplate/frappe_app_boilerplate", f"{app_name}/{scrub_title}"),
		("frappe_app_boilerplate.frappe_app_boilerplate", f"{app_name}.{scrub_title}"),
		("frappe_app_boilerplate_settings", f"{scrub_title}_settings"),
		("frappe_app_boilerplate", app_name),
		("FrappeAppBoilerplate", pascal_title),
		("Frappe App Boilerplate", title),
		("BoilerplateTestSuite", f"{pascal_title}TestSuite"),
		("Boilerplate Example", f"{title} Example"),
		("BoilerplateExample", f"{pascal_title}Example"),
		("boilerplate_example", f"{scrub_title}_example"),
		("Boilerplate", pascal_title),
		("boilerplate", app_name),
	]
	if args.publisher:
		replacements.append((CURRENT_PUBLISHER, args.publisher))
	if args.email:
		replacements.append((CURRENT_EMAIL, args.email))
	if args.license and args.license != CURRENT_LICENSE:
		replacements.append((CURRENT_LICENSE, args.license))
	return replacements


def strip_template_only_section(content: str) -> str:
	pattern = re.compile(
		r"\n*" + re.escape(TEMPLATE_ONLY_BEGIN) + r".*?" + re.escape(TEMPLATE_ONLY_END) + r"\n?",
		flags=re.DOTALL,
	)
	if TEMPLATE_ONLY_BEGIN in content and not pattern.search(content):
		fail(f"README.md contains {TEMPLATE_ONLY_BEGIN!r} without a matching {TEMPLATE_ONLY_END!r}.")
	return pattern.sub("\n", content)


def rewrite_contents(root: Path, files: list[str], replacements: list[tuple[str, str]]) -> int:
	changed = 0
	for rel_path in files:
		if is_excluded(rel_path):
			continue
		path = root / rel_path
		try:
			content = path.read_text(encoding="utf-8")
		except OSError:
			continue
		except UnicodeDecodeError:
			continue
		if rel_path == "README.md":
			content = strip_template_only_section(content)
		for old, new in replacements:
			content = content.replace(old, new)
		try:
			path.write_text(content, encoding="utf-8")
		except OSError as exc:
			fail(f"could not write {rel_path}: {exc}")
		changed += 1
	return changed


def renamed_path(rel_path: str, replacements: list[tuple[str, str]], app_name: str, scrub_title: str) -> str:
	parts = rel_path.split("/")
	new_parts = []
	for index, part in enumerate(parts):
		if part == CURRENT_APP_NAME and index == 0:
			new_parts.append(app_name)
		elif part == CURRENT_APP_NAME and index == 1:
			new_parts.append(scrub_title)
		else:
			new_part = part
			for old, new in replacements:
				new_part = new_part.replace(old, new)
			new_parts.append(new_part)
	return "/".join(new_parts)


def rename_paths(
	root: Path,
	files: list[str],
	replacements: list[tuple[str, str]],
	app_name: str,
	scrub_title: str,
) -> int:
	moves = []
	for rel_path in files:
		if is_excluded(rel_path):
			continue
		new_path = renamed_path(rel_path, replacements, app_name, scrub_title)
		if new_path != rel_path:
			moves.append((rel_path, new_path))
	for old, new in moves:
		target = root / new
		target.parent.mkdir(parents=True, exist_ok=True)
		try:
			subprocess.run(["git", "mv", old, new], cwd=root, check=True, capture_output=True)
		except subprocess.CalledProcessError as exc:
			fail(f"git mv {old} {new} failed: {exc.stderr.decode(errors='replace')}")
	remove_empty_dirs(root)
	return len(moves)


def remove_empty_dirs(root: Path) -> None:
	for dirpath, dirnames, filenames in os.walk(root, topdown=False):
		if ".git" in Path(dirpath).parts:
			continue
		if not dirnames and not filenames:
			with contextlib.suppress(OSError):
				Path(dirpath).rmdir()


def update_license_file(root: Path, license_id: str) -> None:
	url = f"https://api.github.com/licenses/{license_id.lower()}"
	body = None
	try:
		# nosemgrep below: pinned https GitHub API host; the license-id path is validated
		# CLI input, and the fetch is best-effort (bandit audit heuristic).
		with urllib.request.urlopen(url, timeout=15) as response:  # nosemgrep
			body = json.loads(response.read().decode("utf-8"))["body"]
	except OSError:
		pass
	except KeyError:
		pass
	except json.JSONDecodeError:
		pass
	if body is None:
		print(
			f"warning: could not fetch the license text for {license_id!r} from "
			"api.github.com — metadata was updated but license.txt was left "
			"unchanged; replace it yourself.",
			file=sys.stderr,
		)
		return
	(root / "license.txt").write_text(body, encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Rename this Frappe app template to a real app.",
		epilog="Example: python3 rename.py my_awesome_app --title 'My Awesome App' "
		"--publisher 'Your Name' --email you@example.com --license mit",
	)
	parser.add_argument("app_name", help="snake_case app name, as `bench new-app` accepts")
	parser.add_argument("--title", help="human-readable app title (default: derived from app name)")
	parser.add_argument("--publisher", help="app publisher name (hooks.py, pyproject.toml)")
	parser.add_argument("--email", help="app contact email (hooks.py, pyproject.toml)")
	parser.add_argument("--license", help="SPDX license id, e.g. mit, agpl-3.0, gpl-3.0")
	return parser.parse_args(argv)


def main() -> int:
	args = parse_args()
	args.license = args.license.lower() if args.license else None
	validate_app_name(args.app_name)
	args.title = args.title or args.app_name.replace("_", " ").title()
	validate_title(args.title)
	if args.email:
		validate_email(args.email)
	for flag, value in (
		("--publisher", args.publisher),
		("--email", args.email),
		("--license", args.license),
	):
		if value:
			validate_metadata_value(flag, value)

	root = repo_root()
	os.chdir(root)
	files = tracked_files(root)
	ensure_renameable(root, files)

	scrub_title = scrub(args.title)
	pascal_title = pascal_case(args.title)
	replacements = build_replacements(args, scrub_title, pascal_title)

	print(f"Renaming {CURRENT_TITLE!r} ({CURRENT_APP_NAME}) -> {args.title!r} ({args.app_name})")
	changed = rewrite_contents(root, files, replacements)
	moved = rename_paths(root, files, replacements, args.app_name, scrub_title)

	for template_only_path in TEMPLATE_ONLY_PATHS:
		try:
			subprocess.run(
				["git", "rm", "-q", "-f", template_only_path],
				cwd=root,
				check=True,
				capture_output=True,
			)
			print(f"Removed template-only path {template_only_path}")
		except subprocess.CalledProcessError:
			pass

	if args.license and args.license != CURRENT_LICENSE:
		update_license_file(root, args.license)

	print(f"Rewrote {changed} files, renamed {moved} paths.")
	print("Next steps:")
	print("  1. Review the result with `git status` and `git diff`.")
	print(f"  2. Delete the example DocType '{scrub_title}_example/' (marked DELETE ME).")
	print("  3. Update the description in pyproject.toml and hooks.py to describe your app.")
	print("  4. Commit.")
	return 0


if __name__ == "__main__":
	sys.exit(main())
