import ast
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/hell-claude"


class PluginMetadataTests(unittest.TestCase):
    def test_client_tests_use_explicit_utf8_for_text_io(self):
        missing = []
        for filename in (
            "test_plugin_metadata.py",
            "test_hook_contract.py",
            "test_skill_contract.py",
        ):
            path = ROOT / "tests" / filename
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=filename)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if not isinstance(node.func, ast.Attribute):
                    continue
                keywords = {keyword.arg: keyword.value for keyword in node.keywords}
                if node.func.attr in {"read_text", "write_text"}:
                    if "encoding" not in keywords:
                        missing.append(f"{filename}:{node.lineno}")
                if (
                    node.func.attr == "run"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "subprocess"
                    and isinstance(keywords.get("text"), ast.Constant)
                    and keywords["text"].value is True
                    and "encoding" not in keywords
                ):
                    missing.append(f"{filename}:{node.lineno}")
        self.assertEqual(missing, [])

    def read_json(self, relative_path):
        path = PLUGIN / relative_path
        self.assertTrue(path.is_file(), f"missing {relative_path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_manifests_share_identity(self):
        codex = self.read_json(".codex-plugin/plugin.json")
        claude = self.read_json(".claude-plugin/plugin.json")
        self.assertEqual(codex["name"], "hell-claude")
        self.assertEqual(claude["name"], "hell-claude")
        self.assertEqual(codex["version"], claude["version"])
        self.assertEqual(codex["version"], "0.1.1")
        self.assertRegex(codex["version"], r"^\d+\.\d+\.\d+$")
        skill = (PLUGIN / "skills/hell-report/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Client Version\n0.1.1", skill)

    def test_codex_manifest_uses_supported_fields_and_default_hook_discovery(self):
        manifest = self.read_json(".codex-plugin/plugin.json")
        self.assertNotIn("hooks", manifest)
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(manifest["interface"]["displayName"], "Hell Claude")

    def test_phrase_rules_are_unique(self):
        rules = self.read_json("hooks/phrases.json")
        normalized = [phrase.casefold().strip() for phrase in rules["phrases"]]
        requested = {
            "wtf",
            "silly",
            "stupid",
            "are you crazy",
            "what're you doing",
            "ruin it",
            "go die",
            "他妈",
            "傻逼",
            "煞笔",
            "脑残",
            "去死",
            "操",
        }
        self.assertEqual(rules["version"], 1)
        self.assertEqual(rules["cooldown_seconds"], 300)
        self.assertEqual(len(normalized), len(set(normalized)))
        self.assertNotIn("/hell", normalized)
        self.assertTrue(requested.issubset(set(normalized)))

    def test_hook_config_has_posix_and_windows_commands(self):
        config = self.read_json("hooks/hooks.json")
        for event in ("SessionStart", "UserPromptSubmit"):
            with self.subTest(event=event):
                group = config["hooks"][event][0]
                self.assertNotIn("matcher", group)
                command = group["hooks"][0]
                self.assertIn("detect-complaint.sh", command["command"])
                self.assertIn("detect-complaint.ps1", command["commandWindows"])

    def test_both_marketplaces_publish_the_same_nested_plugin(self):
        codex = json.loads(
            (ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8")
        )
        claude = json.loads(
            (ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8")
        )
        self.assertEqual(codex["name"], "hell-claude")
        self.assertEqual(claude["name"], "hell-claude")
        self.assertEqual(codex["plugins"][0]["name"], "hell-claude")
        self.assertEqual(claude["plugins"][0]["name"], "hell-claude")
        self.assertEqual(
            codex["plugins"][0]["source"]["path"], "./plugins/hell-claude"
        )
        self.assertEqual(
            claude["plugins"][0]["source"], "./plugins/hell-claude"
        )

    def test_client_ci_runs_linux_and_windows_contracts(self):
        path = ROOT / ".github/workflows/client-plugin-tests.yml"
        self.assertTrue(path.is_file(), "missing client plugin CI workflow")
        text = path.read_text(encoding="utf-8")
        self.assertIn("ubuntu-latest", text)
        self.assertIn("windows-latest", text)
        self.assertIn("tests.test_hook_contract", text)


if __name__ == "__main__":
    unittest.main()
