# Install in Claude Code

The Claude Code package contains the same Hook and Skill as the Codex package. Installation does not grant GitHub access and does not submit an Issue.

## Requirements

- Current Claude Code with plugin marketplace support on macOS, Linux, or Windows.
- GitHub CLI (`gh`) is recommended. Authenticate it yourself with `gh auth login`; otherwise the Skill uses the browser fallback.

## Install

Run these commands on macOS, Linux, or Windows:

```text
claude plugin marketplace add AndrewWayne/hell-claude
claude plugin install hell-claude@hell-claude
```

Restart Claude Code or run `/reload-plugins`. Open `/hooks` to inspect the Hook before you trust it: plugins can run local commands with your user permissions. The package selects Bash on macOS/Linux and PowerShell on Windows.

## Verify

Start a new session and enter `/hell`. `/hell` immediately starts a local draft but does not authorize submission. After the complete draft appears, the Agent asks whether to submit it now; answer cancel and confirm that no Issue was opened. A direct affirmative response would authorize submission without a fixed phrase. `/plugin` should also list `hell-claude@hell-claude` as installed.

## Update

Refresh the marketplace, then reload plugins:

```text
claude plugin marketplace update hell-claude
/reload-plugins
```

## Uninstall

Remove the plugin and, optionally, its marketplace:

```text
claude plugin uninstall hell-claude@hell-claude
claude plugin marketplace remove hell-claude
```

Removing the plugin stops future Hook execution. Previously submitted public Issues and archived records are unaffected.
