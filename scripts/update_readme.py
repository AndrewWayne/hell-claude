#!/usr/bin/env python3
"""Generate README statistics and per-Agent indexes from archived records."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape, quoteattr

import yaml


START = "<!-- HELL-STATS:START -->"
END = "<!-- HELL-STATS:END -->"
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
HISTORY_CHART = "assets/hell-history.svg"
CHART_COLORS = (
    "#0969da",
    "#cf222e",
    "#1a7f37",
    "#8250df",
    "#bf8700",
    "#0550ae",
    "#a40e26",
    "#116329",
    "#6639ba",
)


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


def build_cumulative_history(
    records: list[dict[str, Any]], agent_ids: list[str]
) -> tuple[list[str], dict[str, list[int]]]:
    """Return a daily cumulative series with a zero baseline before first report."""
    series = {agent_id: [] for agent_id in agent_ids}
    if not records:
        return [], series

    daily: dict[date, Counter] = {}
    for record in records:
        submitted = date.fromisoformat(str(record["submitted_at"])[:10])
        daily.setdefault(submitted, Counter())[record["agent"]["framework"]] += 1

    event_dates = sorted(daily)
    timeline = [event_dates[0] - timedelta(days=1), *event_dates]
    running = Counter()
    for current in timeline:
        running.update(daily.get(current, Counter()))
        for agent_id in agent_ids:
            series[agent_id].append(running[agent_id])
    return [value.isoformat() for value in timeline], series


def _chart_ticks(maximum: int, segments: int = 4) -> list[int]:
    return sorted({round(maximum * index / segments) for index in range(segments + 1)})


def render_history_svg(
    records: list[dict[str, Any]], display_names: dict[str, str]
) -> str:
    width, height = 1000, 620
    left, right, top, bottom = 72, 28, 70, 160
    plot_width = width - left - right
    plot_height = height - top - bottom
    agent_ids = list(display_names)
    dates, series = build_cumulative_history(records, agent_ids)
    maximum = max((max(values, default=0) for values in series.values()), default=0)
    y_max = max(1, maximum)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        "<title>Cumulative Hell reports by harness</title>",
        "<desc>Each line shows the cumulative number of archived reports for one coding agent harness over time.</desc>",
        "<style>",
        ".label{fill:#57606a;font:13px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif}",
        ".title{fill:#24292f;font:600 20px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif}",
        ".grid{stroke:#d0d7de;stroke-width:1}.axis{stroke:#8c959f;stroke-width:1.2}",
        ".series{fill:none;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}",
        "@media (prefers-color-scheme:dark){.label{fill:#8b949e}.title{fill:#c9d1d9}.grid{stroke:#30363d}.axis{stroke:#6e7681}}",
        "</style>",
        '<text class="title" x="72" y="34">Cumulative Hell reports by harness</text>',
    ]

    for tick in _chart_ticks(y_max):
        y = top + plot_height - (tick / y_max * plot_height)
        lines.append(f'<line class="grid" x1="{left}" y1="{y:.2f}" x2="{width - right}" y2="{y:.2f}"/>')
        lines.append(f'<text class="label" x="{left - 12}" y="{y + 4:.2f}" text-anchor="end">{tick}</text>')

    lines.extend(
        [
            f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}"/>',
            f'<line class="axis" x1="{left}" y1="{top + plot_height}" x2="{width - right}" y2="{top + plot_height}"/>',
        ]
    )

    if dates:
        date_values = [date.fromisoformat(value) for value in dates]
        first_ordinal = date_values[0].toordinal()
        span = max(1, date_values[-1].toordinal() - first_ordinal)

        def x_position(value: date) -> float:
            return left + ((value.toordinal() - first_ordinal) / span * plot_width)

        tick_count = min(6, len(date_values))
        tick_indexes = sorted(
            {round(index * (len(date_values) - 1) / max(1, tick_count - 1)) for index in range(tick_count)}
        )
        for index in tick_indexes:
            x = x_position(date_values[index])
            lines.append(
                f'<text class="label" x="{x:.2f}" y="{top + plot_height + 25}" text-anchor="middle">{escape(dates[index])}</text>'
            )

        for index, agent_id in enumerate(agent_ids):
            color = CHART_COLORS[index % len(CHART_COLORS)]
            points = " ".join(
                f"{x_position(day):.2f},{top + plot_height - (value / y_max * plot_height):.2f}"
                for day, value in zip(date_values, series[agent_id])
            )
            lines.append(
                f'<polyline class="series" data-agent={quoteattr(agent_id)} stroke="{color}" points="{points}"/>'
            )
    else:
        lines.append(
            f'<text class="label" x="{left + plot_width / 2:.2f}" y="{top + plot_height / 2:.2f}" text-anchor="middle">No archived reports yet</text>'
        )

    legend_top = height - 104
    column_width = 300
    for index, agent_id in enumerate(agent_ids):
        column, row = index % 3, index // 3
        x = left + column * column_width
        y = legend_top + row * 28
        color = CHART_COLORS[index % len(CHART_COLORS)]
        total = series[agent_id][-1] if series[agent_id] else 0
        label = f"{display_names[agent_id]} · {total}"
        lines.append(f'<line x1="{x}" y1="{y}" x2="{x + 24}" y2="{y}" stroke="{color}" stroke-width="4" stroke-linecap="round"/>')
        lines.append(f'<text class="label" x="{x + 34}" y="{y + 4}">{escape(label)}</text>')

    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def generate_history_chart(
    records: list[dict[str, Any]], display_names: dict[str, str], target: Path
) -> bool:
    return write_if_changed(target, render_history_svg(records, display_names))


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
        "### Cumulative reports by harness",
        "",
        f"![Cumulative Hell reports by harness]({HISTORY_CHART})",
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
    parser.add_argument("--history-chart", type=Path, default=Path(HISTORY_CHART))
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
    generate_history_chart(records, display_names, args.history_chart)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
