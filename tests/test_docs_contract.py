import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class DocumentationContractTests(unittest.TestCase):
    def test_readme_covers_public_mvp_contract(self):
        text = (ROOT / "README.md").read_text()
        required = [
            "# Hell Claude",
            "not a benchmark",
            "Installation",
            "Verification",
            "Usage",
            "Privacy",
            "Supported Agents",
            "Contributing",
            "Roadmap",
            "<!-- HELL-STATS:START -->",
            "<!-- HELL-STATS:END -->",
            "docs/install/codex.md",
            "docs/install/claude-code.md",
        ]
        self.assertEqual([value for value in required if value not in text], [])

    def test_install_guides_cover_supported_clients_and_platforms(self):
        common = ["macOS", "Linux", "Windows", "/hell", "trust", "Update", "Uninstall"]
        guides = {
            "codex.md": ["codex plugin marketplace add", "Plugins Directory"],
            "claude-code.md": [
                "claude plugin marketplace add",
                "claude plugin install hell-claude@hell-claude",
            ],
        }
        for filename, client_terms in guides.items():
            with self.subTest(filename=filename):
                text = (ROOT / "docs/install" / filename).read_text()
                self.assertEqual(
                    [value for value in common + client_terms if value not in text], []
                )

    def test_privacy_and_contribution_policies_are_explicit(self):
        privacy = (ROOT / "PRIVACY.md").read_text()
        for value in (
            "explicit confirmation",
            "what leaves your machine",
            "deletion",
            "Git history",
            "token",
            "20 user messages",
        ):
            self.assertIn(value.casefold(), privacy.casefold())
        contribution = (ROOT / "CONTRIBUTING.md").read_text()
        for value in ("fictional", "MIT", "aliases", "phrases", "categories", "adapters"):
            self.assertIn(value, contribution)

    def test_agent_indexes_exist_for_every_configured_agent(self):
        config = yaml.safe_load((ROOT / "config/agents.yml").read_text())
        missing = [
            agent
            for agent in config["agents"]
            if not (ROOT / "docs/agents" / f"{agent}.md").is_file()
        ]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
