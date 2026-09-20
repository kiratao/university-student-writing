from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SCRIPT = ROOT / "scripts" / "package_plugin.py"


def load_package_module():
    spec = importlib.util.spec_from_file_location("package_plugin", PACKAGE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load package_plugin.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PluginPackageTests(unittest.TestCase):
    def test_manifests_and_skill_identity_match(self) -> None:
        portable = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        compatibility = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        skill_frontmatter = (ROOT / "skills" / portable["name"] / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(portable["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        self.assertEqual(portable["name"], compatibility["name"])
        self.assertEqual(portable["version"], compatibility["version"])
        self.assertEqual(portable["description"], compatibility["description"])
        self.assertEqual(portable["keywords"], compatibility["keywords"])
        interface = portable["extensions"]["com.openai"]["interface"]
        self.assertEqual(interface, compatibility["interface"])
        self.assertEqual(interface["category"], "Education & Research")
        self.assertLessEqual(len(interface["shortDescription"]), 30)
        self.assertIn(f"name: {portable['name']}", skill_frontmatter)

    def test_archive_is_deterministic_and_clean(self) -> None:
        module = load_package_module()
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first.zip"
            second = Path(temp) / "second.zip"
            self.assertEqual(module.build_archive(first, False), 0)
            self.assertEqual(module.build_archive(second, False), 0)
            first_hash = hashlib.sha256(first.read_bytes()).hexdigest()
            second_hash = hashlib.sha256(second.read_bytes()).hexdigest()
            self.assertEqual(first_hash, second_hash)
            with zipfile.ZipFile(first) as archive:
                names = set(archive.namelist())
            self.assertIn("plugin.json", names)
            self.assertIn(".codex-plugin/plugin.json", names)
            self.assertIn("skills/university-student-writing/SKILL.md", names)
            self.assertFalse(any("/.git/" in name or "/tests/" in name for name in names))
            self.assertFalse(any(name.endswith((".log", ".aux", ".pyc")) for name in names))

    def test_output_safety_and_manifest_driven_default_name(self) -> None:
        module = load_package_module()
        manifest = module.load_manifest()
        self.assertEqual(
            module.default_output(manifest).name,
            f"{manifest['name']}-{manifest['version']}.zip",
        )
        with tempfile.TemporaryDirectory() as temp:
            sentinel = Path(temp) / "sentinel.txt"
            sentinel.write_text("keep me", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, r"\.zip extension"):
                module.build_archive(sentinel, True)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep me")
            with self.assertRaisesRegex(ValueError, "packaged source file"):
                module.build_archive(ROOT / "plugin.json", True)


if __name__ == "__main__":
    unittest.main()
