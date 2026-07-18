import tempfile
import unittest
from pathlib import Path

try:
    from scripts import update_readme
except ImportError:
    update_readme = None


def missing(name):
    def fail(*args, **kwargs):
        raise AssertionError(f"missing implementation: {name}")
    return fail


aggregate = getattr(update_readme, "aggregate", missing("aggregate"))
generate_agent_indexes = getattr(
    update_readme, "generate_agent_indexes", missing("generate_agent_indexes")
)
load_records = getattr(update_readme, "load_records", missing("load_records"))
render_stats = getattr(update_readme, "render_stats", missing("render_stats"))
replace_generated_region = getattr(
    update_readme, "replace_generated_region", missing("replace_generated_region")
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/stats/records"
AGENTS = [
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


class StatsTests(unittest.TestCase):
    def test_load_and_aggregate_records(self):
        records = load_records(FIXTURES)
        stats = aggregate(records)
        self.assertEqual(stats["agents"]["codex"], 2)
        self.assertEqual(stats["agents"]["claude-code"], 1)
        self.assertEqual(stats["models"]["gpt-example"], 2)
        self.assertEqual(stats["failures"]["incorrect-code"], 2)

    def test_render_is_deterministic_sorted_and_escaped(self):
        rendered = render_stats(
            load_records(FIXTURES),
            "AndrewWayne/hell-claude",
            "2026-07-18T12:00:00Z",
        )
        self.assertIn("**Archived reports:** 3", rendered)
        self.assertIn("**Last generated:** 2026-07-18T12:00:00Z", rendered)
        self.assertLess(rendered.index("| codex | 2 |"), rendered.index("| claude-code | 1 |"))
        self.assertIn(r"claude\|example", rendered)
        self.assertIn("[#3](https://github.com/AndrewWayne/hell-claude/issues/3)", rendered)
        self.assertLess(rendered.index("[#3]"), rendered.index("[#2]"))

    def test_replace_changes_only_one_marker_region(self):
        document = "before\n<!-- HELL-STATS:START -->\nold\n<!-- HELL-STATS:END -->\nafter\n"
        result = replace_generated_region(document, "new")
        self.assertEqual(
            result,
            "before\n<!-- HELL-STATS:START -->\nnew\n<!-- HELL-STATS:END -->\nafter\n",
        )
        self.assertEqual(replace_generated_region(result, "new"), result)
        for invalid in ("no markers", "<!-- HELL-STATS:START -->"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                replace_generated_region(invalid, "new")

    def test_generates_all_nine_agent_indexes_idempotently(self):
        records = load_records(FIXTURES)
        display_names = {agent: agent.replace("-", " ").title() for agent in AGENTS}
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            changed = generate_agent_indexes(
                records, display_names, target, "AndrewWayne/hell-claude"
            )
            self.assertEqual(set(changed), {f"{agent}.md" for agent in AGENTS})
            self.assertIn("gpt-example", (target / "codex.md").read_text())
            self.assertIn("No archived reports.", (target / "pi.md").read_text())
            self.assertEqual(
                generate_agent_indexes(
                    records, display_names, target, "AndrewWayne/hell-claude"
                ),
                [],
            )


if __name__ == "__main__":
    unittest.main()
