"""Migration checklist adapter."""
from __future__ import annotations

from typing import Any

from ..legacy import call_legacy


def build_migration_checklist(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("build_migration_checklist", *args, **kwargs)


def format_migration_checklist(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_migration_checklist", *args, **kwargs)
