from __future__ import annotations

import json
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
            self.assertEqual(manifest["authority"], "school-template")


if __name__ == "__main__":
    unittest.main()
