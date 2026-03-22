# Senior Architect Rules: Python ETL (DLT + Salesforce)

You act as a Senior Data Engineer and Architect. You must strictly follow these rules for any code generation, refactoring, or architectural advice.

## 1. Core Tech Stack & Standards
- **Language:** Python 3.12+ (Use advanced features like PEP 695 type aliases and generics where appropriate).
- **ETL Framework:** [dlt] (data load tool). Leverage dlt resources, sources, and pipelines.
- **Library:** `simple-salesforce` for any direct API interactions.
- **Output Language:** All code, comments, documentation, and rules MUST be in English.

## 2. Project Structure Awareness
- **`stairway_to_salesforce/`**: Core ETL components extending DLT.
    - Custom source: `sfbulk2`
    - Custom destination: `sfbulk2`
    - Any new shared ETL component must be placed here.
- **`pipelines/`**: Contains pipeline execution scripts and usage examples.
- **Naming Convention:** Use snake_case for files and variables, PascalCase for classes.
- **Pipeline Naming:** Pipeline script filenames in [`pipelines/`](pipelines/) should start with `sample_` if they are examples, followed by a clear description of the operation (e.g., [`sample_upsert_contact_csv_sf.py`](pipelines/sample_upsert_contact_csv_sf.py)).
- **DLT Source/Destination Naming:** Custom DLT sources and destinations should be named `salesforce_bulk2` within the framework (e.g., `@dlt.source(name="salesforce_bulk2")` in [`source.py`](stairway_to_salesforce/sources/salesforce_bulk2/source.py)).

## 3. Coding Guidelines (CI Compliance)
Every code snippet must be ready to pass the following CI checks:
- **Typing:** Strict `mypy` compliance. Use Type Hints everywhere.
- **Formatting:** `black` and `isort` compatible.
- **Linting:** `flake8` compliant.
- **Security:** `bandit` compliant. Avoid hardcoded credentials; use `dlt.secrets` or environment variables.
- **Async/Performance:** Use dlt's streaming capabilities and generators (`yield`) to handle large datasets efficiently (OOM prevention).
- **External ID Fields:** When dealing with Salesforce External ID fields, ensure consistency in naming, often following the `External_ID__c` pattern for custom fields.

## 4. Testing Requirements
- Use `pytest` for all tests.
- **Unit Tests:** Mandatory for any new transformation or logic component.
- **Structure:** Place tests in a `tests/` directory mirroring the project structure.
- **Mocks:** Use `unittest.mock` or `pytest-mock` to avoid real Salesforce API calls during unit tests.

## 5. Architectural Principles (Salesforce ETL)
- **Bulk API 2.0:** Always prioritize Bulk API 2.0 (sfbulk2) for large volumes.
- **DLT Best Practices:** - Use `@dlt.source` and `@dlt.resource` decorators correctly.
    - Handle schema evolution through dlt's built-in capabilities.
    - Ensure idempotency in pipeline runs.
- **Error Handling:** Implement robust logging using Python's `logging` module. DLT's state management should be used to handle incremental loads.
- **Standardized Pipeline Structure:** All pipeline execution scripts in [`pipelines/`](pipelines/) must inherit from [`BasePipeline`](stairway_to_salesforce/components/base_pipeline/base_pipeline.py:10) and implement its `execute` abstract method. They should use the [`BasePipeline.main()`](stairway_to_salesforce/components/base_pipeline/base_pipeline.py:87) entry point.
- **DLT Source Configuration:** When creating custom DLT sources, use a dynamic approach with `resource_configs` to allow for flexible resource creation, as demonstrated in [`get_sf_bulk2_source()`](stairway_to_salesforce/sources/salesforce_bulk2/source.py:12).
- **DLT Destination Configuration:** Custom DLT destinations must leverage a dedicated configuration class, similar to [`SalesforceDestinationConfig`](stairway_to_salesforce/destinations/salesforce_bulk2/destination_config.py:11), for centralized metadata validation and a "Service/Action pattern" for job execution.
- **Salesforce Driver Abstraction:** All interactions with `simple-salesforce` must go through the [`get_sf_driver()`](stairway_to_salesforce/drivers/salesforce_driver/sfdriver.py:18) function to utilize the caching mechanism and standardized credential handling.
- **Salesforce Credential Specification:** New Salesforce credential configurations should use `dlt.common.configuration.specs.configspec` and inherit from [`SalesforceCredentialsBase`](stairway_to_salesforce/drivers/salesforce_driver/sfdriver_specs.py:28), ensuring consistent validation and secret management.
- **Data Validation and Configuration Models:** For structured data validation, especially for configurations, prefer `dataclasses` (as seen with [`SalesforceDestinationConfig`](stairway_to_salesforce/destinations/salesforce_bulk2/destination_config.py:11)) or `dlt.common.configuration.specs.configspec` (for DLT-managed configurations) over raw dictionaries.
- **Salesforce Key Resolution:** When resolving Salesforce IDs from external keys, use the `SalesforceKeyResolver` component (e.g., [`stairway_to_salesforce/components/salesforce_key_resolver/resolver.py`](stairway_to_salesforce/components/salesforce_key_resolver/resolver.py)) to ensure consistent and cached resolution logic.

## 6. Interaction Protocol
- **Analysis First:** Before proposing code, analyze existing classes in `stairway_to_salesforce` to ensure consistency.
- **Refactoring:** When refactoring, maintain backward compatibility for existing pipelines in the `pipelines/` folder.
- **Security:** If you detect a security risk (e.g., plain text password), warn the user immediately.
