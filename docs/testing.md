# Testing
This page explains how to run, write, and organize tests for **Stairway to Salesforce**. We distinguish between **Framework Tests** (internal logic) and **Pipeline Tests** (data flow validation).

## 1. Pipeline Testing (User Focus)
Pipeline tests are integration tests. They verify that your data correctly travels from your source to Salesforce (or vice-versa). These tests require a live connection to a Salesforce Sandbox or Scratch Org.

**How to run**
Since these are functional scripts, you can run them directly using uv:

```bash
#Run a specific sample or custom pipeline using the test environment
uv run pipelines/sample01_upsert_account_csv_sf.py --env test
```

**Where to store them**
Location: /pipelines/

Best Practice: Create scripts prefixed with test_ or use the existing samples to validate your connectivity and mapping logic.

## 2. Framework Testing (Contributor Focus)
Framework tests are unit tests. They verify the internal components of the library (Drivers, Sources, Resolvers) using Mocks. They do not require a Salesforce connection and are extremely fast.

**How to run**
We recommend using the provided Makefile for simplicity:

```bash
make check-test
```

Run a specific sample or custom pipeline using the test environment
```bash
uv run pytest stairway_to_salesforce/tests/ --cov=stairway_to_salesforce --cov-report=term
```

**Where to store them**
- **Location**: stairway_to_salesforce/tests/
- **Requirement**: Every new component or bug fix in the core package must include a corresponding unit test in this directory.

## Test Environment Configuration
To avoid polluting your production data, always use a dedicated test environment in your .dlt/secrets.toml:

```toml
[salesforce.test]
auth_type = "client_credentials"
instance_url = "https://your-sandbox.my.salesforce.com"
client_id = "your_test_client_id"
client_secret = "your_test_client_secret"
```

## Coverage Reports
To identify untested parts of the framework, you can generate an HTML coverage report:

```bash
uv run pytest stairway_to_salesforce/tests/ --cov=stairway_to_salesforce --cov-report=html

#Then open htmlcov/index.html in your browser
```

## Best Practices
1. **Mock External Calls**: Framework tests should never hit the real Salesforce API. Use unittest.mock or pytest-mock.
2. **Environment Isolation**: Always use the --env test flag when running integration pipelines.
3. **Clean Up**: If your pipeline test creates data in Salesforce, ensure your script includes a cleanup step or use a disposable Scratch Org.
4. **Pre-commit**: Contributors should run make check-all before pushing code to ensure no regression was introduced.

## Debugging
If a test fails, you can use standard pytest flags to get more context:

```bash
#-v: Verbose, -s: Show print statements, -x: Stop at first failure
uv run pytest stairway_to_salesforce/tests/ -v -s -x
```
