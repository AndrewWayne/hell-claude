# Hell Claude

Hell Claude is a public archive for coding-agent failures that users decide are worth preserving. Its client plugin detects explicit frustration, helps the Agent decide whether a report is warranted, and keeps drafting separate from submission. A GitHub Action validates accepted Issues, archives them as structured YAML, and rebuilds the tables below.

These are user-submitted incidents, not controlled experiments. The statistics are not a benchmark and must not be read as model failure rates.

## Installation

The first release provides direct installation for Codex and Claude Code. The report schema can still describe all nine supported Agent families.

- [Install for Codex](docs/install/codex.md)
- [Install for Claude Code](docs/install/claude-code.md)

Both packages contain a `UserPromptSubmit` Hook and the same `hell-report` Skill. Review and trust the Hook before enabling it: installed plugins can execute local commands with your user permissions.

## Verification

After installation, start a new client session and enter `/hell`. `/hell` immediately starts a local draft; it does not submit anything. The Agent shows the complete title and body, then asks whether to submit it now. A direct affirmative response to that question authorizes submission; no fixed phrase is required.

## Usage

Automatic detection uses an English and Chinese phrase list and a five-minute cooldown. An automatic match is a soft trigger: it asks the Agent whether its preceding behavior contains a major mistake, but the matched phrase alone is not proof. If the Agent thinks the mistake is substantial, it asks for draft authorization while continuing the user's active task without stalling it. An unambiguous yes authorizes a local draft only and does not authorize submission.

`/hell` is the hard trigger. It bypasses cooldown and authorizes immediate local drafting. The Skill looks backward through at most 20 user messages—never 20 full turns—and selects only evidence needed to explain the failure.

The preferred submission path is an already authenticated GitHub CLI session. Run `gh auth login` yourself if needed. When `gh` is unavailable or logged out, the Skill opens a prefilled browser form and leaves the final GitHub Submit click to you.

## Privacy

Nothing is drafted merely because a soft trigger matched, and nothing is submitted because the user authorized a draft. The draft is redacted locally; submission requires a separate explicit confirmation to the Agent's submission question. The server then performs a second, fail-closed scan before writing a record. Read [PRIVACY.md](PRIVACY.md) before sending private or work-related material.

## Supported Agents

The schema accepts `claude-code`, `codex`, `opencode`, `forgecode`, `kimi-code`, `trae`, `openclaw`, `hermes`, and `pi`. Direct plugin installation currently targets Codex and Claude Code; the other names are classification targets, not installable adapters in this release.

## Archive statistics

<!-- HELL-STATS:START -->
> These counts describe archived user submissions, not controlled model failure rates.

**Archived reports:** 2

**Last generated:** 2026-07-18T22:09:37Z

### Agents

| Name | Reports |
| --- | ---: |
| codex | 2 |

### Models

| Name | Reports |
| --- | ---: |
| unknown | 2 |

### Failure categories

| Name | Reports |
| --- | ---: |
| hallucinated-result | 2 |
| instruction-misunderstanding | 2 |
| tool-misuse | 2 |
| false-success-claim | 1 |

### Recent reports

| Issue | Agent | Model | Failures | Submitted |
| --- | --- | --- | --- | --- |
| [#2](https://github.com/AndrewWayne/hell-claude/issues/2) | codex | unknown | hallucinated-result, tool-misuse, instruction-misunderstanding | 2026-07-18 |
| [#1](https://github.com/AndrewWayne/hell-claude/issues/1) | codex | unknown | instruction-misunderstanding, hallucinated-result, tool-misuse, false-success-claim | 2026-07-18 |
<!-- HELL-STATS:END -->

## Contributing

Reports arrive through the [Hell report Issue Form](https://github.com/AndrewWayne/hell-claude/issues/new?template=hell-report.yml). Code and taxonomy changes are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). Never place real credentials, private source, or personal data in a fixture.

## Roadmap

- Improve GitHub presentation with richer, automatically refreshed views.
- Add carefully tested adapters for more Agent clients.
- Expand aliases and categories without changing historical records.
- Evaluate duplicate clustering beyond the MVP's exact-match hint.

## License

Code and documentation are available under the [MIT License](LICENSE). Submitted reports remain public GitHub content supplied by their authors.
