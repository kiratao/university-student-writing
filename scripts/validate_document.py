#!/usr/bin/env python3
"""Validate the observable structure of a generated student LaTeX project."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PLACEHOLDER_RE = re.compile(r"\\missingfield\{([^}]*)\}")
IMAGE_RE = re.compile(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}")
SKILL_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = SKILL_ROOT / "references" / "genre-registry.json"
SOURCE_SUFFIXES = {".tex", ".sty", ".cls", ".bib", ".bbx", ".cbx", ".png", ".jpg", ".jpeg", ".pdf"}


def load_project(project: Path) -> tuple[dict, Path, str]:
    manifest_path = project / "document.json"
    if not manifest_path.is_file():
        raise ValueError("缺少 document.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    main = project / manifest.get("main", "main.tex")
    if not main.is_file():
        raise ValueError(f"缺少主文件：{main.name}")
    return manifest, main, main.read_text(encoding="utf-8")


def validate(project: Path, strict: bool) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        manifest, main, text = load_project(project)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"passed": False, "errors": [str(exc)], "warnings": []}

    for key in ("genre_id", "family", "language", "engine", "required_sections"):
        if key not in manifest:
            errors.append(f"document.json 缺少字段：{key}")

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    genre_id = manifest.get("genre_id")
    registered = registry.get(genre_id)
    if not registered:
        errors.append(f"文体未在注册表登记：{genre_id}")
    else:
        for key in ("family", "language"):
            if manifest.get(key) != registered.get(key):
                errors.append(f"document.json 的 {key} 与注册表不一致")
        if manifest.get("required_sections") != registered.get("sections"):
            errors.append("document.json 的 required_sections 与注册表不一致")

    if "\\begin{document}" not in text or "\\end{document}" not in text:
        errors.append("main.tex 缺少完整 document 环境")
    if text.count("\\begin{") != text.count("\\end{"):
        warnings.append("begin/end 环境数量不一致；请人工检查嵌套环境")
    if "@@" in text:
        errors.append("main.tex 含未替换的模板标记 @@...@@")

    for section in manifest.get("required_sections", []):
        if section not in text:
            errors.append(f"缺少注册表要求的结构：{section}")

    placeholders = PLACEHOLDER_RE.findall(text)
    if placeholders:
        message = f"仍有 {len(placeholders)} 个待填写字段：" + "、".join(placeholders[:8])
        (errors if strict else warnings).append(message)

    for raw_path in IMAGE_RE.findall(text):
        if "\\" in raw_path or "#" in raw_path:
            continue
        image_path = (main.parent / raw_path).resolve()
        candidates = [image_path] if image_path.suffix else [image_path.with_suffix(ext) for ext in (".pdf", ".png", ".jpg", ".jpeg")]
        if any(not candidate.is_relative_to(project) for candidate in candidates):
            errors.append(f"图片路径越出项目目录：{raw_path}")
            continue
        if not any(candidate.is_file() for candidate in candidates):
            errors.append(f"图片不存在：{raw_path}")

    log = main.with_suffix(".log")
    pdf = main.with_suffix(".pdf")
    if log.is_file():
        log_text = log.read_text(encoding="utf-8", errors="replace")
        if "There were undefined references" in log_text or "Citation" in log_text and "undefined" in log_text:
            errors.append("编译日志含未解析引用或引文")
        if "Overfull \\hbox" in log_text:
            warnings.append("编译日志含 Overfull hbox；需要视觉检查")
        if "LaTeX Error:" in log_text or "Emergency stop" in log_text:
            errors.append("编译日志含 LaTeX 致命错误")
    else:
        warnings.append("未发现编译日志；尚不能确认实际编译状态")

    if pdf.is_file():
        dependencies = [
            path for path in project.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and path != pdf
            and path.suffix.lower() in SOURCE_SUFFIXES
        ]
        newest_dependency = max((path.stat().st_mtime for path in dependencies), default=main.stat().st_mtime)
        if pdf.stat().st_mtime < newest_dependency:
            errors.append("PDF 早于项目中的源码或资源，需要重新编译")
        if log.is_file() and log.stat().st_mtime < newest_dependency:
            errors.append("编译日志早于项目中的源码或资源，需要重新编译")
    else:
        warnings.append("未发现 PDF；交付前应实际编译并检查")

    if manifest.get("school_template_source_label") and not (project / "school-template").exists():
        errors.append("记录了学校模板来源，但 school-template/ 不存在")
    if manifest.get("school_template_status") == "copied-for-manual-adaptation":
        warnings.append("学校模板已保留，但 main.tex 仍是内置基线；提交前必须人工适配学校模板")

    return {
        "passed": not errors,
        "project": str(project),
        "genre_id": manifest.get("genre_id"),
        "family": manifest.get("family"),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--strict", action="store_true", help="把待填写字段视为错误")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    result = validate(args.project.resolve(), args.strict)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("PASS" if result["passed"] else "FAIL")
        for message in result["errors"]:
            print(f"ERROR: {message}")
        for message in result["warnings"]:
            print(f"WARN: {message}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
