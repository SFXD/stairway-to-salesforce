"""
Unit tests for Salesforce validation utilities.
"""

import pytest

from stairway_to_salesforce.utils.salesforce_validators import (
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

    def test_invalid_special_characters(self):
        """Test objects with invalid characters."""
        with pytest.raises(ValueError, match="Invalid.*object name"):
            sanitize_sobject_name("Account!")
        with pytest.raises(ValueError, match="Invalid.*object name"):
            sanitize_sobject_name("Object-Name")

    def test_prevents_sql_injection(self):
        """Test that SQL injection attempts are caught."""
        error_pattern = "Invalid.*object name|Dangerous pattern|Disallowed keyword"
        with pytest.raises(ValueError, match=error_pattern):
            sanitize_sobject_name("Account; DROP TABLE Users")


class TestSanitizeFieldName:
    """Tests for sanitize_field_name()"""

    def test_valid_field_name(self):
        """Test validation of valid field names."""
        assert sanitize_field_name("Name") == "Name"
        assert sanitize_field_name("Custom_Field__c") == "Custom_Field__c"

    def test_relationship_notation(self):
        """Test validation with relationship notation (dots)."""
        assert sanitize_field_name("Account.Name") == "Account.Name"
        assert sanitize_field_name("Contact.Account.Name") == "Contact.Account.Name"

    def test_relationship_notation_disabled(self):
        """Test that relationship notation can be disabled."""
        with pytest.raises(ValueError, match="Invalid.*field name"):
            sanitize_field_name("Account.Name", allow_relationship_notation=False)

    def test_invalid_special_characters(self):
        """Test fields with invalid characters."""
        with pytest.raises(ValueError, match="Invalid.*field name"):
            sanitize_field_name("Field-Name")
        with pytest.raises(ValueError, match="Invalid.*field name"):
            sanitize_field_name("Name!")

    def test_keyword_in_field_name(self):
        """Test that standalone keywords are rejected but custom fields are OK."""
        # Custom field with keyword is fine
        assert sanitize_field_name("Update__c") == "Update__c"

        # Standalone keyword is rejected
        with pytest.raises(ValueError, match="Disallowed keyword"):
            sanitize_field_name("DROP")


class TestValidateSoqlFilter:
    """Tests for validate_soql_filter()"""

    def test_valid_filter(self):
        """Test valid SOQL filters."""
        validate_soql_filter("Name = 'Acme'")
        validate_soql_filter("CreatedDate > 2025-01-01T00:00:00Z")
        validate_soql_filter(
            "IsDeleted = false AND (Status = 'Active' OR Type = 'Partner')"
        )

    def test_invalid_sql_injection(self):
        """Test filters with SQL injection patterns."""
        with pytest.raises(ValueError, match="Dangerous pattern|potentially dangerous"):
            validate_soql_filter("Name = 'Acme'; DROP TABLE Account")
        with pytest.raises(ValueError, match="Dangerous pattern|potentially dangerous"):
            validate_soql_filter("Name = 'Acme' -- comment")

    def test_invalid_dangerous_keywords(self):
        """Test filters with dangerous standalone keywords."""
        with pytest.raises(ValueError, match="Disallowed keyword"):
            validate_soql_filter("DELETE FROM Account")

    def test_unbalanced_quotes(self):
        """Test filters with unbalanced quotes."""
        with pytest.raises(ValueError, match="unbalanced single quotes"):
            validate_soql_filter("Name = 'Acme")


class TestValidateFieldNames:
    """Tests for validate_field_names()"""

    def test_valid_field_names(self):
        """Test validation of valid field mappings."""
        fields = {
            "Id": "account_id",
            "Name": "account_name",
            "Custom_Field__c": "custom",
        }
        validate_field_names(fields)

    def test_invalid_field_in_dict(self):
        """Test that any invalid field in dict raises error."""
        fields = {"Id": "id", "'; DROP--": "bad"}
        with pytest.raises(ValueError, match="Invalid.*field name|Dangerous pattern"):
            validate_field_names(fields)
