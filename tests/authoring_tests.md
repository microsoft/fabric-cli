# Test Data Setup

This document provides instructions for setting up the test environment and configuring test data for the Fabric CLI test suite.

## Test Execution Modes

The Fabric CLI test suite can run in two modes:

- **Live Mode**: Tests make actual HTTP requests to Microsoft Fabric APIs. The values needed for these API calls are injected into the tests via environment variables. When no command-line flag is specified, tests run in live mode and will record new cassettes.  Use the `--record` flag to run tests in this mode.

    For example, to run 'cd' command tests in live mode: 
    `python3 -m pytest tests/test_commands/test_cd.py --record`

    Test Recording Privacy Notice:
    Before creating a PR with test recordings ensure NO private information is visible in your recordings.
    If private data is accidentally recorded, mask or mock the private data using test processor.

- **Playback Mode**: Tests use pre-recorded VCR.py cassettes without making real API calls or requiring actual Fabric resources. This is the default mode.

    For example, to run 'cd' command tests in playback (default) mode:
    `python3 -m pytest tests/test_commands/test_cd.py`

## Available Test Environment Variables

When running tests in **live mode**, the tests perform real requests to Microsoft Fabric and Azure services.

**Important:** To minimize the risk of affecting actual resources, you should use **mock/placeholder values whenever possible** and only use actual resource IDs when the test specifically requires real resources to function correctly. Most tests can work with mock values that follow the correct format (e.g., valid GUIDs, proper naming conventions).

**Use actual resource values only when:**
- The test needs to validate real API responses
- The test involves operations that require existing resources
- Mock values cause authentication or authorization failures

For most testing scenarios, the mock values provided in [`static_test_data.py`](../tests/test_commands/data/static_test_data.py:24) are sufficient and should be preferred to avoid unintended modifications to production resources.

## Supported Test Environment Variables

### User Authentication

| Variable | Description | Purpose |
|----------|-------------|---------|
| `FABRIC_CLI_TEST_ADMIN_UPN` | Admin user UPN/email | Admin user email/UPN for admin operations |
| `FABRIC_CLI_TEST_ADMIN_ID` | Admin user GUID | Admin user GUID for admin operations |
| `FABRIC_CLI_TEST_USER_UPN` | Regular user UPN/email | Regular user email/UPN for access control tests |
| `FABRIC_CLI_TEST_USER_ID` | Regular user GUID | Regular user GUID for access control tests |

### Service Principal

| Variable | Description | Purpose |
|----------|-------------|---------|
| `FABRIC_CLI_TEST_SERVICE_PRINCIPAL_ID` | Service Principal GUID | Service principal GUID for app-based authentication |

### Capacity

| Variable | Description | Purpose |
|----------|-------------|---------|
| `FABRIC_CLI_TEST_CAPACITY_ID` | Fabric Capacity GUID | Fabric capacity GUID for capacity management tests |
| `FABRIC_CLI_TEST_CAPACITY_NAME` | Fabric Capacity name | Capacity name for capacity operations |

### Labels

| Variable | Description | Purpose |
|----------|-------------|---------|
| `FABRIC_CLI_TEST_NON_BUSINESS_LABEL_ID` | Non-Business label GUID | Non-Business label GUID for labeling tests |
| `FABRIC_CLI_TEST_PROTECTED_LABEL_ID` | Protected label GUID | Protected label GUID for labeling tests |

### Azure Resources

| Variable | Description | Purpose |
|----------|-------------|---------|
| `FABRIC_CLI_TEST_AZURE_SUBSCRIPTION_ID` | Azure Subscription GUID | Azure subscription GUID for Azure integration tests |
| `FABRIC_CLI_TEST_AZURE_RESOURCE_GROUP` | Azure Resource Group name | Resource group name for Azure operations |
| `FABRIC_CLI_TEST_AZURE_LOCATION` | Azure Location/Region | Azure region/location |

### SQL Server

| Variable | Description | Purpose |
|----------|-------------|---------|
| `FABRIC_CLI_TEST_SQL_SERVER` | SQL Server name | SQL Server name for database connection tests |
| `FABRIC_CLI_TEST_SQL_DATABASE` | SQL Database name | Database name for SQL operations |

### Virtual Network

| Variable | Description | Purpose |
|----------|-------------|---------|
| `FABRIC_CLI_TEST_VNET_NAME` | VNet name | Virtual network name for network-related tests |
| `FABRIC_CLI_TEST_VNET_SUBNET` | VNet subnet name | Subnet name for network configuration tests |

### Credential Details

| Variable | Description | Purpose |
|----------|-------------|---------|
| `FABRIC_CLI_TEST_CREDENTIAL_DETAILS_USERNAME` | Username for Connection credential details | Username for Connection creation tests |
| `FABRIC_CLI_TEST_CREDENTIAL_DETAILS_PASSWORD` | Password for Connection  credentialdetails | Password for Connection creation tests|

### Mock vs. Actual Values - Best Practices

| Resource Type | Recommended Approach | Example Mock Value | When to Use Actual |
|---------------|---------------------|-------------------|-------------------|
| **User IDs** | Use mock GUIDs | `00000000-0000-0000-0000-000000000001` | When testing user-specific permissions |
| **Capacity IDs** | Use mock GUIDs | `00000000-0000-0000-0000-000000000004` | When testing capacity assignment operations |
| **Workspace Names** | Use mock names | `mocked_fabriccli_capacity_name` | When testing workspace creation/deletion |
| **Azure Resources** | Use mock names/IDs | `mocked_fabriccli_resource_group` | When testing Azure integration features |
| **SQL Credentials** | Use mock credentials | `mocked_sql_server_server` | When testing actual database connections |

