# Salesforce Driver - Unit Tests

This directory contains comprehensive unit tests for the Salesforce driver components.

## Test Files

### Credential Specifications
- **`test_sfdriver_specs.py`** (600+ lines)
  - Tests for all credential classes (SecurityTokenAuth, OrganizationIdAuth, etc.)
  - Configuration class tests (SalesforceDriverConfiguration)
  - Validation logic (InstanceAuth, JWTAuth validation)
  - Secret field handling
  - Proxy configuration
  - Edge cases and error conditions

### Driver Factory
- **`test_sfdriver_factory.py`** (650+ lines)
  - Credential resolution from various formats (dict, string path, objects)
  - Resolution priority order testing
  - Driver creation for all credential types
  - Integration with simple-salesforce
  - Custom configuration and session handling
  - Error handling and validation

### Cache Manager
- **`test_sfdriver_cache_manager.py`** (550+ lines)
  - Cache key generation (MD5 hashing)
  - Cache hit/miss scenarios
  - TTL (Time-To-Live) behavior
  - Cache eviction when full (maxsize=8)
  - Multi-environment caching
  - Cache invalidation
  - Thread safety considerations

### Main Driver Module
- **`test_sfdriver.py`** (500+ lines)
  - Public API testing (`get_salesforce_driver`)
  - String credentials with caching
  - Credential objects without caching
  - Integration with factory and cache
  - Error handling and propagation
  - Edge cases (unicode, empty strings)

## Architecture

The Salesforce driver is composed of four main modules:

```
sfdriver_specs.py         # Credential classes and configuration
       ↓
sfdriver_factory.py       # Credential resolution and driver creation
       ↓
sfdriver_cache_manager.py # TTL-based driver caching
       ↓
sfdriver.py               # Public API
```

## Supported Credential Types

1. **SecurityTokenAuth** - OAuth 2.0 Username-Password Flow with Security Token
   - Fields: `user_name`, `password`, `security_token`

2. **OrganizationIdAuth** - Trusted IP Ranges Authentication
   - Fields: `user_name`, `password`, `organization_id`

3. **InstanceAuth** - Direct Session Access
   - Fields: `session_id`, `instance` OR `instance_url`

4. **ConsumerKeySecretAuth** - OAuth 2.0 Username-Password Flow with Connected App
   - Fields: `user_name`, `password`, `consumer_key`, `consumer_secret`

5. **JWTAuth** - OAuth 2.0 JWT Bearer Flow
   - Fields: `user_name`, `consumer_key`, `privatekey` OR `privatekey_file`

6. **ConsumerKeySecretDomainAuth** - OAuth 2.0 Client Credentials Flow
   - Fields: `consumer_key`, `consumer_secret`, `domain`

## Running Tests

### Run all driver tests:
```bash
pytest tests/unit/drivers/ -v
```

### Run specific test file:
```bash
pytest tests/unit/drivers/test_sfdriver_specs.py -v
```

### Run specific test class:
```bash
pytest tests/unit/drivers/test_sfdriver_cache_manager.py::TestCacheManagerIntegration -v
```

### Run with coverage:
```bash
pytest tests/unit/drivers/ --cov=dlt_salesforce_advanced.drivers.salesforce_driver --cov-report=html
```

### Skip slow tests (TTL tests):
```bash
pytest tests/unit/drivers/ -v -m "not slow"
```

## Test Coverage

Target: **>95% code coverage** for driver modules

Current coverage areas:
- ✅ All credential class initialization and validation
- ✅ Credential resolution from all formats (dict, string, object)
- ✅ Driver creation for all credential types
- ✅ Cache operations (add, get, has, clear)
- ✅ Cache key generation and hashing
- ✅ TTL behavior and cache eviction
- ✅ Integration workflows
- ✅ Error handling and edge cases

## Key Testing Patterns

### 1. Testing Credential Classes
```python
def test_create_security_token_auth(self):
    creds = SecurityTokenAuth(
        user_name="test@example.com",
        password="test_password",
        security_token="test_token"
    )
    
    assert creds.user_name == "test@example.com"
    assert creds.password == "test_password"
    assert creds.security_token == "test_token"
```

### 2. Testing Credential Validation
```python
def test_instance_auth_requires_instance_or_url(self):
    creds = InstanceAuth(session_id="session")
    
    with pytest.raises(ConfigurationValueError, match="instance.*instance_url"):
        creds.on_resolved()
```

### 3. Testing Credential Resolution
```python
@patch('dlt.secrets')
def test_resolve_from_dlt_secrets_path(self, mock_secrets):
    mock_secrets.__getitem__.return_value = {...}
    
    result = resolve_salesforce_credentials("salesforce.dev")
    
    assert isinstance(result, SecurityTokenAuth)
```

### 4. Testing Driver Factory
```python
@patch('module.Salesforce')
def test_make_driver_security_token_auth(self, mock_sf_class):
    mock_sf_instance = Mock()
    mock_sf_class.return_value = mock_sf_instance
    
    result = make_salesforce_driver(creds, session=None, config=config)
    
    assert result == mock_sf_instance
    mock_sf_class.assert_called_once()
```

