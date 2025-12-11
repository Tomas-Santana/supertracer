from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse
from supertracer.services.auth import AuthService
from supertracer.connectors.base import BaseConnector
from supertracer.types.options import ApiOptions
from supertracer.types.logs import Log
from supertracer.types.filters import LogFilters
from typing import List, Optional, Annotated
from supertracer.middleware.api_middleware import authenticate_request
from supertracer.services.metrics import MetricsService


class APIService:
    BASE_PATH = "/supertracer-api/api/v1"
    def __init__(self, auth: AuthService, metrics: MetricsService, connector: BaseConnector):
        print("Initializing APIService")
        self.auth = auth
        self.metrics = metrics
        self.connector = connector
        self.router = APIRouter(prefix=self.BASE_PATH, tags=["SuperTracer API"])

        self._add_routes()
        
    def get_log(self, id: int):
        return self.connector.fetch_log(id)
      
    def query_logs(
      self,
      filters: Annotated[LogFilters, Query(...)],
    ):
        return self.connector.fetch_logs(filters)
    
    def _add_routes(self):
        if not self.auth.api_enabled:
            return
        
        @self.router.get("/logs")
        async def query_logs_endpoint(
          filters: Annotated[LogFilters, Query(...)],
          request: Request
        ):
            if not authenticate_request(request, self.auth, ApiOptions()):
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            data = self.query_logs(filters)
            last_date = data[-1]['timestamp'] if data else None
            res = {
                "data": data,
                "length": len(data)
            }
            
            # include a next_page_url if there are more logs
            if last_date and filters.limit and len(data) == filters.limit:
                query = filters.model_dump(mode='json')
                query['end_date'] = last_date.isoformat()
                res['next_page_url'] = str(request.url).split('?')[0] + '?' + '&'.join([f"{key}={value}" for key, value in query.items() if value is not None])
            return res

        @self.router.get("/logs/{id}", response_model=Optional[Log])
        async def get_log_endpoint(id: int, request: Request):
            if not authenticate_request(request, self.auth, ApiOptions()):
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            
            
            return self.get_log(id)
        
        @self.router.get("/metrics")
        async def get_metrics_endpoint(request: Request):
            if not authenticate_request(request, self.auth, ApiOptions()):
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            # For simplicity, return a placeholder metrics response
            return self.metrics.get_summary()
        
        
        
        @self.router.get("/status")
        async def status_endpoint(request: Request):
            if not authenticate_request(request, self.auth, ApiOptions()):
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            return {"status": "ok"}
        
