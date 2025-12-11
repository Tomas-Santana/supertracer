import pytest
from pydantic import ValidationError
from supertracer.types.options import (
    LoggerOptions, MetricsOptions,
    AuthOptions, ApiOptions, RetentionOptions, CaptureOptions
)

class TestOptionsValidation:
    def test_logger_options_validation(self):
        with pytest.raises(ValidationError, match="Logging level must be non-negative"):
            LoggerOptions(level=-1)

    def test_metrics_options_validation(self):
        with pytest.raises(ValidationError, match="history_limit must be positive"):
            MetricsOptions(history_limit=0)
            
        with pytest.raises(ValidationError, match="refresh_interval must be positive"):
            MetricsOptions(refresh_interval=0)

    def test_auth_options_validation(self):
        # Enabled but no credentials
        with pytest.raises(ValidationError, match="If auth_enabled is True"):
            AuthOptions(auth_enabled=True)
            
        # Valid cases
        AuthOptions(auth_enabled=True, username="u", password="p")
        AuthOptions(auth_enabled=True, username_env="U", password_env="P")
        AuthOptions(auth_enabled=True, auth_fn=lambda u, p: True)

    def test_api_options_validation(self):
        # Enabled but no key
        with pytest.raises(ValidationError, match="If api_enabled is True"):
            ApiOptions(api_enabled=True)
            
        # Valid cases
        ApiOptions(api_enabled=True, api_key="key")
        ApiOptions(api_enabled=True, api_key_env="KEY_ENV")
        ApiOptions(api_enabled=True, api_auth_fn=lambda k: True)

    def test_retention_options_validation(self):
        with pytest.raises(ValidationError, match="max_records must be non-negative"):
            RetentionOptions(max_records=-1)
            
        with pytest.raises(ValidationError, match="cleanup_interval_minutes must be positive"):
            RetentionOptions(cleanup_interval_minutes=0)

    def test_capture_options_validation(self):
        with pytest.raises(ValidationError, match="Body size limit must be non-negative"):
            CaptureOptions(max_request_body_size=-1)
            
        with pytest.raises(ValidationError, match="Body size limit must be non-negative"):
            CaptureOptions(max_response_body_size=-1)
