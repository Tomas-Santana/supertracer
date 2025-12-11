# Authentication Configuration and Logic

SuperTracer includes a built-in authentication system to protect the UI dashboard (`/supertracer/logs`). This document explains how to configure and customize the login process.

## Configuration (`AuthOptions`)

Authentication is configured using the `AuthOptions` class passed to `SuperTracer`.

```python
from src.supertracer.types import options

auth_config = options.AuthOptions(
    auth_enabled=True,             # Enable login protection
    username="admin",              # Method 1: Direct Credentials
    password="secret",
    # username_env="USER_ENV",     # Method 2: Credentials from Environment Variables
    # password_env="PASS_ENV",
    # auth_fn=my_login_func,       # Method 3: Custom Authentication Logic
    storage_secret="random_string" # Secret for session encryption
)
```

### Options Detail

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `auth_enabled` | `bool` | `False` | If `True`, users are redirected to a login page before accessing the dashboard. |
| `username` / `password` | `str` | `None` | Static credentials for simple protection. |
| `username_env` / `password_env` | `str` | `None` | Names of environment variables containing the credentials. |
| `auth_fn` | `Callable[[str, str], bool]` | `None` | A custom function that takes `(username, password)` and returns `True` if valid. |
| `storage_secret` | `str` | `None` | A secret string used to sign session cookies. |
| `storage_secret_env` | `str` | `None` | Env var name for the storage secret. |

## Authentication Logic

The `AuthService` manages the login flow. When `auth_enabled` is `True`:

1.  **Access Control**: Any attempt to access `/supertracer/logs` without a valid session redirects the user to `/supertracer/login`.
2.  **Validation Priority**: When a user submits the login form, credentials are validated in this order:
    1.  **Direct Credentials**: Matches against `username` and `password` if provided.
    2.  **Environment Variables**: Matches against values found in `username_env` and `password_env`.
    3.  **Custom Function**: Calls `auth_fn(username, password)`. This allows integration with external databases or LDAP.

### The `auth_fn`

The custom authentication function gives you full control. It is useful for checking against a database or implementing complex logic.

**Signature:**
```python
def my_auth_function(username: str, password: str) -> bool:
    # Return True if login is successful, False otherwise
    return username == "admin" and password == "complex_logic"
```

## Session Management

- **Storage**: SuperTracer uses NiceGUI's built-in storage (signed cookies) to maintain user sessions.
- **Secret**: The `storage_secret` is crucial for security. If not provided, one should be set via environment variable or passed directly to ensure sessions cannot be forged.
- **Logout**: A logout button in the UI clears the session and redirects to the login page.
