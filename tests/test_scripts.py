from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CREATE = ROOT / "scripts" / "create_document.py"
VALIDATE = ROOT / "scripts" / "validate_document.py"
REGISTRY = ROOT / "references" / "genre-registry.json"


class ScriptTests(unittest.TestCase):
    def run_script(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), *args],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
            env={**os.environ, "PYTHONUTF8": "1"},
        )

    def test_list_includes_core_genres(self) -> None:
        result = self.run_script(CREATE, "--list")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("course-paper-zh", result.stdout)
        self.assertIn("social-practice-report-zh", result.stdout)
        self.assertIn("activity-proposal-zh", result.stdout)
        self.assertIn("resume-en", result.stdout)

    def test_every_registered_genre_generates_and_validates(self) -> None:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            for genre_id in registry:
                output = temp_root / genre_id
                created = self.run_script(CREATE, "--genre", genre_id, "--output", str(output))
                self.assertEqual(created.returncode, 0, f"{genre_id}: {created.stderr}")
                self.assertTrue((output / "main.tex").is_file())
                self.assertTrue((output / "studentwrite.sty").is_file())
                checked = self.run_script(VALIDATE, str(output), "--json")
                self.assertEqual(checked.returncode, 0, f"{genre_id}: {checked.stdout}\n{checked.stderr}")
                result = json.loads(checked.stdout)
                self.assertTrue(result["passed"])
                self.assertTrue(result["warnings"])

    def test_refuses_nonempty_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "project"
            output.mkdir()
            (output / "keep.txt").write_text("user data", encoding="utf-8")
            result = self.run_script(CREATE, "--genre", "course-paper-zh", "--output", str(output), "--force")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((output / "keep.txt").read_text(encoding="utf-8"), "user data")

    def test_school_template_is_copied_and_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            school = temp_root / "school"
            school.mkdir()
            (school / "official.cls").write_text("official", encoding="utf-8")
            output = temp_root / "project"
            result = self.run_script(
                CREATE,
                "--genre",
                "course-paper-zh",
                "--output",
                str(output),
                "--school-template",
                str(school),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "school-template" / "official.cls").is_file())
            manifest = json.loads((output / "document.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["authority"], "built-in-baseline")
            self.assertEqual(manifest["school_template_status"], "copied-for-manual-adaptation")
            self.assertTrue(manifest["requires_manual_template_adaptation"])
            self.assertEqual(manifest["school_template_source_label"], "school")
            self.assertRegex(manifest["school_template_sha256"], r"^[0-9a-f]{64}$")
            self.assertNotIn(str(temp_root), json.dumps(manifest, ensure_ascii=False))

    def test_english_genres_use_english_templates(self) -> None:
        genres = ("imrad-paper-en", "formal-email-en", "resume-en", "personal-statement-en")
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            for genre_id in genres:
                output = temp_root / genre_id
                result = self.run_script(CREATE, "--genre", genre_id, "--output", str(output))
                self.assertEqual(result.returncode, 0, result.stderr)
                source = (output / "main.tex").read_text(encoding="utf-8")
                self.assertIn("[[To fill:", source)
                self.assertNotIn("[[待填写：", source)

    def test_rejects_recursive_school_template_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            school = Path(temp) / "school"
            school.mkdir()
            (school / "main.tex").write_text("official", encoding="utf-8")
            output = school / "generated"
            result = self.run_script(
                CREATE,
                "--genre", "course-paper-zh",
                "--output", str(output),
                "--school-template", str(school),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())

    def test_validator_rejects_manifest_tampering_and_external_image(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            output = temp_root / "project"
            created = self.run_script(CREATE, "--genre", "course-paper-zh", "--output", str(output))
            self.assertEqual(created.returncode, 0, created.stderr)
            manifest_path = output / "document.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["required_sections"] = []
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            outside = temp_root / "outside.png"
            outside.write_bytes(b"not a real image")
            main = output / "main.tex"
            source = main.read_text(encoding="utf-8").replace(
                "\\end{document}", "\\includegraphics{../outside.png}\n\\end{document}"
            )
            main.write_text(source, encoding="utf-8")
            checked = self.run_script(VALIDATE, str(output), "--json")
            self.assertNotEqual(checked.returncode, 0)
            result = json.loads(checked.stdout)
            self.assertTrue(any("required_sections" in item for item in result["errors"]))
            self.assertTrue(any("越出项目目录" in item for item in result["errors"]))

    @unittest.skipUnless(shutil.which("latexmk"), "latexmk is not installed")
    def test_representative_chinese_and_english_projects_compile(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            for genre_id in ("course-paper-zh", "formal-email-en", "mla-research-paper-en"):
                output = temp_root / genre_id
                created = self.run_script(
                    CREATE,
                    "--genre", genre_id,
                    "--output", str(output),
                    "--author", "Test Student",
                    "--last-name", "Student",
                )
                self.assertEqual(created.returncode, 0, created.stderr)
                compiled = subprocess.run(
                    ["latexmk", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                    cwd=output,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(compiled.returncode, 0, f"{genre_id}: {compiled.stdout}\n{compiled.stderr}")
                checked = self.run_script(VALIDATE, str(output), "--json")
                self.assertEqual(checked.returncode, 0, checked.stdout)


if __name__ == "__main__":
    unittest.main()
