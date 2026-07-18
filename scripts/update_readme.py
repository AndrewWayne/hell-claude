#!/usr/bin/env python3
"""Generate README statistics and per-Agent indexes from archived records."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


START = "<!-- HELL-STATS:START -->"
END = "<!-- HELL-STATS:END -->"
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def load_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("issue-*.yaml")):
        try:
            record = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(record, dict):
                raise ValueError("record is not a mapping")
            if record.get("schema_version") != 1:
                raise ValueError("unsupported schema version")
            if record.get("status") != "archived":
                raise ValueError("record status is not archived")
            for key in ("source_issue", "submitted_at", "agent", "task", "failure"):
                if key not in record:
                    raise ValueError(f"missing {key}")
        except Exception as exc:
            raise ValueError(f"invalid record {path}: {exc}") from exc
        records.append(record)
    return records


def aggregate(records: list[dict[str, Any]]) -> dict[str, Counter]:
    result = {
        "agents": Counter(),
        "models": Counter(),
        "failures": Counter(),
    }
    for record in records:
        result["agents"][record["agent"]["framework"]] += 1
        result["models"][record["agent"].get("model") or "unknown"] += 1
        result["failures"].update(record["failure"]["categories"])
    return result


def escape_cell(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def ranked_rows(counter: Counter) -> list[tuple[str, int]]:
    return sorted(counter.items(), key=lambda item: (-item[1], str(item[0])))


def render_ranking(title: str, counter: Counter) -> str:
    lines = [f"### {title}", "", "| Name | Reports |", "| --- | ---: |"]
    if counter:
        lines.extend(
            f"| {escape_cell(name)} | {count} |"
            for name, count in ranked_rows(counter)
        )
    else:
        lines.append("| No archived reports | 0 |")
    return "\n".join(lines)


def validate_repository(repository: str) -> None:
    if not REPOSITORY.fullmatch(repository):
        raise ValueError("repository must use OWNER/REPO format")


def render_stats(
    records: list[dict[str, Any]], repository: str, generated_at: str
) -> str:
    validate_repository(repository)
    stats = aggregate(records)
    sections = [
        "> These counts describe archived user submissions, not controlled model failure rates.",
        "",
        f"**Archived reports:** {len(records)}",
        "",
        f"**Last generated:** {generated_at}",
        "",
        render_ranking("Agents", stats["agents"]),
        "",
        render_ranking("Models", stats["models"]),
        "",
        render_ranking("Failure categories", stats["failures"]),
        "",
        "### Recent reports",
        "",
        "| Issue | Agent | Model | Failures | Submitted |",
        "| --- | --- | --- | --- | --- |",
    ]
    recent = sorted(
        records,
        key=lambda record: (record["submitted_at"], record["source_issue"]),
        reverse=True,
    )[:5]
    if not recent:
        sections.append("| No archived reports | | | | |")
    for record in recent:
        number = int(record["source_issue"])
        issue = f"[#{number}](https://github.com/{repository}/issues/{number})"
        sections.append(
            "| "
            + " | ".join(
                [
                    issue,
                    escape_cell(record["agent"]["framework"]),
                    escape_cell(record["agent"].get("model") or "unknown"),
                    escape_cell(", ".join(record["failure"]["categories"])),
                    escape_cell(str(record["submitted_at"])[:10]),
                ]
            )
            + " |"
        )
    return "\n".join(sections).rstrip() + "\n"


def replace_generated_region(document: str, generated: str) -> str:
    if document.count(START) != 1 or document.count(END) != 1:
        raise ValueError("README must contain exactly one marker pair")
    start = document.index(START)
    end = document.index(END)
    if start > end:
        raise ValueError("README markers are reversed")
    before = document[: start + len(START)]
    after = document[end:]
    return before + "\n" + generated.rstrip() + "\n" + after


def write_if_changed(path: Path, content: str) -> bool:
    if path.is_file() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def render_agent_index(
    agent_id: str,
    display_name: str,
    records: list[dict[str, Any]],
    repository: str,
) -> str:
    validate_repository(repository)
    selected = [
        record for record in records if record["agent"]["framework"] == agent_id
    ]
    selected.sort(
        key=lambda record: (record["submitted_at"], record["source_issue"]),
        reverse=True,
    )
    lines = [f"# {display_name} Hell Reports", "", f"Archived reports: {len(selected)}", ""]
    if not selected:
        lines.append("No archived reports.")
    else:
        lines.extend(
            [
                "| Issue | Model | Task | Failures | Submitted |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for record in selected:
            number = int(record["source_issue"])
            link = f"[#{number}](https://github.com/{repository}/issues/{number})"
            lines.append(
                "| "
                + " | ".join(
                    [
                        link,
                        escape_cell(record["agent"].get("model") or "unknown"),
                        escape_cell(record["task"]["category"]),
                        escape_cell(", ".join(record["failure"]["categories"])),
                        escape_cell(str(record["submitted_at"])[:10]),
                    ]
                )
                + " |"
            )
    return "\n".join(lines).rstrip() + "\n"


def generate_agent_indexes(
    records: list[dict[str, Any]],
    display_names: dict[str, str],
    target: Path,
    repository: str,
) -> list[str]:
    changed: list[str] = []
    for agent_id in display_names:
        content = render_agent_index(
            agent_id, display_names[agent_id], records, repository
        )
        filename = f"{agent_id}.md"
        if write_if_changed(target / filename, content):
            changed.append(filename)
    return changed


def load_display_names(config_path: Path) -> dict[str, str]:
    document = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return {
        agent_id: entry["display_name"]
        for agent_id, entry in document["agents"].items()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, default=Path("records"))
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    parser.add_argument("--agents-dir", type=Path, default=Path("docs/agents"))
    parser.add_argument("--agents-config", type=Path, default=Path("config/agents.yml"))
    parser.add_argument("--repository", required=True)
    parser.add_argument("--generated-at")
    args = parser.parse_args()

    generated_at = args.generated_at or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")
    records = load_records(args.records)
    generated = render_stats(records, args.repository, generated_at)
    readme = args.readme.read_text(encoding="utf-8")
    write_if_changed(args.readme, replace_generated_region(readme, generated))
    display_names = load_display_names(args.agents_config)
    generate_agent_indexes(records, display_names, args.agents_dir, args.repository)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
