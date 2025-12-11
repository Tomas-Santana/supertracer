from typing import Optional, Callable, Literal, Union, Annotated
from pydantic import BaseModel, Field, field_validator, model_validator

class LoggerOptions(BaseModel):
    level: int = 20 # logging.INFO
    format: str = '%(message)s'
    datefmt: str | None = None

    @field_validator('level')
    @classmethod
    def level_must_be_valid(cls, v: int) -> int:
        if v < 0:
            raise ValueError('Logging level must be non-negative')
        return v

class MetricsOptions(BaseModel):
    enabled: bool = True
    history_limit: int = 1000
    refresh_interval: float = 2.0

    @field_validator('history_limit')
    @classmethod
    def history_limit_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError('history_limit must be positive')
        return v

    @field_validator('refresh_interval')
    @classmethod
    def refresh_interval_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('refresh_interval must be positive')
        return v
    
class UIOptions(BaseModel):
    mount_path: str = "/supertracer"
    page_size: int = 20
    storage_secret: str | None = None
    storage_secret_env: str | None = None

class AuthOptions(BaseModel):
    auth_enabled: bool = False
    username: str | None = None
    password: str | None = None
    username_env: str | None = None
    password_env: str | None = None
    auth_fn: Callable[[str, str], bool] | None = None

    @model_validator(mode='after')
    def check_auth_config(self) -> 'AuthOptions':
        if self.auth_enabled:
            has_credentials = (self.username and self.password)
            has_env_credentials = (self.username_env and self.password_env)
            has_auth_fn = self.auth_fn is not None
            
            if not (has_credentials or has_env_credentials or has_auth_fn):
                raise ValueError('If auth_enabled is True, you must provide username/password, env vars, or an auth_fn')
        return self

class ApiOptions(BaseModel):
    base_path: str = "/supertracer-api"
    api_enabled: bool = False
    api_auth_enabled: bool = True
    api_key: str | None = None
    api_key_env: str | None = None
    api_auth_fn: Callable[[str], bool] | None = None

    @model_validator(mode='after')
    def check_api_config(self) -> 'ApiOptions':
        if self.api_enabled and self.api_auth_enabled:
            if not (self.api_key or self.api_key_env or self.api_auth_fn):
                raise ValueError('If api_enabled is True, you must provide api_key, api_key_env, or api_auth_fn')
        return self

class RetentionOptions(BaseModel):
    enabled: bool = False
    max_records: int = 10000
    cleanup_interval_minutes: int = 30
    cleanup_older_than_hours: int = 24
    
    @field_validator('max_records')
    @classmethod
    def max_records_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError('max_records must be non-negative')
        return v
        
    @field_validator('cleanup_interval_minutes')
    @classmethod
    def cleanup_interval_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError('cleanup_interval_minutes must be positive')
        return v

class CaptureOptions(BaseModel):
    capture_request_body: bool = True
    max_request_body_size: int = 1024 * 10  # 10 KB
    capture_response_body: bool = True
    max_response_body_size: int = 1024 * 10  # 10 KB
    exclude_headers: list[str] = Field(default_factory=lambda: ['authorization', 'cookie'])
    save_own_traces: bool = False

    @field_validator('max_request_body_size', 'max_response_body_size')
    @classmethod
    def size_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError('Body size limit must be non-negative')
        return v

class SupertracerOptions(BaseModel):
    logger_options: LoggerOptions = Field(default_factory=LoggerOptions)
    metrics_options: MetricsOptions = Field(default_factory=MetricsOptions)
    auth_options: AuthOptions = Field(default_factory=AuthOptions)
    api_options: ApiOptions = Field(default_factory=ApiOptions)
    retention_options: RetentionOptions = Field(default_factory=RetentionOptions)
    capture_options: CaptureOptions = Field(default_factory=CaptureOptions)
    ui_options: UIOptions = Field(default_factory=UIOptions)
 