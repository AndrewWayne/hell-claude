#!/usr/bin/env python3
"""Validate a structured Issue and archive it as a deterministic YAML record."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


MAX_REPORT_CHARS = 50_000
HEADING = re.compile(r"^## ([A-Za-z][A-Za-z ]*)\s*$")
REQUIRED_FIELDS = {
    "Schema Version",
    "Agent",
    "Model",
    "Task Category",
    "User Goal",
    "Expected Behavior",
    "Actual Behavior",
    "Failure Categories",
    "Impact",
    "Evidence",
    "Client Redaction",
}

SENSITIVE_PATTERNS = {
    "api-token": re.compile(r"\b(?:sk|rk|pk)-[A-Za-z0-9_-]{20,}\b"),
    "credential-remote": re.compile(r"https?://[^\s/:]+:[^@\s]+@[^\s]+"),
    "email-address": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "env-assignment": re.compile(
        r"(?im)^\s*(?:export\s+)?[A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD)"
        r"\s*=\s*\S+"
    ),
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "private-key": re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----"),
    "unix-home-path": re.compile(r"(?:/Users|/home)/[A-Za-z0-9._-]+/"),
    "windows-home-path": re.compile(r"[A-Za-z]:\\Users\\[A-Za-z0-9._-]+\\", re.I),
}


def parse_sections(body: str) -> dict[str, str]:
    result: dict[str, str] = {}
    current: str | None = None
    values: list[str] = []
    for line in body.replace("\r\n", "\n").splitlines():
        match = HEADING.match(line)
        if match:
            if current is not None:
                result[current] = "\n".join(values).strip()
            current = match.group(1)
            if current in result:
                raise ValueError(f"duplicate heading: {current}")
            values = []
        elif current is not None:
            values.append(line)
    if current is not None:
        result[current] = "\n".join(values).strip()
    return result


def parse_list(value: str) -> list[str]:
    parsed: list[str] = []
    for line in value.splitlines():
        item = re.sub(r"^\s*[-*]\s*", "", line)
        item = re.sub(r"^\[[ xX]\]\s*", "", item).strip()
        if item:
            parsed.append(item)
    return parsed


def normalize_agent(
    value: str, aliases: dict[str, set[str]]
) -> tuple[str, str | None]:
    raw = value.strip()
    folded = raw.casefold()
    for canonical, values in aliases.items():
        if folded == canonical.casefold() or folded in values:
            return canonical, None if folded == canonical.casefold() else raw
    return "other", raw


def normalize_model(value: str, aliases: dict[str, str]) -> tuple[str, str]:
    raw = value.strip() or "unknown"
    return aliases.get(raw.casefold(), raw), raw


def validate_report(
    sections: dict[str, str], body_length: int, config: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if sections.get("Schema Version") != "1":
        errors.append("unsupported schema version")
    for field in sorted(REQUIRED_FIELDS):
        if not sections.get(field, "").strip():
            errors.append(f"missing field: {field}")
    if body_length > MAX_REPORT_CHARS:
        errors.append(f"report exceeds {MAX_REPORT_CHARS} characters")

    task = sections.get("Task Category", "")
    if task and task not in config["task_categories"]:
        errors.append(f"unknown task category: {task}")

    failures = set(parse_list(sections.get("Failure Categories", "")))
    unknown_failures = sorted(failures - config["failure_categories"])
    if unknown_failures:
        errors.append("unknown failure categories: " + ", ".join(unknown_failures))
    if sections.get("Client Redaction") and sections["Client Redaction"] != "completed":
        errors.append("client redaction is not completed")
    return errors


def scan_sensitive(text: str) -> list[str]:
    return sorted(
        name for name, pattern in SENSITIVE_PATTERNS.items() if pattern.search(text)
    )


def load_config(config_dir: Path) -> dict[str, Any]:
    agents_doc = yaml.safe_load((config_dir / "agents.yml").read_text())
    aliases: dict[str, set[str]] = {}
    display_names: dict[str, str] = {}
    for canonical, entry in agents_doc["agents"].items():
        display_names[canonical] = entry["display_name"]
        aliases[canonical] = {
            str(value).casefold() for value in entry.get("aliases", [])
        }
        aliases[canonical].add(entry["display_name"].casefold())

    model_doc = yaml.safe_load((config_dir / "model-aliases.yml").read_text())
    model_aliases = {
        str(raw).casefold(): str(canonical)
        for raw, canonical in model_doc.get("aliases", {}).items()
    }
    task_doc = yaml.safe_load((config_dir / "task-categories.yml").read_text())
    failure_doc = yaml.safe_load((config_dir / "failure-categories.yml").read_text())
    return {
        "agent_aliases": aliases,
        "agent_display_names": display_names,
        "model_aliases": model_aliases,
        "task_categories": set(task_doc["categories"]),
        "failure_categories": set(failure_doc["categories"]),
    }


def build_record(
    event: dict[str, Any],
    sections: dict[str, str],
    agent_aliases: dict[str, set[str]],
    model_aliases: dict[str, str],
) -> dict[str, Any]:
    issue = event["issue"]
    framework, detected_raw_name = normalize_agent(
        sections["Agent"], agent_aliases
    )
    raw_name = sections.get("Raw Agent Name", "").strip() or detected_raw_name
    model, raw_model = normalize_model(sections.get("Model", ""), model_aliases)
    return {
        "id": f"github-issue-{issue['number']}",
        "schema_version": 1,
        "status": "archived",
        "source_issue": issue["number"],
        "source_url": issue["html_url"],
        "repository": event["repository"]["full_name"],
        "submitted_at": issue["created_at"],
        "updated_at": issue["updated_at"],
        "agent": {
            "framework": framework,
            "raw_name": raw_name,
            "model": model,
            "raw_model": raw_model,
            "client_version": sections.get("Client Version", "").strip() or None,
        },
        "task": {
            "category": sections["Task Category"],
            "goal": sections["User Goal"],
            "expected": sections["Expected Behavior"],
            "actual": sections["Actual Behavior"],
        },
        "failure": {
            "categories": parse_list(sections["Failure Categories"]),
            "impact": parse_list(sections["Impact"]),
            "evidence": sections["Evidence"],
        },
        "privacy": {
            "client_redaction": sections["Client Redaction"] == "completed",
            "server_scan": "passed",
        },
    }


def record_path(repo_root: Path, event: dict[str, Any]) -> Path:
    year = str(event["issue"]["created_at"])[:4]
    return repo_root / "records" / year / f"issue-{event['issue']['number']}.yaml"


def write_record(path: Path, record: dict[str, Any]) -> bool:
    rendered = yaml.safe_dump(
        record, sort_keys=False, allow_unicode=True, width=100
    )
    if path.is_file() and path.read_text(encoding="utf-8") == rendered:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return True


def normalized_goal(record: dict[str, Any]) -> str:
    return " ".join(record["task"]["goal"].casefold().split())


def find_possible_duplicate(record: dict[str, Any], records_root: Path) -> int | None:
    if not records_root.exists():
        return None
    current_issue = record["source_issue"]
    signature = (
        record["agent"]["framework"],
        record["task"]["category"],
        frozenset(record["failure"]["categories"]),
        normalized_goal(record),
    )
    for path in sorted(records_root.rglob("issue-*.yaml")):
        existing = yaml.safe_load(path.read_text(encoding="utf-8"))
        if existing.get("source_issue") == current_issue:
            continue
        existing_signature = (
            existing["agent"]["framework"],
            existing["task"]["category"],
            frozenset(existing["failure"]["categories"]),
            normalized_goal(existing),
        )
        if existing_signature == signature:
            return int(existing["source_issue"])
    return None


def process_event(
    event: dict[str, Any], repo_root: Path, config_dir: Path
) -> dict[str, Any]:
    body = event.get("issue", {}).get("body") or ""
    findings = scan_sensitive(body)
    if findings:
        return {"status": "needs-redaction", "findings": findings}

    try:
        sections = parse_sections(body)
    except ValueError as exc:
        return {"status": "invalid-report", "errors": [str(exc)]}

    config = load_config(config_dir)
    errors = validate_report(sections, len(body), config)
    if errors:
        return {"status": "invalid-report", "errors": errors}

    record = build_record(
        event,
        sections,
        config["agent_aliases"],
        config["model_aliases"],
    )
    duplicate_issue = find_possible_duplicate(record, repo_root / "records")
    path = record_path(repo_root, event)
    changed = write_record(path, record)
    result: dict[str, Any] = {
        "status": "archived",
        "record": path.relative_to(repo_root).as_posix(),
        "changed": changed,
    }
    if duplicate_issue is not None:
        result["duplicate_issue"] = duplicate_issue
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path, default=Path("config"))
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()

    event = json.loads(args.event.read_text(encoding="utf-8"))
    result = process_event(event, args.repo_root, args.config)
    args.result.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
