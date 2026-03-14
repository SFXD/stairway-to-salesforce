"""
Unit tests for Salesforce destination data processor.
"""

import csv
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pyarrow as pa
import pytest

from stairway_to_salesforce.destinations.salesforce_bulk2.data_processor import (
    _convert_dicts_to_csv,
    _convert_recordbatch_to_csv,
    cleanup_temp_file,
    prepare_data,
)


class TestPrepareData:
    """Tests for prepare_data() function."""

    def test_prepare_data_from_file_path_string(self, temp_csv_file):
        """Test prepare_data with existing CSV file path as string."""
        result = prepare_data(temp_csv_file)

        assert result == temp_csv_file
        assert os.path.exists(result)
        assert result.endswith(".csv")

    def test_prepare_data_from_path_object(self, temp_csv_file):
        """Test prepare_data with Path object."""
        path_obj = Path(temp_csv_file)
        result = prepare_data(path_obj)

        assert result == str(temp_csv_file)
        assert os.path.exists(result)

    def test_prepare_data_nonexistent_file(self):
        """Test that nonexistent file raises ValueError."""
        with pytest.raises(ValueError, match="File does not exist"):
            prepare_data("/nonexistent/directory/file.csv")

    def test_prepare_data_non_csv_file(self, temp_dir):
        """Test that non-CSV file raises ValueError."""
        txt_file = temp_dir / "data.txt"
        txt_file.write_text("test data")

        with pytest.raises(ValueError, match="must be CSV format"):
            prepare_data(str(txt_file))

    def test_prepare_data_from_dict_list(self, sample_account_data):
        """Test prepare_data with list of dictionaries."""
        result = prepare_data(sample_account_data)

        try:
            assert os.path.exists(result)
            assert result.endswith(".csv")

            # Verify CSV content
            with open(result, "r", encoding="utf-8") as f:
                content = f.read()
                assert "001xx000000001" in content
                assert "Acme Corp" in content
                assert "001xx000000002" in content
                assert "Global Industries" in content
        finally:
            if os.path.exists(result):
                os.unlink(result)

    def test_prepare_data_from_recordbatch(self):
        """Test prepare_data with PyArrow RecordBatch."""
        data = {
            "Id": ["001xx000000001", "001xx000000002"],
            "Name": ["Acme Corp", "Global Industries"],
            "Amount": [1000.50, 2000.75],
        }
        batch = pa.RecordBatch.from_pydict(data)

        result = prepare_data(batch)

        try:
            assert os.path.exists(result)
            assert result.endswith(".csv")

            # Verify CSV content
            df = pd.read_csv(result)
            assert len(df) == 2
            assert "Id" in df.columns
            assert "Name" in df.columns
            assert df.iloc[0]["Name"] == "Acme Corp"
        finally:
            if os.path.exists(result):
                os.unlink(result)

    def test_prepare_data_empty_list(self):
        """Test that empty list raises ValueError wrapped in RuntimeError."""
        with pytest.raises(RuntimeError, match="No data items provided"):
            prepare_data([])

    def test_prepare_data_iterator(self):
        """Test prepare_data with iterator of dictionaries."""
        data_iter = iter([{"Id": "001", "Name": "Test1"}, {"Id": "002", "Name": "Test2"}])

        result = prepare_data(data_iter)

        try:
            assert os.path.exists(result)
            df = pd.read_csv(result)
            assert len(df) == 2
        finally:
            if os.path.exists(result):
                os.unlink(result)

    def test_prepare_data_generator(self):
        """Test prepare_data with generator of dictionaries."""

        def data_generator():
            yield {"Id": "001", "Name": "Test1"}
            yield {"Id": "002", "Name": "Test2"}

        result = prepare_data(data_generator())

        try:
            assert os.path.exists(result)
            df = pd.read_csv(result)
            assert len(df) == 2
        finally:
            if os.path.exists(result):
                os.unlink(result)


