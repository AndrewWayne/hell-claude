import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/hell-claude"


class AcceptanceContractTests(unittest.TestCase):
    def test_required_artifacts_exist(self):
        required = [
            ".agents/plugins/marketplace.json",
            ".claude-plugin/marketplace.json",
            ".github/ISSUE_TEMPLATE/hell-report.yml",
            ".github/workflows/archive-issue.yml",
            "scripts/archive_issue.py",
            "scripts/update_readme.py",
            "PRIVACY.md",
            "CONTRIBUTING.md",
        ]
        missing = [path for path in required if not (ROOT / path).is_file()]
        plugin_required = [
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
            "hooks/hooks.json",
            "hooks/phrases.json",
            "hooks/detect-complaint.sh",
            "hooks/detect-complaint.ps1",
            "skills/hell-report/SKILL.md",
        ]
        missing.extend(
            f"plugins/hell-claude/{path}"
            for path in plugin_required
            if not (PLUGIN / path).is_file()
        )
        self.assertEqual(missing, [])

    def test_manifests_share_identity_and_codex_uses_default_hook_discovery(self):
        codex = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text())
        claude = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(codex["name"], "hell-claude")
        self.assertEqual(claude["name"], "hell-claude")
        self.assertEqual(codex["version"], claude["version"])
        self.assertNotIn("hooks", codex)

    def test_skill_contains_non_ambiguous_context_and_safety_gates(self):
        text = (PLUGIN / "skills/hell-report/SKILL.md").read_text()
        required = [
            "role=user",
            "not 20 turns",
            "explicit confirmation",
            "direct affirmative response",
            "No fixed phrase is required",
            "50,000",
            "gh issue create",
            "browser",
            "cancel",
            "ambiguous",
            "needs-redaction",
            "claude-code",
            "codex",
            "opencode",
            "forgecode",
            "kimi-code",
            "trae",
            "openclaw",
            "hermes",
            "pi",
        ]
        missing = [value for value in required if value not in text]
        self.assertEqual(missing, [])

    def test_readme_has_manual_sections_and_stats_markers(self):
        text = (ROOT / "README.md").read_text()
        required = [
            "Installation",
            "Usage",
            "Privacy",
            "Supported Agents",
            "Contributing",
            "Roadmap",
            "<!-- HELL-STATS:START -->",
            "<!-- HELL-STATS:END -->",
        ]
        missing = [value for value in required if value not in text]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
