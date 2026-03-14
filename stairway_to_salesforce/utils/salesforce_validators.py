"""
Validation and sanitization utilities for Salesforce objects, fields, and SOQL.
"""

import re
from datetime import date, datetime
from typing import Any

# 1. BASE PATTERNS
_SF_NAME = r"[a-zA-Z][a-zA-Z0-9_]*"
_SF_SUFFIX = r"(__[cr|e|p|v|share|history|changeevent])?"

# 2. COMPILED REGEX
RE_SOBJECT_NAME = re.compile(f"^{_SF_NAME}{_SF_SUFFIX}$")
RE_FIELD_NAME_STRICT = re.compile(f"^{_SF_NAME}{_SF_SUFFIX}$")
RE_FIELD_NAME_RELATIONSHIP = re.compile(f"^{_SF_NAME}(\\.{_SF_NAME})*{_SF_SUFFIX}$")

RE_DANGEROUS_CONTENT = re.compile(
    r"("
    r";|--|/\*|\*/|\0|"
    r"\b(DROP|DELETE|INSERT|UPDATE|TRUNCATE|ALTER|CREATE|EXEC|EXECUTE)\b(?!__)|"
    r"\(.*SELECT.*\)"
    r")",
    re.IGNORECASE,
)


def _check_dangerous_patterns(value: str, context: str) -> None:
    match = RE_DANGEROUS_CONTENT.search(value)
    if match:
        forbidden = match.group(0).upper()
        # Maintenance of legacy error strings for test compatibility
        if any(kw in forbidden for kw in ["DROP", "DELETE", "UPDATE", "INSERT", "SELECT"]):
            raise ValueError(f"Disallowed keyword detected in {context}: {forbidden}")
        raise ValueError(f"Dangerous pattern detected in {context}: {forbidden}")


def sanitize_sobject_name(sobject_name: str) -> str:
    if not sobject_name:
        raise ValueError("Object name cannot be empty")
    if not RE_SOBJECT_NAME.match(sobject_name):
        raise ValueError(f"Invalid Salesforce object name: {sobject_name}")
    _check_dangerous_patterns(sobject_name, "object name")
    return sobject_name


def sanitize_field_name(field_name: str, allow_relationship_notation: bool = True) -> str:
    if not field_name:
        raise ValueError("Field name cannot be empty")
    regex = RE_FIELD_NAME_RELATIONSHIP if allow_relationship_notation else RE_FIELD_NAME_STRICT
    if not regex.match(field_name):
        raise ValueError(f"Invalid Salesforce field name: {field_name}")
    _check_dangerous_patterns(field_name, "field name")
    return field_name


def validate_soql_filter(query_filter: str | None) -> None:
    if not query_filter:
        return
    _check_dangerous_patterns(query_filter, "query filter")
    if query_filter.count("'") % 2 != 0:
        raise ValueError("Security violation: unbalanced single quotes in filter")


def validate_field_names(fields: dict[str, str], allow_relationship_notation: bool = True) -> None:
    for source_field in fields.keys():
        sanitize_field_name(source_field, allow_relationship_notation=allow_relationship_notation)


def _detect_type(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return "datetime" if isinstance(value, datetime) else "date"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, bool):
        return "boolean"
    return "string"


def format_soql_value(value: Any, field_type: str = "auto") -> str:
    """Format a Python value for use in a SOQL query string."""
    if value is None:
        return "NULL"

    actual_type = field_type if field_type != "auto" else _detect_type(value)

    if actual_type == "datetime":
        if isinstance(value, (datetime, date)):
            # Salesforce format: 2024-01-01T00:00:00.000Z
            return value.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        return str(value)
    elif actual_type == "date":
        if isinstance(value, (datetime, date)):
            return value.strftime("%Y-%m-%d")
        return str(value)
    elif actual_type == "number":
        return str(value)
    elif actual_type == "boolean":
        return "true" if value else "false"
    else:
        escaped = str(value).replace("'", "\\'")
        return f"'{escaped}'"
