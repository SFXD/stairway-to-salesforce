"""
Validation and sanitization utilities for Salesforce objects, fields, and SOQL.

These utilities prevent injection attacks and ensure data integrity when
interacting with Salesforce APIs.
"""

import re
from typing import Any
from datetime import datetime, date


def sanitize_sobject_name(sobject_name: str) -> str:
    """
    Validate and sanitize Salesforce object names to prevent injection.
    
    Salesforce object names must:
    - Start with a letter
    - Contain only letters, numbers, and underscores
    - May end with __c (custom objects), __r (relationships), __e (events), etc.
    - Examples: Account, Contact, Custom_Object__c, My_Custom__c
    
    Args:
        sobject_name: Object name to validate
    
    Returns:
        Validated object name (unchanged if valid)
    
    Raises:
        ValueError: If object name is invalid or potentially malicious
    
    Examples:
        >>> sanitize_sobject_name("Account")
        'Account'
        >>> sanitize_sobject_name("Custom_Object__c")
        'Custom_Object__c'
        >>> sanitize_sobject_name("My_Custom_Object__c")
        'My_Custom_Object__c'
        >>> sanitize_sobject_name("'; DROP TABLE--")
        ValueError: Invalid Salesforce object name
    """
    if not sobject_name:
        raise ValueError("Object name cannot be empty")
    
    # Salesforce object naming rules:
    # - Start with letter
    # - Can contain letters, numbers, underscores (including consecutive underscores)
    # - May have suffixes like __c, __r, __e, __mdt, __b, __pc, __ka, __kav, __x, __xo
    # Pattern explanation:
    # ^[a-zA-Z]         - Start with letter
    # [a-zA-Z0-9_]*     - Followed by any number of letters, numbers, or underscores
    # (__[a-zA-Z]+)?    - Optional suffix like __c, __mdt, etc.
    # $                 - End of string
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]*(__[a-zA-Z]+)?$'
    
    if not re.match(pattern, sobject_name):
        raise ValueError(
            f"Invalid Salesforce object name: '{sobject_name}'. "
            f"Object names must start with a letter and contain only "
            f"letters, numbers, and underscores. "
            f"Custom objects should end with suffixes like '__c'."
        )
    
    # Additional validation: check length (Salesforce limit is 40 characters for API name)
    if len(sobject_name) > 255:  # Being generous with limit
        raise ValueError(
            f"Object name too long: '{sobject_name}'. "
            f"Maximum length is 255 characters."
        )
    
    return sobject_name


