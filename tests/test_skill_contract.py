import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/hell-claude"


class SkillContractTests(unittest.TestCase):
    def read_skill(self):
        path = PLUGIN / "skills/hell-report/SKILL.md"
        self.assertTrue(path.is_file(), "missing skills/hell-report/SKILL.md")
        return path.read_text(encoding="utf-8")

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
            "direct affirmative response",
            "No fixed phrase is required",
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

    def test_skill_uses_only_the_validated_hook_model(self):
        text = self.read_skill()
        for value in (
            "validated runtime model provided by the Hook",
            "Use `unknown` when the Hook does not provide one",
            "Do not guess",
        ):
            self.assertIn(value, text)

    def test_confirmation_gate_precedes_every_submission_path(self):
        text = self.read_skill()
        confirm = text.index("## Confirm")
        submit = text.index("## Submit")
        self.assertLess(confirm, submit)
        gate = text[confirm:submit]
        for value in (
            "ask whether to submit it now",
            "direct affirmative response",
            "No fixed phrase is required",
            "ambiguous reply",
            "On cancel",
            "perform no network action",
            "show the changed payload and ask again",
            "request to edit the draft",
        ):
            self.assertIn(value, gate)

        self.assertNotIn("Submit this Hell report", gate)

    def test_draft_permission_is_separate_and_does_not_stall_active_work(self):
        text = self.read_skill()
        draft_gate = text.index("## Draft authorization")
        collect = text.index("## Collect")
        submit = text.index("## Submit")
        self.assertLess(draft_gate, collect)
        self.assertLess(collect, submit)
        required = [
            "unambiguous yes",
            "authorizes local draft generation only",
            "does not authorize submission",
            "continue the user's active task",
            "must not stall",
            "complete Issue title and body",
        ]
        self.assertEqual([value for value in required if value not in text], [])


if __name__ == "__main__":
    unittest.main()
