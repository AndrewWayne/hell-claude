import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.archive_issue import process_event
from scripts.update_readme import (
    generate_agent_indexes,
    generate_history_chart,
    load_display_names,
    load_records,
    render_stats,
    replace_generated_region,
)
from tests.test_archive_issue import body, event


ROOT = Path(__file__).resolve().parents[1]


class EndToEndTests(unittest.TestCase):
    def test_fictional_issue_updates_record_readme_and_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "config", root / "config")
            readme = root / "README.md"
            readme.write_text(
                "# Test\n\n<!-- HELL-STATS:START -->\nold\n<!-- HELL-STATS:END -->\n"
            )

            result = process_event(event(), root, root / "config")
            self.assertEqual(result["status"], "archived")
            records = load_records(root / "records")
            generated = render_stats(
                records, "AndrewWayne/hell-claude", "2026-07-18T12:00:00Z"
            )
            readme.write_text(replace_generated_region(readme.read_text(), generated))
            generate_agent_indexes(
                records,
                load_display_names(root / "config/agents.yml"),
                root / "docs/agents",
                "AndrewWayne/hell-claude",
            )
            generate_history_chart(
                records,
                load_display_names(root / "config/agents.yml"),
                root / "assets/hell-history.svg",
            )

            self.assertTrue((root / "records/2026/issue-42.yaml").is_file())
            self.assertIn("Archived reports:** 1", readme.read_text())
            self.assertIn("[#42]", (root / "docs/agents/codex.md").read_text())
            self.assertTrue((root / "assets/hell-history.svg").is_file())

            unsafe = event(
                number=43,
                issue_body=body(**{"Evidence": "token ghp_" + "Z" * 36}),
            )
            unsafe_result = process_event(unsafe, root, root / "config")
            self.assertEqual(unsafe_result["status"], "needs-redaction")
            self.assertFalse((root / "records/2026/issue-43.yaml").exists())


if __name__ == "__main__":
    unittest.main()
