import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/hell-claude"
FIXTURES = ROOT / "tests/fixtures/hook"
HARD_TRIGGER_TEXT = "Invoke the hell-report skill now"
SOFT_TRIGGER_TEXT = "Assess whether your prior behavior contains a major mistake"


def run_hook_input(
    adapter: str, input_text: str, data_dir: str
) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.update(
        CLAUDE_PLUGIN_ROOT=str(PLUGIN),
        CODEX_PLUGIN_ROOT=str(PLUGIN),
        PLUGIN_DATA=data_dir,
        CLAUDE_PLUGIN_DATA=data_dir,
    )
    if adapter == "posix":
        command = ["bash", str(PLUGIN / "hooks/detect-complaint.sh")]
    else:
        executable = shutil.which("pwsh") or shutil.which("powershell")
        if not executable:
            raise unittest.SkipTest("PowerShell is not installed")
        command = [
            executable,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(PLUGIN / "hooks/detect-complaint.ps1"),
        ]
    return subprocess.run(
        command,
        input=input_text,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def run_hook(adapter: str, fixture: str, data_dir: str) -> subprocess.CompletedProcess:
    return run_hook_input(
        adapter,
        (FIXTURES / fixture).read_text(encoding="utf-8"),
        data_dir,
    )


def available_adapters():
    adapters = ["posix"] if os.name != "nt" else []
    if shutil.which("pwsh") or shutil.which("powershell"):
        adapters.append("powershell")
    return adapters


class HookContractTests(unittest.TestCase):
    def test_hook_has_no_network_or_transcript_access(self):
        forbidden = [
            "transcript_path",
            "curl ",
            "wget ",
            "Invoke-WebRequest",
            "Invoke-RestMethod",
            "gh ",
        ]
        for name in ("detect-complaint.sh", "detect-complaint.ps1"):
            with self.subTest(name=name):
                text = (PLUGIN / "hooks" / name).read_text(encoding="utf-8")
                self.assertEqual(
                    [value for value in forbidden if value.casefold() in text.casefold()],
                    [],
                )

    def test_required_prompts_trigger_and_other_input_fails_open(self):
        for adapter in available_adapters():
            with self.subTest(adapter=adapter, fixture="explicit.json"), tempfile.TemporaryDirectory() as data:
                result = run_hook(adapter, "explicit.json", data)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stderr, "")
                self.assertIn(HARD_TRIGGER_TEXT, result.stdout)
                self.assertNotIn(SOFT_TRIGGER_TEXT, result.stdout)
            for fixture in ("negative-en.json", "negative-zh.json"):
                with self.subTest(adapter=adapter, fixture=fixture), tempfile.TemporaryDirectory() as data:
                    result = run_hook(adapter, fixture, data)
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(result.stderr, "")
                    self.assertIn(SOFT_TRIGGER_TEXT, result.stdout)
                    self.assertNotIn(HARD_TRIGGER_TEXT, result.stdout)
            for fixture in ("ordinary.json", "invalid.json"):
                with self.subTest(adapter=adapter, fixture=fixture), tempfile.TemporaryDirectory() as data:
                    result = run_hook(adapter, fixture, data)
                    self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_automatic_trigger_cools_down_but_explicit_trigger_does_not(self):
        for adapter in available_adapters():
            with self.subTest(adapter=adapter), tempfile.TemporaryDirectory() as data:
                first = run_hook(adapter, "negative-en.json", data)
                second = run_hook(adapter, "negative-en.json", data)
                self.assertIn(SOFT_TRIGGER_TEXT, first.stdout)
                self.assertEqual(second.stdout, "")
            with self.subTest(adapter=adapter), tempfile.TemporaryDirectory() as data:
                first = run_hook(adapter, "explicit.json", data)
                second = run_hook(adapter, "explicit.json", data)
                self.assertIn(HARD_TRIGGER_TEXT, first.stdout)
                self.assertIn(HARD_TRIGGER_TEXT, second.stdout)

    def test_user_configuration_can_disable_or_extend_automatic_detection(self):
        for adapter in available_adapters():
            with self.subTest(adapter=adapter), tempfile.TemporaryDirectory() as data:
                Path(data, "config.json").write_text(
                    json.dumps({"auto_detect": False}), encoding="utf-8"
                )
                self.assertEqual(run_hook(adapter, "negative-en.json", data).stdout, "")
                self.assertIn(HARD_TRIGGER_TEXT, run_hook(adapter, "explicit.json", data).stdout)
            with self.subTest(adapter=adapter), tempfile.TemporaryDirectory() as data:
                Path(data, "config.json").write_text(
                    json.dumps({"additional_phrases": ["Please reconsider"]}),
                    encoding="utf-8",
                )
                result = run_hook(adapter, "custom.json", data)
                self.assertIn(SOFT_TRIGGER_TEXT, result.stdout)
                self.assertNotIn(HARD_TRIGGER_TEXT, result.stdout)

    def test_requested_phrases_use_the_soft_trigger(self):
        phrases = [
            "WTF",
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
        ]
        for adapter in available_adapters():
            for index, phrase in enumerate(phrases):
                payload = json.dumps(
                    {"session_id": f"new-{index}", "prompt": f"Agent, {phrase}!"}
                )
                with self.subTest(adapter=adapter, phrase=phrase), tempfile.TemporaryDirectory() as data:
                    result = run_hook_input(adapter, payload, data)
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(result.stderr, "")
                    self.assertIn(SOFT_TRIGGER_TEXT, result.stdout)
                    self.assertNotIn(HARD_TRIGGER_TEXT, result.stdout)

    def test_soft_trigger_encodes_judgment_and_two_authorization_gates(self):
        for adapter in available_adapters():
            with self.subTest(adapter=adapter), tempfile.TemporaryDirectory() as data:
                output = run_hook(adapter, "negative-en.json", data).stdout
                required = [
                    "phrase match alone is not proof",
                    "do not stall it for Hell Claude",
                    "Only an unambiguous yes authorizes local draft generation",
                    "it does not authorize submission",
                    "separate explicit confirmation",
                ]
                self.assertEqual(
                    [value for value in required if value not in output], []
                )


if __name__ == "__main__":
    unittest.main()
