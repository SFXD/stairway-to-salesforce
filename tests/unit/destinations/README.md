# Salesforce Bulk API v2 Destination - Unit Tests

This directory contains comprehensive unit tests for the Salesforce Bulk API v2 destination.

## Test Files

### Core Configuration & Validation
- **`test_destination_config.py`** - Tests for `SalesforceDestinationConfig` class
  - Configuration parsing from DLT table schemas
  - Validation of write dispositions and operations
  - Primary key extraction and handling
  - Edge cases and error conditions

### Data Processing
- **`test_data_processor.py`** - Tests for data conversion to CSV
  - File path handling
  - PyArrow RecordBatch conversion
  - Dictionary list conversion
  - Temporary file cleanup
  - Unicode and special character handling

### Operations
- **`test_operations_common.py`** - Tests for common operation utilities
  - `get_bulk_client()` - Client retrieval and validation
  - `process_results()` - Job result processing and error handling
  - `_save_rejected_records()` - Failed record persistence

- **`test_operations.py`** - Tests for individual operations
  - `exec_insert()` - Insert operation
  - `exec_upsert()` - Upsert with external IDs
  - `exec_delete()` - Delete with ID resolution
  - `exec_replace()` - Replace (query + delete + insert)

### Job Execution
- **`test_job_executor.py`** - Tests for job dispatch router
  - Operation routing to correct handlers
  - Parameter passing and validation
  - Error handling and propagation

### Integration
- **`test_destination.py`** - Tests for main destination module
  - Full workflow integration
  - Component interaction
  - Error handling and cleanup
  - Configuration validation

## Running Tests

### Run all destination tests:
```bash
pytest tests/unit/destinations/ -v
```

### Run specific test file:
```bash
pytest tests/unit/destinations/test_data_processor.py -v
```

### Run with coverage:
```bash
pytest tests/unit/destinations/ --cov=dlt_salesforce_advanced.destinations.salesforce_bulk2 --cov-report=html
```

## Test Structure

Each test file follows this structure:
1. **Imports** - Standard imports and module imports
2. **Test Classes** - Grouped by functionality
3. **Test Methods** - Individual test cases with descriptive names
4. **Edge Cases** - Dedicated classes for edge cases and error conditions

## Fixtures

Common fixtures are defined in `tests/conftest.py`:
- **Credentials**: `mock_security_token_credentials`, `mock_consumer_key_credentials`
- **Clients**: `mock_salesforce_client`, `mock_bulk2_client`, `mock_salesforce_with_bulk2`
- **Data**: `sample_account_data`, `sample_csv_data`, `sample_field_mapping`
- **Files**: `temp_csv_file`, `temp_dir`
- **Results**: `successful_job_result`, `failed_job_result`, `partial_success_job_result`

## Key Testing Patterns

### 1. Mocking External Dependencies
```python
@patch('module.function')
def test_something(self, mock_function):
    mock_function.return_value = expected_value
    # Test logic
```

### 2. Testing Error Conditions
```python
def test_invalid_input(self):
    with pytest.raises(ValueError, match="expected error message"):
        function_under_test(invalid_input)
```

### 3. Verifying Mock Calls
```python
mock_function.assert_called_once_with(expected_args)
assert mock_function.call_count == 2
```

### 4. Testing Cleanup with Finally Blocks
```python
try:
    # Test logic
finally:
    if temp_file.exists():
        temp_file.unlink()
```

## Coverage Goals

Target: **>90% code coverage** for the destination module

Current coverage areas:
- ✅ Configuration validation
- ✅ Data processing and conversion
- ✅ All CRUD operations (insert, upsert, delete, replace)
- ✅ Error handling and logging
- ✅ Temporary file management
- ✅ Integration workflows

## Important Notes

### DLT Destination Decorator
The `@dlt.destination` decorator makes direct function testing challenging. Tests for `destination.py` focus on:
- Configuration validation logic
- Component integration
- Error handling
- Cleanup behavior

### External ID Resolution
Tests for delete operations include scenarios with:
- Salesforce IDs (direct deletion)
- External IDs (resolution required)
- Failed resolution handling

### Temporary Files
All tests that create temporary files include cleanup in `finally` blocks to prevent test pollution.

### Async Operations
Salesforce Bulk API operations are synchronous in these tests. Real API calls are mocked.

## Adding New Tests

When adding new tests:

1. **Follow naming convention**: `test_<functionality>_<scenario>`
2. **Use descriptive docstrings**: Explain what the test validates
3. **Group related tests**: Use test classes to organize
4. **Mock external dependencies**: Don't make real Salesforce API calls
5. **Clean up resources**: Use finally blocks for file cleanup
6. **Test edge cases**: Include tests for error conditions
7. **Use fixtures**: Reuse common test data from conftest.py

## Common Testing Scenarios

### Testing with CSV Files
```python
def test_with_csv(self, temp_csv_file):
    result = function_that_uses_csv(temp_csv_file)
    assert result is not None
```

### Testing Error Propagation
```python
@patch('module.dependency')
def test_error_propagation(self, mock_dep):
    mock_dep.side_effect = RuntimeError("Original error")
    
    with pytest.raises(RuntimeError, match="Original error"):
        function_under_test()
```

### Testing Cleanup on Error
```python
@patch('module.cleanup_function')
@patch('module.main_function')
def test_cleanup_on_error(self, mock_main, mock_cleanup):
    mock_main.side_effect = Exception("Error")
    
    try:
        function_under_test()
    except:
        pass
    
    mock_cleanup.assert_called_once()
```

## Dependencies

Test dependencies (should be in `requirements-dev.txt`):
- `pytest>=7.0.0`
- `pytest-cov>=4.0.0`
- `pytest-mock>=3.10.0`

## Continuous Integration

These tests are designed to run in CI/CD pipelines:
- No external Salesforce connections required
- All dependencies mocked
- Fast execution (<30 seconds total)
- Deterministic results

---

For questions or issues with tests, please refer to the main project documentation or create an issue in the repository.