### 5. Testing Cache Behavior
```python
def test_cache_hit_returns_same_instance(self):
    cache_key = get_cache_key("salesforce.dev")
    mock_driver = Mock()
    
    add_driver_to_cache(cache_key, mock_driver)
    result = get_driver_from_cache(cache_key)
    
    assert result is mock_driver
```

## Cache Management

### Cache Configuration
- **Type**: TTLCache (from cachetools)
- **Max Size**: 8 drivers
- **TTL**: 3600 seconds (1 hour)
- **Eviction**: LRU (Least Recently Used)

### Cache Keys
Cache keys are MD5 hashes of the DLT secrets path:
```python
cache_key = hashlib.md5("salesforce.dev".encode()).hexdigest()
```

### When Cache is Used
- ✅ String credentials path: `get_salesforce_driver("salesforce.dev")`
- ❌ Credential objects: `get_salesforce_driver(SecurityTokenAuth(...))`

## Fixtures

Common fixtures are defined in `tests/conftest.py`:
- **`mock_security_token_credentials`** - Pre-configured SecurityTokenAuth
- **`mock_consumer_key_credentials`** - Pre-configured ConsumerKeySecretDomainAuth
- **`mock_salesforce_client`** - Mock Salesforce client
- **`temp_dir`** - Temporary directory for file operations

## Important Notes

### DLT Secrets Integration
The driver integrates with DLT's secrets management system. Tests mock `dlt.secrets` to avoid requiring actual secrets configuration.

### Simple Salesforce Integration
The driver wraps the `simple-salesforce` library. Tests mock the `Salesforce` class to avoid actual API connections.

### Cache Thread Safety
The TTLCache is **not thread-safe** by default. In production environments with concurrent access, consider adding locks around cache operations.

### TTL Expiration
Tests for TTL expiration are marked with `@pytest.mark.slow` since they require time delays. These can be skipped in fast test runs.

## Credential Resolution Priority

When resolving credentials from a dictionary, the factory uses this priority order:

1. **security_token** → SecurityTokenAuth
2. **organization_id** → OrganizationIdAuth
3. **session_id** → InstanceAuth
4. **privatekey/privatekey_file** → JWTAuth
5. **consumer_key + consumer_secret + domain** → ConsumerKeySecretDomainAuth
6. **consumer_key + consumer_secret + user_name** → ConsumerKeySecretAuth

## Adding New Tests

When adding new tests:

1. **Follow naming convention**: `test_<functionality>_<scenario>`
2. **Clear cache in setup**: Use `setup_method` to clear cache
3. **Mock external dependencies**: Don't make real Salesforce connections
4. **Test all credential types**: Ensure new features work with all auth types
5. **Test error conditions**: Include tests for validation errors
6. **Document thread safety**: Note any thread safety implications

## Common Testing Scenarios

### Testing Credential Type Detection
```python
def test_security_token_takes_priority(self):
    cred_dict = {
        "user_name": "test@example.com",
        "password": "password",
        "security_token": "token",
        "organization_id": "00D"  # Also present
    }
    
    result = resolve_salesforce_credentials(cred_dict)
    
    # Should be SecurityTokenAuth, not OrganizationIdAuth
    assert isinstance(result, SecurityTokenAuth)
```

### Testing Cache Invalidation
```python
def test_cache_invalidation_scenario(self):
    cache_key = get_cache_key("salesforce.dev")
    
    # Cache initial driver
    add_driver_to_cache(cache_key, old_driver)
    
    # Invalidate
    clear_cache("salesforce.dev")
    
    # Cache new driver
    add_driver_to_cache(cache_key, new_driver)
    
    assert get_driver_from_cache(cache_key) is new_driver
```

### Testing Driver Creation Pipeline
```python
@patch('module.Salesforce')
@patch('dlt.secrets')
def test_full_workflow_string_credentials(self, mock_secrets, mock_sf):
    mock_secrets.__getitem__.return_value = {...}
    mock_sf.return_value = Mock()
    
    # First call - creates and caches
    result1 = get_salesforce_driver("salesforce.dev")
    
    # Second call - uses cache
    result2 = get_salesforce_driver("salesforce.dev")
    
    assert result1 is result2
```

## Dependencies

Test dependencies (should be in `requirements-dev.txt`):
- `pytest>=7.0.0`
- `pytest-cov>=4.0.0`
- `pytest-mock>=3.10.0`
- `cachetools>=5.0.0` (production dependency)

## Continuous Integration

These tests are designed for CI/CD:
- No external Salesforce connections
- All dependencies mocked
- Fast execution (<10 seconds total)
- Deterministic results
- Cache cleared between tests

## Security Considerations

### Secret Field Handling
- Password and token fields use `TSecretStrValue` type
- DLT's secrets system handles secure storage
- Tests verify field types but don't test actual encryption

### Cache Security
- Cached drivers contain authenticated sessions
- TTL of 1 hour limits exposure window
- Cache is in-memory only (not persisted)

---

For questions or issues with tests, please refer to the main project documentation or create an issue in the repository.
