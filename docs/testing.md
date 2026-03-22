# Testing

This page explains how to run, write, and organize tests for **Stairway to Salesforce**. We use `pytest` as the primary testing engine.

---

## Running Tests

### 1. Pipeline Tests
Runs integration tests that verify the complete data flow.
```bash
uv run --with pytest pytest tests/pipelines/ --cov-report=term
```

### 2. Framework Tests
Runs unit tests for internal components (drivers, sources, etc.).
```bash
uv run --with pytest pytest tests/unit/ --cov=stairway_to_salesforce --cov-report=term
```

### 3. Full Suite Execution
Runs the entire test suite with a coverage report.
```bash
uv run --with pytest pytest --cov=stairway_to_salesforce --cov-report=term
```

---

## Coverage Reports

To generate a detailed report in HTML format and open it in your browser:
```bash
uv run --with pytest pytest --cov=stairway_to_salesforce --cov-report=html
# Then open htmlcov/index.html
```

---

## Test Structure

The `tests/` directory is organized to separate unit logic from integration:

* **tests/pipelines/**: Integration tests for complete pipelines (Sync, Upsert, Delete).
* **tests/unit/**: Unit tests for individual components (Sources, Destinations, Key Resolver, Drivers).

---

## Writing Tests

### Testing a Pipeline
Here is how to test a pipeline using a lightweight destination like **DuckDB**.

```python
import pytest
from stairway_to_salesforce.components import BasePipeline

def test_account_sync_pipeline():
    pipeline = BasePipeline(
        pipeline_name="test_sync",
        environment="test"
    )
    
    # Configuration
    pipeline.source = mock_salesforce_source()
    pipeline.destination = "duckdb" # In-memory destination, very fast
    
    # Execution
    result = pipeline.run()
    
    # Assertions
    assert result.success
    assert result.record_count > 0
```

### Using Mocks
To avoid making actual calls to Salesforce APIs during unit tests, use `unittest.mock`.

```python
from unittest.mock import Mock, patch

@patch('simple_salesforce.Salesforce')
def test_salesforce_source(mock_sf):
    # Mock configuration
    mock_sf.return_value.bulk2.query.return_value = [
        {"Id": "001xxx", "Name": "Test Account"}
    ]
    
    source = get_sf_bulk2_source(sobject="Account")
    records = list(source)
    
    assert len(records) == 1
    assert records[0]["Name"] == "Test Account"
```

---

## Test Environment Configuration

It is highly recommended to create a dedicated section in your `.dlt/secrets.toml` file to ensure you never impact your development or production data.

```toml
[salesforce.test]
# Credentials for a test Sandbox or Scratch Org
client_id = "test_id"
client_secret = "test_secret"
username = "test@example.com.sandbox"

[postgres.test]
database = "test_db"
host = "localhost"
# ...
```

---

## Best Practices

1. **Isolation**: Each test must be independent of others.
2. **Speed**: Use **DuckDB** for pipeline tests; it is an in-memory database that requires no additional setup.
3. **Edge Cases**: Systematically test empty datasets, very large volumes, and API errors.
4. **Clean Up**: Ensure you delete test data or temporary pipelines after execution.

---

## Debugging

If a test fails, you can isolate the execution or enter debug mode:

```bash
# Run a specific test with details (-v)
uv run --with pytest pytest tests/unit/test_key_resolver.py -v

# Run with visible console output (-s)
uv run --with pytest pytest tests/unit/ -v -s
```

**Tip:** You can add `breakpoint()` anywhere in your test code to pause execution and inspect variables.