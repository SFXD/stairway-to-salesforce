"""
Unit tests for Salesforce destination job executor (dispatch router).
"""

from unittest.mock import MagicMock, Mock, call, patch

import pytest

from stairway_to_salesforce.destinations.salesforce_bulk2.job_executor import \
    execute_job


class TestExecuteJob:
    """Tests for execute_job() dispatch function."""

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_insert"
    )
    def test_execute_job_insert(self, mock_insert, temp_csv_file):
        """Test job execution dispatches to insert."""
        mock_driver = Mock()
        mock_resolver = Mock()

        execute_job(
            sf_driver=mock_driver,
            target_name="Account",
            salesforce_operation="insert",
            primary_key=None,
            file_path=temp_csv_file,
            key_resolver=mock_resolver,
        )

        # Should call exec_insert
        mock_insert.assert_called_once_with(
            sf_driver=mock_driver,
            target_name="Account",
            file_path=temp_csv_file,
            primary_key=None,
            key_resolver=mock_resolver,
        )

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_upsert"
    )
    def test_execute_job_upsert(self, mock_upsert, temp_csv_file):
        """Test job execution dispatches to upsert."""
        mock_driver = Mock()
        mock_resolver = Mock()

        execute_job(
            sf_driver=mock_driver,
            target_name="Account",
            salesforce_operation="upsert",
            primary_key="External_ID__c",
            file_path=temp_csv_file,
            key_resolver=mock_resolver,
        )

        # Should call exec_upsert
        mock_upsert.assert_called_once_with(
            sf_driver=mock_driver,
            target_name="Account",
            file_path=temp_csv_file,
            primary_key="External_ID__c",
            key_resolver=mock_resolver,
        )

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_delete"
    )
    def test_execute_job_delete(self, mock_delete, temp_csv_file):
        """Test job execution dispatches to delete."""
        mock_driver = Mock()
        mock_resolver = Mock()

        execute_job(
            sf_driver=mock_driver,
            target_name="Account",
            salesforce_operation="delete",
            primary_key="Id",
            file_path=temp_csv_file,
            key_resolver=mock_resolver,
        )

        # Should call exec_delete
        mock_delete.assert_called_once_with(
            sf_driver=mock_driver,
            target_name="Account",
            file_path=temp_csv_file,
            primary_key="Id",
            key_resolver=mock_resolver,
        )

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_replace"
    )
    def test_execute_job_replace(self, mock_replace, temp_csv_file):
        """Test job execution dispatches to replace."""
        mock_driver = Mock()
        mock_resolver = Mock()

        execute_job(
            sf_driver=mock_driver,
            target_name="Account",
            salesforce_operation="replace",
            primary_key="Id",
            file_path=temp_csv_file,
            key_resolver=mock_resolver,
        )

        # Should call exec_replace
        mock_replace.assert_called_once_with(
            sf_driver=mock_driver,
            target_name="Account",
            file_path=temp_csv_file,
            primary_key="Id",
            key_resolver=mock_resolver,
        )

    def test_execute_job_invalid_operation(self, temp_csv_file):
        """Test that invalid operation raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported operation"):
            execute_job(
                sf_driver=Mock(),
                target_name="Account",
                salesforce_operation="invalid_operation",
                primary_key=None,
                file_path=temp_csv_file,
                key_resolver=None,
            )

    def test_execute_job_invalid_operation_message(self, temp_csv_file):
        """Test that error message includes valid operations."""
        with pytest.raises(ValueError) as exc_info:
            execute_job(
                sf_driver=Mock(),
                target_name="Account",
                salesforce_operation="merge",  # Not supported
                primary_key=None,
                file_path=temp_csv_file,
                key_resolver=None,
            )

        error_msg = str(exc_info.value)
        assert "insert" in error_msg
        assert "upsert" in error_msg
        assert "delete" in error_msg
        assert "replace" in error_msg

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_insert"
    )
    def test_execute_job_passes_all_kwargs(self, mock_insert, temp_csv_file):
        """Test that execute_job passes all parameters correctly."""
        mock_driver = Mock()
        mock_resolver = Mock()

        execute_job(
            sf_driver=mock_driver,
            target_name="Custom_Object__c",
            salesforce_operation="insert",
            primary_key=["Field1__c", "Field2__c"],
            file_path=temp_csv_file,
            key_resolver=mock_resolver,
        )

        # Verify all parameters passed
        call_kwargs = mock_insert.call_args[1]
        assert call_kwargs["sf_driver"] == mock_driver
        assert call_kwargs["target_name"] == "Custom_Object__c"
        assert call_kwargs["file_path"] == temp_csv_file
        assert call_kwargs["primary_key"] == ["Field1__c", "Field2__c"]
        assert call_kwargs["key_resolver"] == mock_resolver

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_upsert"
    )
    def test_execute_job_without_resolver(self, mock_upsert, temp_csv_file):
        """Test execution without key_resolver (optional parameter)."""
        execute_job(
            sf_driver=Mock(),
            target_name="Account",
            salesforce_operation="upsert",
            primary_key="Id",
            file_path=temp_csv_file,
            key_resolver=None,
        )

        # Should still work
        mock_upsert.assert_called_once()
        assert mock_upsert.call_args[1]["key_resolver"] is None


class TestExecuteJobEdgeCases:
    """Tests for edge cases in job execution."""

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_insert"
    )
    def test_execute_job_custom_object(self, mock_insert, temp_csv_file):
        """Test execution with custom Salesforce object."""
        execute_job(
            sf_driver=Mock(),
            target_name="My_Custom_Object__c",
            salesforce_operation="insert",
            primary_key=None,
            file_path=temp_csv_file,
            key_resolver=None,
        )

        assert mock_insert.call_args[1]["target_name"] == "My_Custom_Object__c"

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_delete"
    )
    def test_execute_job_list_primary_key(self, mock_delete, temp_csv_file):
        """Test execution with list primary key."""
        execute_job(
            sf_driver=Mock(),
            target_name="Account",
            salesforce_operation="delete",
            primary_key=["Id", "External_ID__c"],
            file_path=temp_csv_file,
            key_resolver=None,
        )

        # Should pass list as-is
        assert mock_delete.call_args[1]["primary_key"] == ["Id", "External_ID__c"]

    def test_execute_job_case_sensitive_operation(self, temp_csv_file):
        """Test that operation matching is case-sensitive."""
        # Should fail with wrong case
        with pytest.raises(ValueError, match="Unsupported operation"):
            execute_job(
                sf_driver=Mock(),
                target_name="Account",
                salesforce_operation="INSERT",  # Wrong case
                primary_key=None,
                file_path=temp_csv_file,
                key_resolver=None,
            )


class TestDispatchMapIntegrity:
    """Tests to ensure dispatch map covers all operations."""

    def test_all_operations_have_handlers(self):
        """Test that all valid operations have corresponding handlers."""
        from stairway_to_salesforce.destinations.salesforce_bulk2.job_executor import (
            exec_delete, exec_insert, exec_replace, exec_upsert)

        # All these should be callable
        assert callable(exec_insert)
        assert callable(exec_upsert)
        assert callable(exec_delete)
        assert callable(exec_replace)

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_insert"
    )
    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_upsert"
    )
    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_delete"
    )
    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_replace"
    )
    def test_all_operations_dispatched(
        self, mock_replace, mock_delete, mock_upsert, mock_insert, temp_csv_file
    ):
        """Test that all operations can be dispatched."""
        operations = ["insert", "upsert", "delete", "replace"]

        for operation in operations:
            execute_job(
                sf_driver=Mock(),
                target_name="Account",
                salesforce_operation=operation,
                primary_key="Id",
                file_path=temp_csv_file,
                key_resolver=None,
            )

        # Each should be called once
        mock_insert.assert_called_once()
        mock_upsert.assert_called_once()
        mock_delete.assert_called_once()
        mock_replace.assert_called_once()


class TestJobExecutorErrorHandling:
    """Tests for error handling in job executor."""

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_insert"
    )
    def test_execute_job_propagates_operation_errors(self, mock_insert, temp_csv_file):
        """Test that errors from operations are propagated."""
        mock_insert.side_effect = RuntimeError("Salesforce API Error")

        with pytest.raises(RuntimeError, match="Salesforce API Error"):
            execute_job(
                sf_driver=Mock(),
                target_name="Account",
                salesforce_operation="insert",
                primary_key=None,
                file_path=temp_csv_file,
                key_resolver=None,
            )

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_insert"
    )
    def test_execute_job_with_none_file_path(self, mock_insert):
        """Test handling of None file path."""
        # FIX: Mock the insert operation to avoid the actual execution
        mock_insert.return_value = None

        # The error might occur in the operation itself, not in execute_job
        # So we just verify execute_job dispatches correctly
        execute_job(
            sf_driver=Mock(),
            target_name="Account",
            salesforce_operation="insert",
            primary_key=None,
            file_path=None,
            key_resolver=None,
        )

        # Verify it was called with None file_path
        assert mock_insert.call_args[1]["file_path"] is None

    @patch(
        "stairway_to_salesforce.destinations.salesforce_bulk2.job_executor.exec_insert"
    )
    def test_execute_job_with_empty_target_name(self, mock_insert, temp_csv_file):
        """Test handling of empty target name."""
        # May be caught by validation in operations
        execute_job(
            sf_driver=Mock(),
            target_name="",
            salesforce_operation="insert",
            primary_key=None,
            file_path=temp_csv_file,
            key_resolver=None,
        )

        # Should still dispatch (validation happens in operation)
        mock_insert.assert_called_once()
