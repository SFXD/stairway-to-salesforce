"""
Unit tests for Salesforce validation utilities.
"""

from datetime import date, datetime

import pytest

from stairway_to_salesforce.utils.salesforce_validators import (
    format_soql_value,
    sanitize_field_name,
    sanitize_sobject_name,
    validate_field_names,
    validate_soql_filter,
)


class TestSanitizeSobjectName:
    """Tests for sanitize_sobject_name()"""

    def test_valid_standard_object(self):
        """Test validation of standard Salesforce objects."""
        assert sanitize_sobject_name("Account") == "Account"
        assert sanitize_sobject_name("Contact") == "Contact"
        assert sanitize_sobject_name("Opportunity") == "Opportunity"

    def test_valid_custom_object(self):
        """Test validation of custom Salesforce objects."""
        assert sanitize_sobject_name("Custom_Object__c") == "Custom_Object__c"
        assert sanitize_sobject_name("My_Custom__c") == "My_Custom__c"

    def test_valid_with_multiple_underscores(self):
        """Test objects with multiple underscores."""
        assert sanitize_sobject_name("My_Custom_Object__c") == "My_Custom_Object__c"

    def test_invalid_empty_name(self):
        """Test that empty object name raises error."""
        with pytest.raises(ValueError, match="Object name cannot be empty"):
            sanitize_sobject_name("")

    def test_invalid_starts_with_number(self):
        """Test that object starting with number raises error."""
        with pytest.raises(ValueError, match="Invalid Salesforce object name"):
            sanitize_sobject_name("123Account")

    def test_invalid_special_characters(self):
        """Test that special characters raise error."""
        with pytest.raises(ValueError, match="Invalid Salesforce object name"):
            sanitize_sobject_name("Account-Name")

        with pytest.raises(ValueError, match="Invalid Salesforce object name"):
            sanitize_sobject_name("Account.Name")

    def test_sql_injection_attempt(self):
        """Test that SQL injection attempts are blocked."""
        with pytest.raises(ValueError, match="Invalid Salesforce object name"):
            sanitize_sobject_name("Account'; DROP TABLE--")


class TestSanitizeFieldName:
    """Tests for sanitize_field_name()"""

    def test_valid_standard_field(self):
        """Test validation of standard fields."""
        assert sanitize_field_name("Name") == "Name"
        assert sanitize_field_name("Id") == "Id"

    def test_valid_custom_field(self):
        """Test validation of custom fields."""
        assert sanitize_field_name("Custom_Field__c") == "Custom_Field__c"
        assert sanitize_field_name("truncated_description__c") == "truncated_description__c"

    def test_valid_relationship_field(self):
        """Test validation of relationship fields with dot notation."""
        assert sanitize_field_name("Account.Name") == "Account.Name"
        assert sanitize_field_name("Owner__r.Email") == "Owner__r.Email"
        assert (
            sanitize_field_name("Custom_Lookup__r.Custom_Field__c")
            == "Custom_Lookup__r.Custom_Field__c"
        )

    def test_relationship_notation_disabled(self):
        """Test that relationship notation can be disabled."""
        with pytest.raises(ValueError, match="Invalid field name"):
            sanitize_field_name("Account.Name", allow_relationship_notation=False)

    def test_invalid_empty_name(self):
        """Test that empty field name raises error."""
        with pytest.raises(ValueError, match="Field name cannot be empty"):
            sanitize_field_name("")

    def test_invalid_special_characters(self):
        """Test that invalid characters raise error."""
        with pytest.raises(ValueError, match="Invalid field name"):
            sanitize_field_name("Field-Name")

        with pytest.raises(ValueError, match="Invalid field name"):
            sanitize_field_name("Field Name")

    def test_keyword_in_field_name(self):
        """Test that SQL keywords as part of field names are blocked."""
        with pytest.raises(ValueError, match="disallowed keyword"):
            sanitize_field_name("DROP")

        with pytest.raises(ValueError, match="disallowed keyword"):
            sanitize_field_name("DELETE__field")


