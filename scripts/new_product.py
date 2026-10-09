#!/usr/bin/env python3
"""Create a NeoSuite product or engine repository from this template.

    python scripts/new_product.py neotasks --title NeoTasks --kind product --dest ../neotasks

The template's example product, ``neoexample``, is copied to ``--dest`` with every
identifier renamed: ``neoexample`` -> ``<name>`` (crates, Python modules and packages,
npm package, contracts, file names), ``NeoExample`` -> ``<Title>`` and ``NEOEXAMPLE``
-> ``<NAME>`` (environment variable prefix). ``neosuite.toml``, ``README.md`` and
``CHANGELOG.md`` are written fresh for the new component.

The result builds and passes its tests unchanged; replace the example ``Item``
domain with the real one from there.

``--dest`` may be a new directory or an existing one (for example a freshly
initialised git repository). Existing files are never overwritten, with one
exception handled on purpose: an existing ``LICENSE`` is kept, and package
metadata is set to match it (AGPL-3.0-only or Apache-2.0).
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

TEMPLATE_ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

PLACEHOLDER = "neoexample"
PLACEHOLDER_TITLE = "NeoExample"
PLACEHOLDER_ENV = "NEOEXAMPLE"
TEMPLATE_REPO = "neosuite-template"

NAME_RE = re.compile(r"^neo[a-z][a-z0-9]{1,29}$")
TITLE_RE = re.compile(r"^[A-Z][A-Za-z0-9]{1,39}$")

# Never copied, wherever they appear.
EXCLUDED_DIRS = {
    ".git",
    "target",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    ".venv",
    "venv",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
}
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".so", ".egg-info")

# Written by this script instead of copied.
GENERATED = {"neosuite.toml", "README.md", "CHANGELOG.md", "LICENSE"}

FRONTEND_BLOCK = re.compile(r"^[ \t]*# >>> frontend\n.*?^[ \t]*# <<< frontend\n", re.M | re.S)
BLOCK_MARKER = re.compile(r"^[ \t]*# (>>>|<<<) frontend\n", re.M)

LICENSE_FIELDS = (
    # (relative path, pattern, replacement template)
    ("engine/Cargo.toml", r'^license = "[^"]*"$', 'license = "{spdx}"'),
    ("engine/py/pyproject.toml", r'^license = "[^"]*"$', 'license = "{spdx}"'),
    ("backend/pyproject.toml", r'^license = "[^"]*"$', 'license = "{spdx}"'),
    ("frontend/package.json", r'^  "license": "[^"]*",$', '  "license": "{spdx}",'),
)


@dataclass(frozen=True)
class Options:
    name: str
    title: str
    kind: str
    frontend: bool
    dest: Path
    license_file: Path | None

    @property
    def env(self) -> str:
        return self.name.upper()


def rename(text: str, options: Options) -> str:
    return (
        text.replace(PLACEHOLDER_ENV, options.env)
        .replace(PLACEHOLDER_TITLE, options.title)
        .replace(PLACEHOLDER, options.name)
        .replace(TEMPLATE_REPO, options.name)
    )


def is_excluded(relative: Path) -> bool:
    if any(part in EXCLUDED_DIRS or part.endswith(".egg-info") for part in relative.parts):
        return True
    return relative.name.endswith(EXCLUDED_SUFFIXES)


def template_files(options: Options) -> list[Path]:
    files: list[Path] = []
    for path in sorted(TEMPLATE_ROOT.rglob("*")):
        relative = path.relative_to(TEMPLATE_ROOT)
        if not path.is_file() or path.resolve() == SELF or is_excluded(relative):
            continue
        if str(relative) in GENERATED:
            continue
        if not options.frontend and relative.parts[0] == "frontend":
            continue
        files.append(relative)
    return files


def transform(relative: Path, text: str, options: Options) -> str:
    if relative.as_posix() == ".github/workflows/ci.yml":
        if not options.frontend:
            text = FRONTEND_BLOCK.sub("", text)
        text = BLOCK_MARKER.sub("", text)
    return rename(text, options)


def detect_spdx(license_text: str) -> str:
    head = license_text[:2000]
    if "GNU AFFERO GENERAL PUBLIC LICENSE" in head:
        return "AGPL-3.0-only"
    if "Apache License" in head:
        return "Apache-2.0"
    raise SystemExit("LICENSE is neither AGPL-3.0 nor Apache-2.0; set the SPDX fields by hand")


def neosuite_toml(options: Options) -> str:
    profiles = '["core"]' if options.kind == "engine" else '["full"]'
    packages = '["frontend"]' if options.frontend else "[]"
    n = options.name
    return f"""[component]
name = "{n}"
kind = "{options.kind}"
title = "{options.title}"
profiles = {profiles}

[build]
images = ["backend"]
packages = {packages}

[contracts]
provides_types = ["{n}.Item"]
consumes_types = []
emits = ["{n}.item.created"]
actions = ["{n}.item.transition"]
depends_on = []

[runtime.backend]
ports = [{{ name = "http", container = 8000, expose = "internal" }}]
ingress = {{ host = "{n.removeprefix("neo")}", path = "/" }}
env_required = []
secrets = []
volumes = []
health = {{ live = "/healthz", ready = "/readyz", metrics = "/metrics" }}
resources = {{ min_memory = "128Mi", min_cpu = "0.1" }}

[lifecycle]
migrate = {{ command = ["{n}", "migrate", "apply"], reversible = false }}
backup = {{ command = ["{n}", "backup", "/backup"], restore = ["{n}", "restore", "/backup"], consistency = "online" }}
upgrade = {{ supports_from = "N-2-minors", downgrade = false }}
"""


def readme(options: Options) -> str:
    n, title = options.name, options.title
    frontend_layout = (
        "├── frontend/      @neospacetech/{n}-ui: screens, widgets and NeoMind context\n".format(n=n)
        if options.frontend
        else ""
    )
    frontend_dev = (
        f"""