def sanitize_field_name(field_name: str, allow_relationship_notation: bool = True) -> str:
    """
    Validate and sanitize SOQL field names to prevent injection.
    
    Salesforce field names can:
    - Start with a letter
    - Contain letters, numbers, underscores (including consecutive underscores)
    - End with __c (custom fields), __r (relationship fields), etc.
    - Include dots for relationship notation (e.g., Account.Name, Owner__r.Email)
    
    Args:
        field_name: Field name to validate
        allow_relationship_notation: Whether to allow dots for relationships
    
    Returns:
        Validated field name (unchanged if valid)
    
    Raises:
        ValueError: If field name is invalid or potentially malicious
    
    Examples:
        >>> sanitize_field_name("Name")
        'Name'
        >>> sanitize_field_name("truncated_description__c")
        'truncated_description__c'
        >>> sanitize_field_name("Custom_Field__c")
        'Custom_Field__c'
        >>> sanitize_field_name("Account.Name")
        'Account.Name'
        >>> sanitize_field_name("Owner__r.Email")
        'Owner__r.Email'
        >>> sanitize_field_name("My_Lookup__r.Custom_Field__c")
        'My_Lookup__r.Custom_Field__c'
        >>> sanitize_field_name("'; DROP--")
        ValueError: Invalid field name
    """
    if not field_name:
        raise ValueError("Field name cannot be empty")
    
    if allow_relationship_notation:
        # Allow dots for relationship notation: Account.Name, Owner__r.Email
        # Pattern explanation:
        # ^[a-zA-Z]              - Start with letter
        # [a-zA-Z0-9_]*          - Letters, numbers, underscores (including __)
        # (__[a-zA-Z]+)?         - Optional suffix like __c, __r
        # (\.[a-zA-Z]...)*       - Optional relationship traversal (can repeat)
        # $                      - End of string
        pattern = r'^[a-zA-Z][a-zA-Z0-9_]*(__[a-zA-Z]+)?(\.[a-zA-Z][a-zA-Z0-9_]*(__[a-zA-Z]+)?)*$'
    else:
        # Simple field names only (no relationship traversal)
        # Same as object pattern but for fields
        pattern = r'^[a-zA-Z][a-zA-Z0-9_]*(__[a-zA-Z]+)?$'
    
    if not re.match(pattern, field_name):
        raise ValueError(
            f"Invalid field name: '{field_name}'. "
            f"Field names must start with a letter and contain only "
            f"letters, numbers, and underscores. "
            f"Custom fields should end with suffixes like '__c', '__r'. "
            + ("Relationship notation (dots) is allowed." if allow_relationship_notation else "")
        )
    
    # Additional security: block SQL/SOQL keywords that shouldn't be in field names
    dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'TRUNCATE', 'ALTER', 'EXEC', 'EXECUTE']
    field_upper = field_name.upper()
    
    # Check each part of the field name (split by dots for relationships)
    parts = field_name.split('.')
    for part in parts:
        # Remove suffix for keyword check
        part_base = re.sub(r'__[a-zA-Z]+$', '', part).upper()
        if part_base in dangerous_keywords:
            raise ValueError(
                f"Field name contains disallowed keyword: '{part}' in '{field_name}'"
            )
    
    # Additional validation: check length
    if len(field_name) > 255:
        raise ValueError(
            f"Field name too long: '{field_name}'. "
            f"Maximum length is 255 characters."
        )
    
    return field_name


def validate_soql_filter(query_filter: str) -> None:
    """
    Validate SOQL WHERE clause filter for security issues.
    
    Checks for common SQL/SOQL injection patterns and dangerous keywords.
    Should be called before using user-provided filters in SOQL queries.
    
    Args:
        query_filter: SOQL WHERE clause filter to validate
    
    Raises:
        ValueError: If filter contains dangerous patterns or keywords
    
    Examples:
        >>> validate_soql_filter("Status = 'Active'")  # OK
        >>> validate_soql_filter("Status = 'Active' AND Type = 'Customer'")  # OK
        >>> validate_soql_filter("Custom_Field__c = 'Value'")  # OK
        >>> validate_soql_filter("Status = 'Active'; DROP TABLE")
        ValueError: Query filter contains potentially dangerous pattern
    """
    if not query_filter:
        return
    
    # Check for dangerous patterns
    dangerous_patterns = [
        r';\s*DROP',
        r';\s*DELETE',
        r';\s*INSERT',
        r';\s*UPDATE',
        r';\s*TRUNCATE',
        r';\s*ALTER',
        r';\s*CREATE',
        r';\s*EXEC',
        r'--',  # SQL comments
        r'/\*',  # Multi-line comments
        r'\*/',  # End of multi-line comment
    ]
    
    filter_upper = query_filter.upper()
    
    for pattern in dangerous_patterns:
        if re.search(pattern, filter_upper, re.IGNORECASE):
            raise ValueError(
                f"Query filter contains potentially dangerous pattern. "
                f"Filter: {query_filter}"
            )
    
    # Check for dangerous standalone keywords at word boundaries
    # This prevents false positives with field names containing these words
    dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'TRUNCATE', 'ALTER', 'CREATE', 'EXEC', 'EXECUTE']
    
    # Use word boundaries to avoid false positives with custom fields like Update__c
    for keyword in dangerous_keywords:
        # Check if keyword appears as a standalone word (not part of field name)
        # Allow it if it's part of a field name (followed/preceded by underscore or letter/number)
        pattern = r'\b' + keyword + r'\b(?!_)'  # Word boundary but not followed by underscore
        if re.search(pattern, filter_upper):
            # Additional check: make sure it's not part of a custom field name like Update__c
            # Look for pattern: keyword followed by __ (custom field pattern)
            if not re.search(keyword + r'__', filter_upper):
                raise ValueError(
                    f"Query filter contains disallowed keyword: {keyword}. "
                    f"Filter: {query_filter}"
                )


