"""Execution gateway adapter."""
from __future__ import annotations

from typing import Any

from ..legacy import call_legacy


def execution_mode(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("execution_mode", *args, **kwargs)


def build_execution_order_plan(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("build_execution_order_plan", *args, **kwargs)


def execution_plan_line(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("_execution_plan_line_v715", *args, **kwargs)


def format_execution_status(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_execution_status", *args, **kwargs)


def submit_testnet_order_test(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("submit_testnet_order_test", *args, **kwargs)


def validate_protection_order_geometry(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("validate_protection_order_geometry", *args, **kwargs)


def submit_testnet_protection_order_tests(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("submit_testnet_protection_order_tests", *args, **kwargs)


def format_testnet_status(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_testnet_status", *args, **kwargs)


def testnet_event_line(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("_testnet_event_line_v721", *args, **kwargs)


def format_testnet_journal_report(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_testnet_journal_report", *args, **kwargs)


def format_testnet_reconciliation_report(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_testnet_reconciliation_report", *args, **kwargs)


def build_live_readiness_checklist(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("build_live_readiness_checklist", *args, **kwargs)


def format_live_readiness_checklist(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_live_readiness_checklist", *args, **kwargs)