### Frontend

`frontend/` is a source-only package consumed by the neosuite-app shell. It expects
`neosuite-commons` checked out next to this repository.

```sh
cd frontend
npm ci
npm run typecheck
```
"""
        if options.frontend
        else ""
    )
    return f"""# {title}

{title} is a NeoSuite {options.kind}.

Status: scaffold. The `Item` model is a placeholder domain to replace.

## Layout

```text
├── engine/        Rust workspace: {n}-core (logic) and {n}-py (PyO3 bindings, wheel `{n}_core`)
├── backend/       FastAPI service, package `{n}`
{frontend_layout}├── contracts/     types, events, actions and the OpenAPI document
├── deploy/        Dockerfile.backend and the Compose fragment
└── neosuite.toml  component descriptor
```

## Develop

Requirements: Rust (stable), Python 3.12+{", Node 22" if options.frontend else ""}.

```sh
python -m venv .venv && . .venv/bin/activate
pip install "maturin>=1.9,<2"
(cd engine && cargo test --workspace)
maturin develop -m engine/py/Cargo.toml
pip install -e "backend[dev]"
cd backend && pytest && ruff check . && mypy
uvicorn {n}.app:app --reload
```

Settings are read from `{options.env}_*` environment variables.
{frontend_dev}
## Container

```sh
docker build -f deploy/Dockerfile.backend -t {n}-backend .
docker run --rm -p 8000:8000 {n}-backend
```
"""


CHANGELOG = """# Changelog

Notable changes, grouped by NeoSuite version (Keep a Changelog format).

## [Unreleased]
"""


def check_dest(options: Options, files: list[Path]) -> None:
    dest = options.dest
    if dest.exists() and not dest.is_dir():
        raise SystemExit(f"{dest} exists and is not a directory")
    if dest.resolve() == TEMPLATE_ROOT or TEMPLATE_ROOT in dest.resolve().parents:
        raise SystemExit("--dest must be outside the template")
    targets = [dest / rename(str(f), options) for f in files]
    targets += [dest / name for name in GENERATED if name != "LICENSE"]
    clashes = [str(t) for t in targets if t.exists()]
    if clashes:
        listed = "\n  ".join(clashes[:10])
        raise SystemExit(f"refusing to overwrite existing files:\n  {listed}")


def generate(options: Options) -> None:
    files = template_files(options)
    check_dest(options, files)
    dest = options.dest
    dest.mkdir(parents=True, exist_ok=True)

    for relative in files:
        source = TEMPLATE_ROOT / relative
        target = dest / rename(relative.as_posix(), options)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = source.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            shutil.copy2(source, target)
            continue
        target.write_text(transform(relative, text, options), encoding="utf-8")
        shutil.copymode(source, target)

    (dest / "neosuite.toml").write_text(neosuite_toml(options), encoding="utf-8")
    (dest / "README.md").write_text(readme(options), encoding="utf-8")
    (dest / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")

    license_path = dest / "LICENSE"
    if options.license_file is not None:
        if license_path.exists():
            raise SystemExit(f"{license_path} exists; drop --license-file or remove it")
        shutil.copyfile(options.license_file, license_path)
    elif not license_path.exists():
        shutil.copyfile(TEMPLATE_ROOT / "LICENSE", license_path)

    spdx = detect_spdx(license_path.read_text(encoding="utf-8"))
    for relative, pattern, replacement in LICENSE_FIELDS:
        path = dest / relative
        if path.exists():
            text = path.read_text(encoding="utf-8")
            text = re.sub(pattern, replacement.format(spdx=spdx), text, count=1, flags=re.M)
            path.write_text(text, encoding="utf-8")

    print(f"Created {options.title} ({options.kind}) in {dest} [{spdx}]")
    if options.kind in {"product", "engine"} and spdx != "AGPL-3.0-only":
        print(
            "note: NeoSuite products and engines are AGPL-3.0-only. Pass --license-file "
            "with the AGPL text (or stamp into a repository that already has it).",
            file=sys.stderr,
        )


def parse_args(argv: list[str] | None = None) -> Options:
    parser = argparse.ArgumentParser(
        description="Create a NeoSuite product or engine from the template."
    )
    parser.add_argument("name", help="component name, e.g. neotasks (lowercase, starts with neo)")
    parser.add_argument("--title", help="display name, e.g. NeoTasks (default: from the name)")
    parser.add_argument("--kind", choices=("product", "engine"), default="product")
    parser.add_argument("--no-frontend", action="store_true", help="omit frontend/ (headless)")
    parser.add_argument("--dest", required=True, type=Path, help="target directory")
    parser.add_argument("--license-file", type=Path, help="LICENSE to use (default: keep/copy)")
    args = parser.parse_args(argv)

    if not NAME_RE.fullmatch(args.name):
        parser.error("name must match neo[a-z][a-z0-9]* (2-30 chars after 'neo')")
    if args.name == PLACEHOLDER:
        parser.error(f"{PLACEHOLDER} is the template's own name")
    title = args.title or "Neo" + args.name[3:].capitalize()
    if not TITLE_RE.fullmatch(title):
        parser.error("title must be a single word starting with a capital letter, e.g. NeoTasks")
    if args.license_file is not None and not args.license_file.is_file():
        parser.error(f"{args.license_file} is not a file")

    return Options(
        name=args.name,
        title=title,
        kind=args.kind,
        frontend=not args.no_frontend,
        dest=args.dest,
        license_file=args.license_file,
    )


def main(argv: list[str] | None = None) -> int:
    generate(parse_args(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
