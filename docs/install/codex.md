# Install in Codex

The Codex package contains a Hook that only examines the submitted prompt and a Skill that drafts the report. Installation does not grant GitHub access and does not submit an Issue.

## Requirements

- Current Codex with plugin marketplace support on macOS, Linux, or Windows.
- GitHub CLI (`gh`) is recommended. Authenticate it yourself with `gh auth login`; otherwise the Skill uses the browser fallback.

## Install

On macOS, Linux, or Windows, add this repository as a marketplace:

```text
codex plugin marketplace add AndrewWayne/hell-claude
```

Restart the ChatGPT desktop app, open the Plugins Directory, choose the Hell Claude marketplace, and install Hell Claude. In the Codex CLI, open `/hooks`, inspect the requested command, and trust it before enabling it. The POSIX adapter runs on macOS/Linux; Windows uses the packaged PowerShell adapter.

## Verify

Start a new Codex session and enter `/hell`. `/hell` immediately starts a local draft but does not authorize submission. After the draft appears, choose cancel and confirm that no Issue was opened. You can also inspect the installed plugin in the Plugins Directory.

## Update

Refresh tracked marketplace snapshots:

```text
codex plugin marketplace upgrade hell-claude
```

Then update or reinstall Hell Claude from the Plugins Directory and restart the app.

## Uninstall

Remove Hell Claude in the Plugins Directory. If you no longer want the catalog either, run:

```text
codex plugin marketplace remove hell-claude
```

Removing the plugin stops future Hook execution. Previously submitted public Issues and archived records are unaffected.