class TestConvertRecordbatchToCsv:
    """Tests for _convert_recordbatch_to_csv() function."""

    def test_convert_simple_recordbatch(self):
        """Test successful RecordBatch conversion."""
        data = {
            "Id": ["001xx000000001", "001xx000000002"],
            "Name": ["Test 1", "Test 2"],
            "Amount": [100.0, 200.0],
        }
        batch = pa.RecordBatch.from_pydict(data)

        result = _convert_recordbatch_to_csv(batch)

        try:
            assert os.path.exists(result)
            assert result.endswith(".csv")

            # Verify content
            df = pd.read_csv(result)
            assert len(df) == 2
            assert set(df.columns) == {"Id", "Name", "Amount"}
            assert df.iloc[0]["Name"] == "Test 1"
        finally:
            if os.path.exists(result):
                os.unlink(result)

    def test_convert_empty_recordbatch(self):
        """Test that empty RecordBatch raises ValueError wrapped in RuntimeError."""
        schema = pa.schema([("Id", pa.string()), ("Name", pa.string())])
        batch = pa.RecordBatch.from_arrays([pa.array([]), pa.array([])], schema=schema)

        with pytest.raises(RuntimeError, match="contains no data"):
            _convert_recordbatch_to_csv(batch)

    def test_convert_recordbatch_with_null_values(self):
        """Test RecordBatch conversion with null values."""
        data = {
            "Id": ["001", "002", "003"],
            "Name": ["Test", None, "Test3"],
            "Amount": [100.0, 200.0, None],
        }
        batch = pa.RecordBatch.from_pydict(data)

        result = _convert_recordbatch_to_csv(batch)

        try:
            assert os.path.exists(result)
            df = pd.read_csv(result)
            assert len(df) == 3
            # Check that nulls are handled
            assert pd.isna(df.iloc[1]["Name"])
        finally:
            if os.path.exists(result):
                os.unlink(result)

    def test_convert_recordbatch_with_special_characters(self):
        """Test RecordBatch with special characters in data."""
        data = {
            "Id": ["001"],
            "Name": ['Test, with "quotes" and commas'],
            "Description": ["Line1\nLine2\rLine3"],
        }
        batch = pa.RecordBatch.from_pydict(data)

        result = _convert_recordbatch_to_csv(batch)

        try:
            assert os.path.exists(result)
            # Verify CSV is properly escaped
            with open(result, "r", encoding="utf-8") as f:
                content = f.read()
                assert "quotes" in content
        finally:
            if os.path.exists(result):
                os.unlink(result)


