"""
Unit tests for Salesforce destination data processor.
"""

import pytest
from unittest.mock import Mock, patch
import tempfile
import os
from pathlib import Path
import pyarrow as pa

from dlt_salesforce_advanced.destinations.salesforce_bulk2.data_processor import (
    prepare_data,
    cleanup_temp_file,
    _convert_recordbatch_to_csv,
    _convert_dicts_to_csv,
)


class TestPrepareData:
    """Tests for prepare_data()"""
    
    def test_prepare_data_from_file_path(self, temp_csv_file):
        """Test prepare_data with existing CSV file."""
        result = prepare_data(temp_csv_file)
        
        assert result == temp_csv_file
        assert os.path.exists(result)
    
    def test_prepare_data_from_path_object(self, temp_csv_file):
        """Test prepare_data with Path object."""
        path_obj = Path(temp_csv_file)
        result = prepare_data(path_obj)
        
        assert result == str(temp_csv_file)
    
    def test_prepare_data_nonexistent_file(self):
        """Test that nonexistent file raises error."""
        with pytest.raises(ValueError, match="File does not exist"):
            prepare_data("/nonexistent/file.csv")
    
    def test_prepare_data_non_csv_file(self, temp_dir):
        """Test that non-CSV file raises error."""
        txt_file = temp_dir / "data.txt"
        txt_file.write_text("test")
        
        with pytest.raises(ValueError, match="must be CSV format"):
            prepare_data(str(txt_file))
    
    def test_prepare_data_from_dicts(self, sample_account_data):
        """Test prepare_data with list of dicts."""
        result = prepare_data(sample_account_data)
        
        try:
            assert os.path.exists(result)
            assert result.endswith('.csv')
            
            with open(result, 'r') as f:
                content = f.read()
                assert "001xx000000001" in content
                assert "Acme Corp" in content
        finally:
            if os.path.exists(result):
                os.unlink(result)
    
    def test_prepare_data_from_recordbatch(self):
        """Test prepare_data with PyArrow RecordBatch."""
        data = {
            'Id': ['001xx000000001', '001xx000000002'],
            'Name': ['Acme Corp', 'Global Industries']
        }
        batch = pa.RecordBatch.from_pydict(data)
        
        result = prepare_data(batch)
        
        try:
            assert os.path.exists(result)
            assert result.endswith('.csv')
            
            with open(result, 'r') as f:
                content = f.read()
                assert "Acme Corp" in content
        finally:
            if os.path.exists(result):
                os.unlink(result)
    
    def test_prepare_data_empty_list(self):
        """Test that empty list raises error."""
        # FIX: Expect RuntimeError, not ValueError (wrapped by implementation)
        with pytest.raises(RuntimeError, match="No data items provided"):
            prepare_data([])


class TestConvertRecordbatchToCsv:
    """Tests for _convert_recordbatch_to_csv()"""
    
    def test_convert_recordbatch_success(self):
        """Test successful RecordBatch conversion."""
        data = {
            'Id': ['001xx000000001', '001xx000000002'],
            'Name': ['Test 1', 'Test 2']
        }
        batch = pa.RecordBatch.from_pydict(data)
        
        result = _convert_recordbatch_to_csv(batch)
        
        try:
            assert os.path.exists(result)
            
            with open(result, 'r') as f:
                content = f.read()
                assert "Id,Name" in content or "Name,Id" in content
                assert "Test 1" in content
        finally:
            if os.path.exists(result):
                os.unlink(result)
    
    def test_convert_empty_recordbatch(self):
        """Test that empty RecordBatch raises error."""
        schema = pa.schema([('Id', pa.string()), ('Name', pa.string())])
        batch = pa.RecordBatch.from_arrays([pa.array([]), pa.array([])], schema=schema)
        
        # FIX: Expect RuntimeError, not ValueError
        with pytest.raises(RuntimeError, match="contains no data"):
            _convert_recordbatch_to_csv(batch)


class TestConvertDictsToCsv:
    """Tests for _convert_dicts_to_csv()"""
    
    def test_convert_dicts_success(self, sample_account_data):
        """Test successful dict conversion."""
        result = _convert_dicts_to_csv(sample_account_data)
        
        try:
            assert os.path.exists(result)
            
            with open(result, 'r') as f:
                content = f.read()
                assert "Id,Name" in content or "Name,Id" in content
                assert "Acme Corp" in content
        finally:
            if os.path.exists(result):
                os.unlink(result)
    
    def test_convert_empty_list(self):
        """Test that empty list raises error."""
        # FIX: Expect RuntimeError
        with pytest.raises(RuntimeError, match="No data items provided"):
            _convert_dicts_to_csv([])
    
    def test_convert_non_dict_items(self):
        """Test that non-dict items raise error."""
        # FIX: Expect RuntimeError
        with pytest.raises(RuntimeError, match="Expected list of dictionaries"):
            _convert_dicts_to_csv([1, 2, 3])
    
    def test_convert_dict_with_no_fields(self):
        """Test that dict with no fields raises error."""
        # FIX: Expect RuntimeError
        with pytest.raises(RuntimeError, match="no fields"):
            _convert_dicts_to_csv([{}])


class TestCleanupTempFile:
    """Tests for cleanup_temp_file()"""
    
    def test_cleanup_temp_file_success(self):
        """Test successful cleanup of temp file."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        temp_file.write("test")
        temp_file.close()
        
        assert os.path.exists(temp_file.name)
        
        cleanup_temp_file(temp_file.name)
        
        assert not os.path.exists(temp_file.name)
    
    def test_cleanup_non_temp_file(self):
        """Test that files OUTSIDE system temp directory are not deleted."""
        # Create a file in current working directory (definitely not in temp)
        test_file = Path.cwd() / "test_important_file.csv"
        test_file.write_text("important data")
        
        try:
            # This file path does NOT start with tempfile.gettempdir()
            # So cleanup_temp_file should NOT delete it
            cleanup_temp_file(str(test_file))
            
            # Verify file still exists (because it's not in system temp dir)
            assert test_file.exists(), "File outside system temp dir should not be deleted"
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
    
    def test_cleanup_file_in_system_temp(self):
        """Test that files IN system temp directory ARE deleted."""
        import tempfile as tf
        
        # Create file specifically in system temp directory
        temp_file = tf.NamedTemporaryFile(mode='w', delete=False, dir=tf.gettempdir())
        temp_file.write("test")
        temp_file.close()
        
        assert os.path.exists(temp_file.name)
        assert temp_file.name.startswith(tf.gettempdir())
        
        # This SHOULD be deleted
        cleanup_temp_file(temp_file.name)
        
        # Verify it was deleted
        assert not os.path.exists(temp_file.name)
    
    def test_cleanup_nonexistent_file(self):
        """Test cleanup of nonexistent file (should not raise)."""
        cleanup_temp_file("/nonexistent/file.csv")  # Should not raise
    
    def test_cleanup_none(self):
        """Test cleanup with None (should not raise)."""
        cleanup_temp_file(None)  # Should not raise
    
    def test_cleanup_empty_string(self):
        """Test cleanup with empty string (should not raise)."""
        cleanup_temp_file("")  # Should not raise