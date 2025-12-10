from pydantic import BaseModel
from datetime import datetime

class LogFilters(BaseModel):
    limit: int = 20
    search_text: str | None = None
    endpoint: str | None = None
    status_code: str | None = None
    log_level: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    methods: list[str] | None = None
    min_latency: int | None = None
    max_latency: int | None = None
    has_error: bool | None = None
    
    def to_query_params(self) -> str:
        params = self.model_dump(exclude_none=True)
        return '&'.join([f"{key}={value}" for key, value in params.items()])
    