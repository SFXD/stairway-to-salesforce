"""
Unit tests for logger configuration.
"""

from pathlib import Path

from dlt_salesforce_advanced.utils.logger_config import (
    get_rejected_records_path,
)



class TestGetRejectedRecordsPath:
    """Tests for get_rejected_records_path()"""
    
    def test_get_path_default_dir(self):
        """Test getting path with default directory."""
        path = get_rejected_records_path(
            target_name="Account",
            job_id="750xx000000TEST",
            operation="insert"
        )
        
        assert isinstance(path, Path)
        assert "Account" in str(path)
        assert "insert" in str(path)
        assert "750xx000000TEST" in str(path)
        assert path.suffix == ".csv"
        assert ".dlt" in str(path)  # Should use default .dlt directory
    
    def test_get_path_custom_dir(self, temp_dir):
        """Test getting path with custom directory."""
        path = get_rejected_records_path(
            target_name="Contact",
            job_id="750xx000000TEST2",
            operation="upsert",
            output_dir=str(temp_dir)
        )
        
        assert temp_dir in path.parents or str(temp_dir) in str(path)
        assert "Contact" in str(path)
        assert "upsert" in str(path)
        assert "750xx000000TEST2" in str(path)