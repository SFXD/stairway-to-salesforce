# Salesforce Bulk API v2 Source

Dynamic, configuration-driven Salesforce data extraction using Bulk API v2.

## Module Structure

- **`source.py`**: Main entry point - defines the `salesforce_bulk2_source()` function
- **`resource_builder.py`**: DLT resource creation and configuration validation
- **`query_builder.py`**: SOQL query construction, security validation, and data fetching
- **`../../drivers/salesforce_driver.py`**: Authentication and Salesforce client management

## Security

All SOQL injection prevention and validation is handled in `query_builder.py`:
- Field name sanitization
- Object name validation
- Query filter validation
- Value escaping and formatting

## Usage

See the main README for usage examples.