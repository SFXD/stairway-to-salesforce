"""
Unit tests for logger configuration.
"""

import pytest
from pathlib import Path
import tempfile
import logging
from unittest.mock import Mock, patch, MagicMock

from dlt_salesforce_advanced.utils.logger_config import (
    get_salesforce_logger,
    get_rejected_records_path,
)


class TestGetSalesforceLogger:
    """Tests for get_salesforce_logger()"""
    
    @patch('dlt_salesforce_advanced.utils.logger_config.get_dlt_logger')
    def test_get_logger_without_file(self, mock_get_dlt_logger):
        """Test getting logger without file logging."""
        mock_logger = Mock(spec=logging.Logger)
        mock_logger.name = "test_logger"
        mock_get_dlt_logger.return_value = mock_logger
        
        logger = get_salesforce_logger("test_logger")
        
        mock_get_dlt_logger.assert_called_once_with("test_logger")
        assert logger == mock_logger
    
    @patch('dlt_salesforce_advanced.utils.logger_config.get_dlt_logger')
    def test_get_logger_with_file(self, mock_get_dlt_logger, temp_dir):
        """Test getting logger with file logging."""
        mock_logger = Mock(spec=logging.Logger)
        mock_logger.name = "test_logger"
        mock_logger.handlers = []
        mock_get_dlt_logger.return_value = mock_logger
        
        log_dir = str(temp_dir)
        logger = get_salesforce_logger("test_logger", log_dir=log_dir)
        
        assert logger == mock_logger
        # Verify addHandler was called (file handler was added)
        assert mock_logger.addHandler.called
    
    @patch('dlt_salesforce_advanced.utils.logger_config.get_dlt_logger')
    def test_get_logger_with_log_level(self, mock_get_dlt_logger):
        """Test setting log level."""
        mock_logger = Mock(spec=logging.Logger)
        mock_logger.name = "test_logger"
        mock_get_dlt_logger.return_value = mock_logger
        
        logger = get_salesforce_logger("test_logger", log_level="DEBUG")
        
        # Verify setLevel was called with DEBUG
        mock_logger.setLevel.assert_called_once_with(logging.DEBUG)


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