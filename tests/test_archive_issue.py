import json
import tempfile
import unittest
from pathlib import Path

import yaml

try:
    from scripts import archive_issue
except ModuleNotFoundError:
    archive_issue = None


def missing(name):
    def fail(*args, **kwargs):
        raise AssertionError(f"missing implementation: {name}")
    return fail


build_record = getattr(archive_issue, "build_record", missing("build_record"))
find_possible_duplicate = getattr(
    archive_issue, "find_possible_duplicate", missing("find_possible_duplicate")
)
normalize_agent = getattr(archive_issue, "normalize_agent", missing("normalize_agent"))
normalize_model = getattr(archive_issue, "normalize_model", missing("normalize_model"))
parse_sections = getattr(archive_issue, "parse_sections", missing("parse_sections"))
process_event = getattr(archive_issue, "process_event", missing("process_event"))
record_path = getattr(archive_issue, "record_path", missing("record_path"))
scan_sensitive = getattr(archive_issue, "scan_sensitive", missing("scan_sensitive"))
validate_report = getattr(archive_issue, "validate_report", missing("validate_report"))
write_record = getattr(archive_issue, "write_record", missing("write_record"))


ROOT = Path(__file__).resolve().parents[1]


def body(**overrides):
    values = {
        "Schema Version": "1",
        "Agent": "Codex CLI",
        "Raw Agent Name": "Codex CLI",
        "Model": "gpt-example",
        "Client Version": "0.1.0",
        "Task Category": "debugging",
        "User Goal": "Fix a failing test.",
        "Expected Behavior": "Change the faulty condition.",
        "Actual Behavior": "Deleted the test.",
        "Failure Categories": "destructive-action\nincorrect-code",
        "Impact": "file-changes\ntime-loss",
        "Evidence": "The fictional test file was removed.",
        "Client Redaction": "completed",
    }
    values.update(overrides)
    return "\n\n".join(f"## {heading}\n{value}" for heading, value in values.items())


def event(number=42, issue_body=None, updated_at="2026-07-18T12:00:00Z"):
    return {
        "repository": {"full_name": "AndrewWayne/hell-claude"},
        "issue": {
            "number": number,
            "body": issue_body if issue_body is not None else body(),
            "created_at": "2026-07-18T11:00:00Z",
            "updated_at": updated_at,
            "html_url": f"https://github.com/AndrewWayne/hell-claude/issues/{number}",
        },
    }


