#!/usr/bin/env python3
"""Create a new LaTeX project from the skill's reviewed genre registry."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = SKILL_ROOT / "references" / "genre-registry.json"
ASSET_ROOT = SKILL_ROOT / "assets" / "latex"


def load_registry() -> dict[str, dict]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)


def field(value: str | None, label: str) -> str:
    return latex_escape(value) if value else rf"\missingfield{{{latex_escape(label)}}}"


def default_date(language: str) -> str:
    today = dt.date.today()
    if language == "en":
        months = (
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        )
        return f"{months[today.month - 1]} {today.day}, {today.year}"
    return f"{today.year}年{today.month}月{today.day}日"


def render_body(genre_id: str, family: str, sections: list[str], language: str) -> str:
    blocks: list[str] = []
    body_prompt = "根据真实信息撰写本节" if language == "zh" else "Write this section using verified information"
    career_prompt = "填写与目标相关且可核验的信息" if language == "zh" else "Add relevant, verifiable information"
    for index, section in enumerate(sections):
        heading = latex_escape(section)
        if genre_id == "apa-student-paper-en" and index == 0:
            blocks.append(rf"\missingfield{{{body_prompt}}}")
        elif genre_id in {"apa-student-paper-en", "mla-research-paper-en"}:
            blocks.append(rf"\section*{{{heading}}}" + "\n" + rf"\missingfield{{{body_prompt}}}")
        elif family in {"academic", "report", "organization"}:
            blocks.append(rf"\section{{{heading}}}" + "\n" + rf"\missingfield{{{body_prompt}}}")
        elif family == "career":
            blocks.append(rf"\section*{{{heading}}}" + "\n" + rf"\missingfield{{{career_prompt}}}")
        else:
            blocks.append(
                rf"\noindent\textbf{{{heading}}}\par"
                + "\n"
                + rf"\missingfield{{{body_prompt}}}\par"
            )
    return "\n\n".join(blocks)


def choose_template(genre_id: str, family: str, language: str) -> Path:
    special = {
        "apa-student-paper-en": ASSET_ROOT / "academic" / "apa.tex",
        "mla-research-paper-en": ASSET_ROOT / "academic" / "mla.tex",
    }
    if genre_id in special:
        return special[genre_id]
    localized = ASSET_ROOT / family / f"main-{language}.tex"
    return localized if localized.is_file() else ASSET_ROOT / family / "main.tex"


def prepare_output(path: Path, force: bool) -> None:
    if path.exists():
        if any(path.iterdir()):
            raise ValueError(f"输出目录非空，拒绝覆盖：{path}")
        if not force:
            raise ValueError(f"输出目录已存在；确认使用空目录时加 --force：{path}")
    else:
        path.mkdir(parents=True)


def validate_school_template_path(source: Path, output: Path) -> None:
    if not source.exists():
        raise ValueError(f"学校模板不存在：{source}")
    if source == output or source.is_relative_to(output):
        raise ValueError("学校模板不能位于输出目录中")
    if source.is_dir() and output.is_relative_to(source):
        raise ValueError("输出目录不能位于学校模板目录中，以免递归复制")


def template_fingerprint(source: Path) -> str:
    digest = hashlib.sha256()
    files = [source] if source.is_file() else sorted(path for path in source.rglob("*") if path.is_file())
    for path in files:
        relative = path.name if source.is_file() else path.relative_to(source).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def copy_school_template(source: Path, output: Path) -> dict[str, str]:
    destination = output / "school-template"
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        destination.mkdir()
        shutil.copy2(source, destination / source.name)
    return {"label": source.name, "sha256": template_fingerprint(source)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="列出可用文体")
    parser.add_argument("--genre", help="genre-registry.json 中的文体 ID")
    parser.add_argument("--output", type=Path, help="新建项目目录")
    parser.add_argument("--title")
    parser.add_argument("--author")
    parser.add_argument("--last-name", help="MLA 页眉使用的作者姓氏")
    parser.add_argument("--student-id")
    parser.add_argument("--university")
    parser.add_argument("--college")
    parser.add_argument("--date")
    parser.add_argument("--school-template", type=Path)
    parser.add_argument("--force", action="store_true", help="允许使用已存在的空目录")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    registry = load_registry()

    if args.list:
        for genre_id, spec in sorted(registry.items(), key=lambda item: (item[1]["domain"], item[0])):
            print(f"{genre_id}\t{spec['display_name']}\t{spec['family']}\t{spec['language']}")
        return 0

    if not args.genre or not args.output:
        parser.error("除 --list 外，必须同时提供 --genre 和 --output")
    if args.genre not in registry:
        print(f"未知文体：{args.genre}；请使用 --list 查看可用 ID", file=sys.stderr)
        return 2

    spec = registry[args.genre]
    language = spec["language"]
    output = args.output.resolve()
    school_template = args.school_template.resolve() if args.school_template else None

    try:
        if school_template:
            validate_school_template_path(school_template, output)
        prepare_output(output, args.force)
        template_path = choose_template(args.genre, spec["family"], language)
        source = template_path.read_text(encoding="utf-8")
        replacements = {
            "@@TITLE@@": field(args.title or spec["display_name"], "标题"),
            "@@AUTHOR@@": field(args.author, "姓名" if language == "zh" else "Name"),
            "@@LAST_NAME@@": field(args.last_name, "Last name"),
            "@@STUDENT_ID@@": field(args.student_id, "学号" if language == "zh" else "Student ID"),
            "@@UNIVERSITY@@": field(args.university, "学校" if language == "zh" else "University"),
            "@@COLLEGE@@": field(args.college, "学院或系" if language == "zh" else "Department"),
            "@@DATE@@": latex_escape(args.date or default_date(language)),
            "@@BODY@@": render_body(args.genre, spec["family"], spec["sections"], language),
        }
        for token, value in replacements.items():
            source = source.replace(token, value)
        unresolved = [token for token in replacements if token in source]
        if unresolved:
            raise ValueError(f"模板仍有未替换标记：{', '.join(unresolved)}")

        (output / "main.tex").write_text(source, encoding="utf-8", newline="\n")
        shutil.copy2(ASSET_ROOT / "common" / "studentwrite.sty", output / "studentwrite.sty")
        (output / "figures").mkdir()
        (output / "attachments").mkdir()
        (output / ".gitignore").write_text(
            "*.aux\n*.bbl\n*.bcf\n*.blg\n*.fdb_latexmk\n*.fls\n*.log\n*.out\n*.run.xml\n*.synctex.gz\n*.toc\n",
            encoding="utf-8",
            newline="\n",
        )

        school_metadata = None
        if school_template:
            school_metadata = copy_school_template(school_template, output)

        manifest = {
            "schema_version": 1,
            "genre_id": args.genre,
            "display_name": spec["display_name"],
            "domain": spec["domain"],
            "family": spec["family"],
            "language": language,
            "engine": "xelatex",
            "main": "main.tex",
            "required_sections": spec["sections"],
            "authority": "built-in-baseline",
            "school_template_source_label": school_metadata["label"] if school_metadata else None,
            "school_template_sha256": school_metadata["sha256"] if school_metadata else None,
            "school_template_status": "copied-for-manual-adaptation" if school_metadata else None,
            "requires_manual_template_adaptation": bool(school_metadata),
            "requires_institution_check": True,
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        (output / "document.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps({"created": str(output), "genre": args.genre, "family": spec["family"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