def format_soql_value(value: Any, field_type: str = "auto") -> str:
    """
    Safely format a value for use in SOQL queries with proper escaping.
    
    IMPORTANT SOQL Formatting Rules:
    - DateTime literals: NOT quoted, ISO 8601 format (2025-11-16T12:24:27.000Z)
    - Date literals: NOT quoted, YYYY-MM-DD format (2025-11-16)
    - String literals: Quoted with escaped single quotes ('John\\'s Account')
    - Number literals: NOT quoted (1000, 99.99)
    - Boolean literals: NOT quoted, lowercase (true, false)
    - Null: NOT quoted (null)
    
    Args:
        value: Value to format
        field_type: Type hint ("datetime", "date", "string", "number", "boolean", "auto")
                   "auto" will attempt to detect the type
    
    Returns:
        Properly formatted and escaped SOQL value
    
    Raises:
        ValueError: If value cannot be formatted as specified type
    
    References:
        https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_dateformats.htm
    
    Examples:
        >>> format_soql_value(datetime(2025, 11, 16, 12, 0), "datetime")
        '2025-11-16T12:00:00.000Z'
        >>> format_soql_value("Active", "string")
        "'Active'"
        >>> format_soql_value(1000, "number")
        '1000'
        >>> format_soql_value(True, "boolean")
        'true'
    """
    if value is None:
        return "null"
    
    # Auto-detect type if not specified
    if field_type == "auto":
        if isinstance(value, datetime):
            field_type = "datetime"
        elif isinstance(value, date):
            field_type = "date"
        elif isinstance(value, bool):
            field_type = "boolean"
        elif isinstance(value, (int, float)):
            field_type = "number"
        elif isinstance(value, str):
            # Try to detect datetime/date strings
            if 'T' in value and ('Z' in value or '+' in value or value.count(':') >= 2):
                field_type = "datetime"
            elif re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                field_type = "date"
            else:
                field_type = "string"
        else:
            field_type = "string"
    
    # Format based on type
    if field_type == "datetime":
        if isinstance(value, str):
            # Validate ISO format
            if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value):
                raise ValueError(
                    f"Invalid datetime format: {value}. Expected ISO 8601 format."
                )
            # Ensure it ends with Z if no timezone specified
            if not (value.endswith('Z') or '+' in value or value.count('-') > 2):
                value = value + 'Z'
            return value  # NO QUOTES for datetime literals
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        else:
            raise ValueError(f"Cannot format {type(value).__name__} as datetime")
    
    elif field_type == "date":
        if isinstance(value, str):
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                raise ValueError(f"Invalid date format: {value}. Expected YYYY-MM-DD.")
            return value  # NO QUOTES for date literals
        elif isinstance(value, (datetime, date)):
            return value.strftime("%Y-%m-%d")
        else:
            raise ValueError(f"Cannot format {type(value).__name__} as date")
    
    elif field_type == "number":
        return str(value)
    
    elif field_type == "boolean":
        return "true" if value else "false"
    
    else:  # string or default
        value_str = str(value)
        # Escape single quotes using backslash (SOQL standard)
        escaped = value_str.replace("'", "\\'")
        return f"'{escaped}'"


def validate_field_names(fields: dict[str, str], allow_relationship_notation: bool = True) -> None:
    """
    Validate all field names in a field mapping dictionary.
    
    Args:
        fields: Dictionary of source field names to target field names
        allow_relationship_notation: Whether to allow dots for relationships
    
    Raises:
        ValueError: If any field name is invalid
    
    Examples:
        >>> validate_field_names({"Id": "account_id", "Name": "account_name"})
        >>> validate_field_names({"truncated_description__c": "description"})
        >>> validate_field_names({"Custom_Field__c": "custom"})
        >>> validate_field_names({"'; DROP--": "bad"})
        ValueError: Invalid field name
    """
    if not fields:
        raise ValueError("Fields dictionary cannot be empty")
    
    for field_name in fields.keys():
        sanitize_field_name(field_name, allow_relationship_notation)