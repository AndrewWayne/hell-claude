import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/hell-claude"


class SkillContractTests(unittest.TestCase):
    def read_skill(self):
        path = PLUGIN / "skills/hell-report/SKILL.md"
        self.assertTrue(path.is_file(), "missing skills/hell-report/SKILL.md")
        return path.read_text()

    def test_skill_has_valid_discovery_metadata(self):
        text = self.read_skill()
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("\nname: hell-report\n", text)
        self.assertIn("\ndescription: Use when", text)

    def test_skill_encodes_collection_privacy_and_confirmation_contract(self):
        text = self.read_skill()
        required = [
            "role=user",
            "not 20 turns",
            "50,000",
            "explicit confirmation",
            "ambiguous",
            "cancel",
            "API key",
            "private key",
            ".env",
            "private remote",
            "full file",
            "gh auth status",
            "gh issue create",
            "browser",
        ]
        self.assertEqual([value for value in required if value not in text], [])

    def test_skill_names_all_agents_and_report_headings(self):
        text = self.read_skill()
        agents = [
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
        headings = [
            "Schema Version",
            "Agent",
            "Raw Agent Name",
            "Model",
            "Client Version",
            "Task Category",
            "User Goal",
            "Expected Behavior",
            "Actual Behavior",
            "Failure Categories",
            "Impact",
            "Evidence",
            "Client Redaction",
        ]
        self.assertEqual([value for value in agents + headings if value not in text], [])

    def test_submission_title_is_routable_by_the_archive_workflow(self):
        text = self.read_skill()
        self.assertIn('--title "[Hell] TITLE"', text)


if __name__ == "__main__":
    unittest.main()
