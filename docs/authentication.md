# Salesforce Authentication Flows

**Stairway to Salesforce** natively supports all standard Salesforce authentication methods thanks to the **dlt** configuration engine.

---

## Configuration by Auth Flow

=== "Client Credentials"
    This is the most modern and recommended method for server-to-server integrations.
    
    ::: stairway_to_salesforce.drivers.salesforce_driver.specs.ConsumerKeySecretDomainAuth
        options:
          show_root_heading: false
          show_source: false

=== "JWT Bearer"
    Ideal for maximum security without storing passwords, using a private key to sign requests.

    ::: stairway_to_salesforce.drivers.salesforce_driver.specs.JWTAuth
        options:
          show_root_heading: false
          show_source: false

=== "Username & Password"
    The classic OAuth 2.0 flow using a Connected App and standard user credentials.

    ::: stairway_to_salesforce.drivers.salesforce_driver.specs.ConsumerKeySecretAuth
        options:
          show_root_heading: false
          show_source: false

=== "Security Token"
    Used for simple connections without creating a Connected App (not recommended for production).

    ::: stairway_to_salesforce.drivers.salesforce_driver.specs.SecurityTokenAuth
        options:
          show_root_heading: false
          show_source: false

=== "Trusted IP / Org ID"
    Useful if your server's IP address is already allowlisted (trusted) within your Salesforce organization.

    ::: stairway_to_salesforce.drivers.salesforce_driver.specs.OrganizationIdAuth
        options:
          show_root_heading: false
          show_source: false

=== "Direct Session"
    Used to reuse an existing `access_token` or `session_id` directly.

    ::: stairway_to_salesforce.drivers.salesforce_driver.specs.InstanceAuth
        options:
          show_root_heading: false
          show_source: false

---

## How does dlt choose the right flow?

The framework uses a **Factory** that inspects the keys present in your configuration:

1. If `auth_type = "client_credentials"` is present, it will use the recommended flow.
2. If a `privatekey` or `privatekey_file` is detected, it will switch to the **JWT** flow.
3. Otherwise, it will look for classic combinations such as Password + Security Token.

> **Security Tip**: Never store your `.key` files or your `client_secret` in your Git repository. Always use environment variables for your production environments.