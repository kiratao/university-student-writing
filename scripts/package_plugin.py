#!/usr/bin/env python3
"""Build a clean, deterministic skills-only plugin archive."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "plugin.json"
COMPATIBILITY_MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
SKILL_ROOT = ROOT / "skills" / "university-student-writing"
ROOT_FILES = ("plugin.json", "README.md", "LICENSE")
ROOT_TREES = (".codex-plugin", "skills/university-student-writing")
DOC_FILES = ("docs/PRIVACY.md", "docs/TERMS.md", "docs/MARKETPLACE_LISTING.zh-CN.md")
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", "tests"}
EXCLUDED_SUFFIXES = {
    ".aux", ".bbl", ".bcf", ".blg", ".fdb_latexmk", ".fls", ".log",
    ".out", ".pyc", ".run.xml", ".synctex.gz", ".toc", ".xdv",
}
FORBIDDEN_TEXT = ("[TODO:", "example.com", "\\Users\\", "/Users/", "/home/")
TEXT_SUFFIXES = {
    ".bib", ".cls", ".json", ".md", ".py", ".tex", ".sty", ".yaml", ".yml", ".txt",
}
TEXT_FILENAMES = {"LICENSE"}


def load_manifest() -> dict:
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read plugin.json: {exc}") from exc
    for field in ("name", "version", "description", "license"):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            raise ValueError(f"plugin.json field {field!r} must be a non-empty string")
    if manifest["name"] != SKILL_ROOT.name:
        raise ValueError("Plugin name and skill directory name must match")
    if manifest.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        raise ValueError("plugin.json must declare the Agent Plugins 1.0.0 schema")
    try:
        compatibility = json.loads(COMPATIBILITY_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read compatibility manifest: {exc}") from exc
    for field in ("name", "version", "license"):
        if compatibility.get(field) != manifest.get(field):
            raise ValueError(f"Portable and compatibility manifests disagree on {field!r}")
    return manifest


def should_include(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if path.is_symlink():
        raise ValueError(f"Symlinks are not allowed in the upload archive: {relative}")
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    joined_suffixes = "".join(path.suffixes).lower()
    return not any(joined_suffixes.endswith(suffix) for suffix in EXCLUDED_SUFFIXES)


def iter_files() -> list[Path]:
    files: list[Path] = []
    for raw in (*ROOT_FILES, *DOC_FILES):
        path = ROOT / raw
        should_include(path)
        if not path.is_file():
            raise ValueError(f"Required package file is missing: {raw}")
        files.append(path)
    for raw in ROOT_TREES:
        tree = ROOT / raw
        if not tree.is_dir():
            raise ValueError(f"Required package directory is missing: {raw}")
        files.extend(path for path in tree.rglob("*") if path.is_file() and should_include(path))
    return sorted(set(files), key=lambda path: path.relative_to(ROOT).as_posix())


def scan_text(files: list[Path]) -> None:
    for path in files:
        if path.name not in TEXT_FILENAMES and path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_TEXT:
            if marker in text:
                raise ValueError(f"Forbidden placeholder or local path in {path.relative_to(ROOT)}: {marker}")


def default_output(manifest: dict) -> Path:
    return ROOT / "dist" / f"{manifest['name']}-{manifest['version']}.zip"


def safe_output_path(output: Path, files: list[Path]) -> Path:
    if output.is_symlink():
        raise ValueError(f"Output may not be a symlink: {output}")
    parent = output.parent.resolve()
    resolved = parent / output.name
    source_paths = {path.resolve() for path in files}
    if resolved in source_paths:
        raise ValueError(f"Output may not overwrite a packaged source file: {resolved}")
    if output.suffix.lower() != ".zip":
        raise ValueError("Output must use the .zip extension")
    return resolved


def build_archive(output: Path | None, force: bool) -> int:
    manifest = load_manifest()
    if not (SKILL_ROOT / "SKILL.md").is_file():
        raise ValueError("Skill entrypoint is missing")
    files = iter_files()
    scan_text(files)
    output = safe_output_path(output or default_output(manifest), files)
    if output.exists() and not force:
        raise ValueError(f"Output already exists; use --force to replace it: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{output.stem}-", suffix=".tmp", dir=output.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in files:
                relative = path.relative_to(ROOT).as_posix()
                info = zipfile.ZipInfo(relative, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, path.read_bytes())
        os.replace(temporary, output)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

    print(json.dumps({
        "archive": str(output),
        "plugin": manifest["name"],
        "version": manifest["version"],
        "files": len(files),
    }, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true", help="replace an existing archive")
    args = parser.parse_args()
    try:
        return build_archive(args.output, args.force)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
