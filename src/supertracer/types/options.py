from typing import Optional, Callable
from pydantic import BaseModel, Field

class LoggerOptions(BaseModel):
    level: int = 20 # logging.INFO
    format: str = '%(message)s'
    datefmt: str | None = None

class MetricsOptions(BaseModel):
    enabled: bool = True
    history_limit: int = 1000
    refresh_interval: float = 2.0

class AuthOptions(BaseModel):
    auth_enabled: bool = False
    username: str | None = None
    password: str | None = None
    username_env: str | None = None
    password_env: str | None = None
    auth_fn: Callable[[str, str], bool] | None = None
    storage_secret: str | None = None
    storage_secret_env: str | None = None

class ApiOptions(BaseModel):
    api_enabled: bool = False
    api_key: str | None = None
    api_key_env: str | None = None
    api_auth_fn: Callable[[str], bool] | None = None

class RetentionOptions(BaseModel):
    enabled: bool = False
    max_records: int = 10000
    cleanup_interval_minutes: int = 30
    cleanup_older_than_hours: int = 24

class SupertracerOptions(BaseModel):
    logger_options: LoggerOptions = Field(default_factory=LoggerOptions)
    metrics_options: MetricsOptions = Field(default_factory=MetricsOptions)
    auth_options: AuthOptions = Field(default_factory=AuthOptions)
    api_options: ApiOptions = Field(default_factory=ApiOptions)
    retention_options: RetentionOptions = Field(default_factory=RetentionOptions)
    save_own_traces: bool = False
    capture_request_body: bool = True
    max_request_body_size: int = 1024 * 10