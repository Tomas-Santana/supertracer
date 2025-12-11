# API Configuration and Usage

SuperTracer provides a REST API to programmatically access logs and metrics. This document explains how to configure and use the API.

## Configuration (`ApiOptions`)

The API is configured using the `ApiOptions` class passed to `SuperTracer`.

```python
from src.supertracer.types import options

api_config = options.ApiOptions(
    api_enabled=True,              # Enable the API endpoints
    api_auth_enabled=True,         # Require authentication
    api_key="my-secret-key",       # Method 1: Direct API Key
    # api_key_env="API_KEY_ENV",   # Method 2: API Key from Environment Variable
    # api_auth_fn=my_auth_func     # Method 3: Custom Validation Function
)
```

### Options Detail

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_enabled` | `bool` | `False` | Master switch to enable or disable the API routes. |
| `api_auth_enabled` | `bool` | `True` | If `True`, requests must provide a valid API key. If `False`, the API is public. |
| `api_key` | `str` | `None` | A static string to use as the valid API key. |
| `api_key_env` | `str` | `None` | The name of the environment variable that contains the API key. |
| `api_auth_fn` | `Callable[[str], bool]` | `None` | A custom function that takes the provided key and returns `True` if valid. |

## Authentication Logic

When `api_auth_enabled` is `True`, the system enforces authentication on all API endpoints.

1.  **Header Requirement**: The client must send the API key in the `X-API-Key` HTTP header.
2.  **Validation Priority**: If multiple authentication methods are configured, they are checked in this order:
    1.  **Direct `api_key`**: Checks if the header matches the configured string.
    2.  **Environment Variable**: Checks if the header matches the value of the environment variable specified in `api_key_env`.
    3.  **Custom Function**: Calls `api_auth_fn(key)` with the header value.

If the check fails or the header is missing, the API returns `401 Unauthorized`.

## Endpoints

The API is mounted at `/supertracer-api/api/v1`.

### 1. Query Logs
**GET** `/supertracer-api/api/v1/logs`

Retrieve a list of logs based on filters.

**Parameters:**
- `limit` (int): Number of logs to return.
- `search_text` (str): Filter by content text.
- `status_code` (str): Filter by status code (e.g., "200", "4XX").
- `method` (str): Filter by HTTP method.
- `start_date` / `end_date`: Date range filtering.

**Response:**
```json
{
  "data": [ ... log objects ... ],
  "length": 50,
  "next_page_url": "http://.../logs?limit=50&end_date=..."
}
```

### 2. Get Log Detail
**GET** `/supertracer-api/api/v1/logs/{id}`

Retrieve full details for a specific log entry.

### 3. Get Metrics
**GET** `/supertracer-api/api/v1/metrics`

Retrieve current dashboard metrics (RPS, error rates, etc.).

### 4. Status Check
**GET** `/supertracer-api/api/v1/status`

Returns `{"status": "ok"}` if the API is operational.
