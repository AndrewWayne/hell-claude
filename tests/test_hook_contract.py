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
TRIGGER_TEXT = "Invoke the hell-report skill"


def run_hook(adapter: str, fixture: str, data_dir: str) -> subprocess.CompletedProcess:
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
        input=(FIXTURES / fixture).read_text(),
        text=True,
        capture_output=True,
        env=env,
        check=False,
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
                text = (PLUGIN / "hooks" / name).read_text()
                self.assertEqual(
                    [value for value in forbidden if value.casefold() in text.casefold()],
                    [],
                )

    def test_required_prompts_trigger_and_other_input_fails_open(self):
        for adapter in available_adapters():
            for fixture in ("explicit.json", "negative-en.json", "negative-zh.json"):
                with self.subTest(adapter=adapter, fixture=fixture), tempfile.TemporaryDirectory() as data:
                    result = run_hook(adapter, fixture, data)
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(result.stderr, "")
                    self.assertIn(TRIGGER_TEXT, result.stdout)
            for fixture in ("ordinary.json", "invalid.json"):
                with self.subTest(adapter=adapter, fixture=fixture), tempfile.TemporaryDirectory() as data:
                    result = run_hook(adapter, fixture, data)
                    self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_automatic_trigger_cools_down_but_explicit_trigger_does_not(self):
        for adapter in available_adapters():
            with self.subTest(adapter=adapter), tempfile.TemporaryDirectory() as data:
                first = run_hook(adapter, "negative-en.json", data)
                second = run_hook(adapter, "negative-en.json", data)
                self.assertIn(TRIGGER_TEXT, first.stdout)
                self.assertEqual(second.stdout, "")
            with self.subTest(adapter=adapter), tempfile.TemporaryDirectory() as data:
                first = run_hook(adapter, "explicit.json", data)
                second = run_hook(adapter, "explicit.json", data)
                self.assertIn(TRIGGER_TEXT, first.stdout)
                self.assertIn(TRIGGER_TEXT, second.stdout)

    def test_user_configuration_can_disable_or_extend_automatic_detection(self):
        for adapter in available_adapters():
            with self.subTest(adapter=adapter), tempfile.TemporaryDirectory() as data:
                Path(data, "config.json").write_text(json.dumps({"auto_detect": False}))
                self.assertEqual(run_hook(adapter, "negative-en.json", data).stdout, "")
                self.assertIn(TRIGGER_TEXT, run_hook(adapter, "explicit.json", data).stdout)
            with self.subTest(adapter=adapter), tempfile.TemporaryDirectory() as data:
                Path(data, "config.json").write_text(
                    json.dumps({"additional_phrases": ["Please reconsider"]})
                )
                self.assertIn(TRIGGER_TEXT, run_hook(adapter, "custom.json", data).stdout)


if __name__ == "__main__":
    unittest.main()