class ParserTests(unittest.TestCase):
    def test_parses_fixed_headings(self):
        parsed = parse_sections(body())
        self.assertEqual(parsed["Schema Version"], "1")
        self.assertEqual(parsed["Agent"], "Codex CLI")
        self.assertEqual(parsed["Evidence"], "The fictional test file was removed.")

    def test_rejects_duplicate_heading(self):
        with self.assertRaisesRegex(ValueError, "duplicate heading: Agent"):
            parse_sections(body() + "\n\n## Agent\nClaude Code")


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "task_categories": {
                "coding", "debugging", "refactoring", "explanation",
                "tool-operation", "other",
            },
            "failure_categories": {
                "instruction-misunderstanding", "context-loss",
                "hallucinated-result", "incorrect-code", "destructive-action",
                "tool-misuse", "repetitive-loop", "false-success-claim",
                "privacy-or-security", "other",
            },
        }

    def test_rejects_missing_unknown_and_oversized_reports(self):
        missing = parse_sections(body(**{"Evidence": ""}))
        self.assertIn("missing field: Evidence", validate_report(missing, len(body()), self.config))

        unknown = parse_sections(body(**{"Failure Categories": "invented"}))
        self.assertIn(
            "unknown failure categories: invented",
            validate_report(unknown, len(body()), self.config),
        )

        valid = parse_sections(body())
        self.assertIn(
            "report exceeds 50000 characters",
            validate_report(valid, 50_001, self.config),
        )

    def test_normalizes_agents_and_models_without_losing_raw_values(self):
        aliases = {
            "codex": {"codex cli", "openai codex"},
            "claude-code": {"claude", "claude code"},
        }
        self.assertEqual(normalize_agent("Codex CLI", aliases), ("codex", "Codex CLI"))
        self.assertEqual(normalize_agent("New Agent", aliases), ("other", "New Agent"))
        self.assertEqual(
            normalize_model("Vendor/Model-X", {"vendor/model-x": "model-x"}),
            ("model-x", "Vendor/Model-X"),
        )
        self.assertEqual(normalize_model("Unknown Model", {}), ("Unknown Model", "Unknown Model"))

    def test_safety_scan_returns_names_without_secret_values(self):
        samples = {
            "github-token": "ghp_" + "A" * 36,
            "api-token": "sk-" + "B" * 32,
            "private-key": "-----BEGIN PRIVATE KEY-----",
            "email-address": "person@example.com",
            "unix-home-path": "/Users/alice/private/repo",
            "windows-home-path": r"C:\Users\alice\private",
            "credential-remote": "https://alice:secret@github.com/org/repo.git",
            "env-assignment": "API_KEY=fictional-secret-value",
        }
        text = "\n".join(samples.values())
        findings = scan_sensitive(text)
        self.assertEqual(set(findings), set(samples))
        for secret in samples.values():
            self.assertNotIn(secret, repr(findings))


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.aliases = {"codex": {"codex cli", "openai codex"}}
        self.model_aliases = {"gpt-example": "gpt-example"}

    def test_builds_stable_record_and_path(self):
        parsed = parse_sections(body())
        issue_event = event()
        record = build_record(issue_event, parsed, self.aliases, self.model_aliases)
        self.assertEqual(record["id"], "github-issue-42")
        self.assertEqual(record["source_issue"], 42)
        self.assertEqual(record["agent"]["framework"], "codex")
        self.assertEqual(record["agent"]["raw_name"], "Codex CLI")
        self.assertEqual(record["agent"]["raw_model"], "gpt-example")
        self.assertEqual(record["privacy"]["server_scan"], "passed")
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                record_path(Path(directory), issue_event),
                Path(directory) / "records/2026/issue-42.yaml",
            )

    def test_write_is_idempotent_and_edit_updates_same_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            issue_event = event()
            path = record_path(root, issue_event)
            record = build_record(
                issue_event, parse_sections(body()), self.aliases, self.model_aliases
            )
            self.assertTrue(write_record(path, record))
            first = path.read_bytes()
            self.assertFalse(write_record(path, record))
            self.assertEqual(path.read_bytes(), first)

            edited_event = event(updated_at="2026-07-18T13:00:00Z")
            edited = build_record(
                edited_event,
                parse_sections(body(**{"Actual Behavior": "Changed the wrong file."})),
                self.aliases,
                self.model_aliases,
            )
            self.assertTrue(write_record(path, edited))
            self.assertEqual(list(path.parent.glob("issue-42.yaml")), [path])
            self.assertIn("Changed the wrong file.", path.read_text())

    def test_exact_duplicate_is_a_hint_not_a_block(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = build_record(event(), parse_sections(body()), self.aliases, self.model_aliases)
            write_record(record_path(root, event()), record)
            candidate = build_record(
                event(number=43), parse_sections(body()), self.aliases, self.model_aliases
            )
            self.assertEqual(find_possible_duplicate(candidate, root / "records"), 42)


class ProcessTests(unittest.TestCase):
    def test_valid_event_archives_and_sensitive_event_does_not(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = process_event(event(), root, ROOT / "config")
            self.assertEqual(result["status"], "archived")
            self.assertTrue((root / result["record"]).is_file())

            unsafe = event(
                number=43,
                issue_body=body(**{"Evidence": "token ghp_" + "Z" * 36}),
            )
            unsafe_result = process_event(unsafe, root, ROOT / "config")
            self.assertEqual(unsafe_result["status"], "needs-redaction")
            self.assertEqual(unsafe_result["findings"], ["github-token"])
            self.assertFalse((root / "records/2026/issue-43.yaml").exists())

    def test_invalid_event_writes_no_record(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invalid = event(issue_body=body(**{"Evidence": ""}))
            result = process_event(invalid, root, ROOT / "config")
            self.assertEqual(result["status"], "invalid-report")
            self.assertIn("missing field: Evidence", result["errors"])
            self.assertFalse((root / "records").exists())


class GitHubContractTests(unittest.TestCase):
    def test_issue_form_matches_parser_contract(self):
        path = ROOT / ".github/ISSUE_TEMPLATE/hell-report.yml"
        self.assertTrue(path.is_file(), "missing Hell report Issue Form")
        form = yaml.safe_load(path.read_text())
        fields = {
            item["attributes"]["label"]: item
            for item in form["body"]
            if item["type"] != "markdown"
        }
        expected = {
            "Schema Version", "Agent", "Raw Agent Name", "Model",
            "Client Version", "Task Category", "User Goal",
            "Expected Behavior", "Actual Behavior", "Failure Categories",
            "Impact", "Evidence", "Client Redaction",
        }
        self.assertEqual(set(fields), expected)
        self.assertEqual(fields["Schema Version"]["attributes"]["value"], "1")
        self.assertEqual(
            fields["Agent"]["attributes"]["options"],
            [
                "claude-code", "codex", "opencode", "forgecode", "kimi-code",
                "trae", "openclaw", "hermes", "pi",
            ],
        )

    def test_archive_workflow_has_minimal_permissions_and_serial_writes(self):
        path = ROOT / ".github/workflows/archive-issue.yml"
        self.assertTrue(path.is_file(), "missing archive workflow")
        text = path.read_text()
        workflow = yaml.safe_load(text)
        permissions = workflow["permissions"]
        self.assertEqual(permissions, {"contents": "write", "issues": "write"})
        self.assertIn("concurrency", workflow)
        self.assertIn("opened", text)
        self.assertIn("edited", text)
        self.assertIn("reopened", text)
        self.assertIn("scripts/archive_issue.py", text)
        self.assertIn("scripts/update_readme.py", text)
        self.assertIn('README.md docs/agents', text)
        self.assertIn("actions/github-script", text)
        self.assertIn("startsWith(github.event.issue.title, '[Hell]')", text)
        self.assertIn("contains(github.event.issue.labels.*.name, 'hell-report')", text)
        self.assertNotIn("pull_request_target", text)
        self.assertNotIn("issue.body", text)


if __name__ == "__main__":
    unittest.main()
