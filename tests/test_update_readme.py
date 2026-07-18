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
build_cumulative_history = getattr(
    update_readme, "build_cumulative_history", missing("build_cumulative_history")
)
generate_history_chart = getattr(
    update_readme, "generate_history_chart", missing("generate_history_chart")
)
generate_agent_indexes = getattr(
    update_readme, "generate_agent_indexes", missing("generate_agent_indexes")
)
load_records = getattr(update_readme, "load_records", missing("load_records"))
render_stats = getattr(update_readme, "render_stats", missing("render_stats"))
render_history_svg = getattr(
    update_readme, "render_history_svg", missing("render_history_svg")
)
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
        self.assertIn(
            "![Cumulative Hell reports by harness](assets/hell-history.svg)",
            rendered,
        )

    def test_cumulative_history_never_decreases(self):
        dates, series = build_cumulative_history(load_records(FIXTURES), AGENTS)
        self.assertEqual(
            dates,
            ["2026-07-15", "2026-07-16", "2026-07-17", "2026-07-18"],
        )
        self.assertEqual(series["codex"], [0, 1, 2, 2])
        self.assertEqual(series["claude-code"], [0, 0, 0, 1])
        self.assertEqual(series["pi"], [0, 0, 0, 0])
        for values in series.values():
            self.assertEqual(values, sorted(values))

    def test_history_svg_is_deterministic_and_names_every_harness(self):
        records = load_records(FIXTURES)
        display_names = {agent: agent.replace("-", " ").title() for agent in AGENTS}
        first = render_history_svg(records, display_names)
        self.assertEqual(first, render_history_svg(records, display_names))
        self.assertIn("<svg", first)
        self.assertIn("Cumulative Hell reports by harness", first)
        self.assertIn('data-agent="codex"', first)
        self.assertIn('data-agent="pi"', first)
        for name in display_names.values():
            self.assertIn(name, first)

    def test_history_chart_write_is_idempotent(self):
        records = load_records(FIXTURES)
        display_names = {agent: agent.replace("-", " ").title() for agent in AGENTS}
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "assets/hell-history.svg"
            self.assertTrue(generate_history_chart(records, display_names, target))
            self.assertTrue(target.is_file())
            self.assertFalse(generate_history_chart(records, display_names, target))

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
