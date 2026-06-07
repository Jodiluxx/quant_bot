"""Static code-audit helpers for the legacy monolith.

The functions here deliberately avoid importing ``quant bot.py``. They parse it
as text/AST so cleanup planning cannot accidentally start network clients,
Telegram polling, or runtime side effects.
"""
from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .paths import LEGACY_BOT_FILE


@dataclass(frozen=True)
class DefinitionInfo:
    name: str
    line: int
    kind: str


def legacy_definitions(path: str | Path = LEGACY_BOT_FILE) -> list[DefinitionInfo]:
    """Return top-level functions/classes from the legacy bot file."""
    source_path = Path(path)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    rows: list[DefinitionInfo] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            rows.append(DefinitionInfo(node.name, int(node.lineno), type(node).__name__))
    return rows


def duplicate_definition_map(definitions: Iterable[DefinitionInfo]) -> dict[str, list[DefinitionInfo]]:
    grouped: dict[str, list[DefinitionInfo]] = defaultdict(list)
    for item in definitions:
        grouped[item.name].append(item)
    return {name: rows for name, rows in grouped.items() if len(rows) > 1}


def active_definition_map(definitions: Iterable[DefinitionInfo]) -> dict[str, DefinitionInfo]:
    """Return the last top-level definition per name, matching Python shadowing."""
    active: dict[str, DefinitionInfo] = {}
    for item in definitions:
        active[item.name] = item
    return active


def audit_payload(
    *,
    path: str | Path = LEGACY_BOT_FILE,
    active_runtime_names: Iterable[str] | None = None,
    duplicate_limit: int = 25,
) -> dict[str, Any]:
    """Build a compact static audit payload for cleanup planning."""
    definitions = legacy_definitions(path)
    duplicates = duplicate_definition_map(definitions)
    active = active_definition_map(definitions)
    active_names = set(active_runtime_names or [])
    active_runtime_defs = {
        name: active[name]
        for name in sorted(active_names)
        if name in active
    }
    duplicate_rows = sorted(
        duplicates.items(),
        key=lambda item: (-len(item[1]), item[0]),
    )[: int(duplicate_limit)]
    return {
        "path": str(Path(path)),
        "total_definitions": len(definitions),
        "unique_definitions": len(active),
        "duplicate_names": len(duplicates),
        "shadowed_definitions": len(definitions) - len(active),
        "active_runtime_definitions": len(active_runtime_defs),
        "top_duplicates": [
            {
                "name": name,
                "count": len(rows),
                "active_line": active[name].line if name in active else None,
                "lines": [row.line for row in rows],
                "kind": rows[-1].kind,
            }
            for name, rows in duplicate_rows
        ],
        "active_runtime_lines": {
            name: {"line": item.line, "kind": item.kind}
            for name, item in active_runtime_defs.items()
        },
    }


def cleanup_priority(payload: dict[str, Any]) -> list[str]:
    """Human-readable cleanup recommendations from an audit payload."""
    recs: list[str] = []
    if int(payload.get("duplicate_names") or 0) > 50:
        recs.append("Clean by extracting covered modules first, not by mass-deleting old shadowed functions.")
    if int(payload.get("shadowed_definitions") or 0) > 100:
        recs.append("Map _base_* wrappers before deleting old runtime layers.")
    if payload.get("top_duplicates"):
        first = payload["top_duplicates"][0]
        recs.append(f"Most duplicated area: {first['name']} ({first['count']} definitions).")
    recs.append("Next safe step: extract pure UI/report functions with tests, then delete only covered wrappers.")
    return recs