class TestValidateSoqlFilter:
    """Tests for validate_soql_filter()"""

    def test_valid_simple_filter(self):
        """Test that valid filters pass validation."""
        validate_soql_filter("Status = 'Active'")
        validate_soql_filter("Type = 'Customer'")

    def test_valid_complex_filter(self):
        """Test complex but valid filters."""
        validate_soql_filter("Status = 'Active' AND Type = 'Customer'")
        validate_soql_filter("Custom_Field__c != null")
        validate_soql_filter("truncated_description__c = 'Value'")

    def test_empty_filter(self):
        """Test that empty filter is allowed."""
        validate_soql_filter("")
        validate_soql_filter(None)

    def test_invalid_sql_injection(self):
        """Test that SQL injection attempts are blocked."""
        with pytest.raises(ValueError, match="dangerous pattern"):
            validate_soql_filter("Status = 'Active'; DROP TABLE")

        with pytest.raises(ValueError, match="dangerous pattern"):
            validate_soql_filter("Status = 'Active'-- comment")

    def test_invalid_dangerous_keywords(self):
        """Test that dangerous keywords are blocked."""
        with pytest.raises(ValueError, match="disallowed keyword"):
            validate_soql_filter("UPDATE Account SET Name = 'Bad'")

        with pytest.raises(ValueError, match="disallowed keyword"):
            validate_soql_filter("DELETE FROM Account")


class TestFormatSoqlValue:
    """Tests for format_soql_value()"""

    def test_format_datetime(self):
        """Test datetime formatting."""
        dt = datetime(2025, 1, 18, 14, 30, 0)
        result = format_soql_value(dt, "datetime")
        assert result == "2025-01-18T14:30:00.000Z"
        assert "'" not in result  # No quotes for datetime

    def test_format_date(self):
        """Test date formatting."""
        d = date(2025, 1, 18)
        result = format_soql_value(d, "date")
        assert result == "2025-01-18"
        assert "'" not in result  # No quotes for date

    def test_format_string(self):
        """Test string formatting with quotes."""
        result = format_soql_value("Active", "string")
        assert result == "'Active'"

    def test_format_string_with_escaping(self):
        """Test that single quotes are escaped."""
        result = format_soql_value("John's Account", "string")
        assert result == "'John\\'s Account'"

    def test_format_number(self):
        """Test number formatting."""
        assert format_soql_value(1000, "number") == "1000"
        assert format_soql_value(99.99, "number") == "99.99"
        assert "'" not in format_soql_value(1000, "number")

    def test_format_boolean(self):
        """Test boolean formatting."""
        assert format_soql_value(True, "boolean") == "true"
        assert format_soql_value(False, "boolean") == "false"

    def test_format_null(self):
        """Test null value formatting."""
        assert format_soql_value(None, "string") == "null"
        assert format_soql_value(None, "auto") == "null"

    def test_auto_detection(self):
        """Test automatic type detection."""
        # DateTime
        dt = datetime(2025, 1, 18, 14, 30, 0)
        assert format_soql_value(dt) == "2025-01-18T14:30:00.000Z"

        # String
        assert format_soql_value("test") == "'test'"

        # Number
        assert format_soql_value(42) == "42"

        # Boolean
        assert format_soql_value(True) == "true"


class TestValidateFieldNames:
    """Tests for validate_field_names()"""

    def test_valid_field_names(self):
        """Test validation of valid field mappings."""
        fields = {
            "Id": "account_id",
            "Name": "account_name",
            "Custom_Field__c": "custom",
        }
        validate_field_names(fields)  # Should not raise

    def test_empty_fields_dict(self):
        """Test that empty fields dict raises error."""
        with pytest.raises(ValueError, match="Fields dictionary cannot be empty"):
            validate_field_names({})

    def test_invalid_field_in_dict(self):
        """Test that invalid field names raise error."""
        fields = {"Id": "account_id", "'; DROP--": "bad_field"}
        with pytest.raises(ValueError, match="Invalid field name"):
            validate_field_names(fields)