**Example of mock-first approach:**
```powershell
# Start with mock values (these work for most tests)
$env:FABRIC_CLI_TEST_CAPACITY_ID="00000000-0000-0000-0000-000000000004"
$env:FABRIC_CLI_TEST_CAPACITY_NAME="mocked_fabriccli_capacity_name"

# Only set actual values if tests fail with authentication errors
# $env:FABRIC_CLI_TEST_CAPACITY_ID="actual-capacity-guid-here"
# $env:FABRIC_CLI_TEST_CAPACITY_NAME="your-real-capacity-name"
```

## Environment Variable Requirements by Mode

### Playback Mode

When running tests in **playback mode**, you do not need to set any environment variables since the tests use pre-recorded responses instead of making real API calls. The test framework automatically provides mock values for all required variables.

### Live Mode

In **live mode**, you only need to set the subset of environment variables that are required for the specific tests you plan to run. The troubleshooting section below explains how to identify which variables are required for your tests.

**Recommended approach:**
1. Start with mock/placeholder values that follow the correct format
2. Only use actual resource IDs if tests fail due to authentication or resource validation issues
3. Use the troubleshooting section to identify missing variables when tests fail

## Security Considerations

- **Never commit real environment variables** to version control

## Implementation Details

During initialization, the system attempts to read environment variables to setup test data and uses helpful placeholder values when variables are missing.
For complete implementation details, see [`tests/test_commands/data/static_test_data.py`](../tests/test_commands/data/static_test_data.py).

## Complete Environment Variables and Mock Values Reference

This section provides a comprehensive reference of all environment variables used in the test suite and their corresponding mock values. The system automatically uses mock values when environment variables are not set, making it easy to run tests without extensive setup.

### Environment Variable Mapping

The [`get_env_with_default()`](../tests/test_commands/data/static_test_data.py:222) function is used to retrieve environment variables, returning a helpful placeholder format `<Missing VARIABLE_NAME value>` when variables are unset.

### Environment Setup Examples

#### Minimal Setup (Mock Values Only)
No environment variables needed - tests will use mock values automatically.

#### Live Mode with Custom Values
```powershell
# Set only the variables needed for your specific tests
$env:FABRIC_CLI_TEST_CAPACITY_ID="your-actual-capacity-guid"
$env:FABRIC_CLI_TEST_ADMIN_UPN="admin@yourdomain.com"
```

#### Complete Environment Setup
```powershell
# User authentication
$env:FABRIC_CLI_TEST_ADMIN_UPN = "admin@mockdomain.com"
$env:FABRIC_CLI_TEST_ADMIN_ID = "mock-admin-guid"
$env:FABRIC_CLI_TEST_USER_UPN = "user@mockdomain.com"
$env:FABRIC_CLI_TEST_USER_ID = "mock-user-guid"

# Service principal
$env:FABRIC_CLI_TEST_SERVICE_PRINCIPAL_ID = "mock-sp-guid"

# Capacity
$env:FABRIC_CLI_TEST_CAPACITY_ID = "mock-capacity-guid"
$env:FABRIC_CLI_TEST_CAPACITY_NAME = "mock-capacity-name"

# Labels (if using label tests)
$env:FABRIC_CLI_TEST_NON_BUSINESS_LABEL_ID = "mock-non-business-label-guid"
$env:FABRIC_CLI_TEST_PROTECTED_LABEL_ID = "mock-protected-label-guid"

# Azure resources
$env:FABRIC_CLI_TEST_AZURE_SUBSCRIPTION_ID = "mock-subscription-guid"
$env:FABRIC_CLI_TEST_AZURE_RESOURCE_GROUP = "mock-resource-group"
$env:FABRIC_CLI_TEST_AZURE_LOCATION = "eastus"

# SQL Server (if needed)
$env:FABRIC_CLI_TEST_SQL_SERVER = "mock-sql-server"
$env:FABRIC_CLI_TEST_SQL_DATABASE = "mock-database"

# Virtual network (if needed)
$env:FABRIC_CLI_TEST_VNET_NAME = "mock-vnet"
$env:FABRIC_CLI_TEST_VNET_SUBNET = "mock-subnet"

# Credentials (if needed)
$env:FABRIC_CLI_TEST_CREDENTIAL_DETAILS_USERNAME = "mock-username"
$env:FABRIC_CLI_TEST_CREDENTIAL_DETAILS_PASSWORD = "mock-password"
```

## Troubleshooting

### Missing Environment Variables

When running tests in **live mode** or **record mode**, if environment variables are missing or empty, the system will use clearly identifiable placeholder values instead of empty strings. This makes it much easier to identify the root cause when tests fail due to missing configuration.

#### Error Indicators in Logs
If a test fails and you see the following format in the log output:
```
<Missing FABRIC_CLI_TEST_... value>
```

This indicates that the test is expecting a specific environment variable to be set, but you haven't configured it.

**Examples of missing variable indicators:**
- `<Missing FABRIC_CLI_TEST_ADMIN_UPN value>`
- `<Missing FABRIC_CLI_TEST_CAPACITY_ID value>`
- `<Missing FABRIC_CLI_TEST_SQL_SERVER value>`
- etc.

#### Resolution Steps
When you encounter these placeholders in test failures:

1. **Identify the missing variable**: The placeholder shows exactly which environment variable needs to be set
2. **Set the environment variable**: Configure the missing variable with a valid value for your test environment
3. **Re-run the test**: After setting the variable, run the test again