class TestConvertDictsToCsv:
    """Tests for _convert_dicts_to_csv() function."""

    def test_convert_simple_dicts(self, sample_account_data):
        """Test successful dict list conversion."""
        result = _convert_dicts_to_csv(sample_account_data)

        try:
            assert os.path.exists(result)
            assert result.endswith(".csv")

            # Verify content
            with open(result, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["Name"] == "Acme Corp"
        finally:
            if os.path.exists(result):
                os.unlink(result)

    def test_convert_empty_list(self):
        """Test that empty list raises ValueError wrapped in RuntimeError."""
        with pytest.raises(RuntimeError, match="No data items provided"):
            _convert_dicts_to_csv([])

    def test_convert_non_dict_items(self):
        """Test that non-dict items raise TypeError wrapped in RuntimeError."""
        with pytest.raises(RuntimeError, match="Expected list of dictionaries"):
            _convert_dicts_to_csv([1, 2, 3])

    def test_convert_dict_with_no_fields(self):
        """Test that dict with no fields raises ValueError wrapped in RuntimeError."""
        with pytest.raises(RuntimeError, match="no fields"):
            _convert_dicts_to_csv([{}])

    def test_convert_dicts_with_inconsistent_fields(self):
        """Test conversion with inconsistent fields (extrasaction='ignore')."""
        data = [
            {"Id": "001", "Name": "Test1", "Extra": "Value"},
            {"Id": "002", "Name": "Test2"},  # Missing 'Extra'
        ]

        result = _convert_dicts_to_csv(data)

        try:
            assert os.path.exists(result)
            # Should use fields from first dict
            with open(result, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                assert set(reader.fieldnames) == {"Id", "Name", "Extra"}
        finally:
            if os.path.exists(result):
                os.unlink(result)

    def test_convert_dicts_with_special_characters(self):
        """Test dicts with special characters requiring CSV escaping."""
        data = [
            {
                "Id": "001",
                "Name": "Test, Inc.",
                "Description": 'Contains "quotes" and commas, and\nnewlines',
            }
        ]

        result = _convert_dicts_to_csv(data)

        try:
            assert os.path.exists(result)
            # Verify proper escaping
            with open(result, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                row = next(reader)
                assert row["Name"] == "Test, Inc."
                assert "quotes" in row["Description"]
        finally:
            if os.path.exists(result):
                os.unlink(result)

    def test_convert_iterator_of_dicts(self):
        """Test conversion of iterator (should convert to list first)."""
        data_iter = iter([{"Id": "001", "Name": "Test1"}, {"Id": "002", "Name": "Test2"}])

        result = _convert_dicts_to_csv(data_iter)

        try:
            assert os.path.exists(result)
            df = pd.read_csv(result)
            assert len(df) == 2
        finally:
            if os.path.exists(result):
                os.unlink(result)


class TestCleanupTempFile:
    """Tests for cleanup_temp_file() function."""

    def test_cleanup_temp_file_in_system_temp(self):
        """Test successful cleanup of file in system temp directory."""
        # Create file in system temp dir
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, dir=tempfile.gettempdir()
        )
        temp_file.write("test")
        temp_file.close()

        assert os.path.exists(temp_file.name)
        assert temp_file.name.startswith(tempfile.gettempdir())

        cleanup_temp_file(temp_file.name)

        # Should be deleted
        assert not os.path.exists(temp_file.name)

    def test_cleanup_file_outside_temp_not_deleted(self):
        """Test that files OUTSIDE system temp directory are NOT deleted."""
        # Create file in current directory (not in system temp)
        test_file = Path.cwd() / "test_important_file.csv"
        test_file.write_text("important data")

        try:
            # This should NOT delete the file (safety check)
            cleanup_temp_file(str(test_file))

            # Verify file still exists
            assert test_file.exists(), "File outside system temp should not be deleted"
        finally:
            # Manual cleanup
            if test_file.exists():
                test_file.unlink()

    def test_cleanup_nonexistent_file(self):
        """Test cleanup of nonexistent file (should not raise)."""
        cleanup_temp_file("/tmp/nonexistent_file_12345.csv")
        # Should not raise any exception

    def test_cleanup_none(self):
        """Test cleanup with None (should not raise)."""
        cleanup_temp_file(None)
        # Should not raise

    def test_cleanup_empty_string(self):
        """Test cleanup with empty string (should not raise)."""
        cleanup_temp_file("")
        # Should not raise

    def test_cleanup_invalid_type(self):
        """Test cleanup with invalid type (should not raise)."""
        cleanup_temp_file(123)  # Integer
        cleanup_temp_file(["path"])  # List
        # Should not raise (safety check handles non-string)

    def test_cleanup_handles_permission_error(self):
        """Test that cleanup handles permission errors gracefully."""
        # Create a temp file
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, dir=tempfile.gettempdir()
        )
        temp_file.close()

        # Mock os.unlink to raise PermissionError
        with patch("os.unlink", side_effect=PermissionError("Cannot delete")):
            # Should not raise - fails silently
            cleanup_temp_file(temp_file.name)

        # Cleanup for real
        try:
            os.unlink(temp_file.name)
        except:  # noqa: E722
            pass


class TestDataProcessorEdgeCases:
    """Tests for edge cases and error handling."""

    def test_prepare_data_with_large_recordbatch(self):
        """Test processing large RecordBatch."""
        # Create larger dataset
        data = {
            "Id": [f"00{i:07d}" for i in range(1000)],
            "Name": [f"Record {i}" for i in range(1000)],
            "Amount": [float(i * 100) for i in range(1000)],
        }
        batch = pa.RecordBatch.from_pydict(data)

        result = prepare_data(batch)

        try:
            assert os.path.exists(result)
            df = pd.read_csv(result)
            assert len(df) == 1000
        finally:
            if os.path.exists(result):
                os.unlink(result)

    def test_prepare_data_unicode_characters(self):
        """Test data with unicode characters."""
        data = [
            {"Id": "001", "Name": "Test 日本語"},
            {"Id": "002", "Name": "Test עברית"},
            {"Id": "003", "Name": "Test العربية"},
        ]

        result = prepare_data(data)

        try:
            assert os.path.exists(result)
            df = pd.read_csv(result, encoding="utf-8")
            assert "日本語" in df.iloc[0]["Name"]
        finally:
            if os.path.exists(result):
                os.unlink(result)

    def test_file_path_validation_case_insensitive(self, temp_dir):
        """Test that CSV extension check is case-insensitive."""
        csv_file = temp_dir / "data.CSV"
        csv_file.write_text("Id,Name\n001,Test")

        # Should accept .CSV (uppercase)
        result = prepare_data(str(csv_file))
        assert result == str(csv_file)
