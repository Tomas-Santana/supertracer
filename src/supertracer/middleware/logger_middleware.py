from typing import Any, Callable, Optional, Dict, Tuple
from fastapi import Request, FastAPI
from starlette.responses import StreamingResponse
import time
from datetime import datetime
import json
from supertracer.types.options import SupertracerOptions
from supertracer.types.logs import Log
from supertracer.services.metrics import MetricsService
import traceback

def add_logger_middleware(options: SupertracerOptions, connector, broadcaster, metrics_service: MetricsService, app: FastAPI) -> None:
    """Creates a FastAPI middleware function for logging requests and responses and adds it to the app.
    
    Args:
        options: Supertracer options for configuring logging behavior.
        connector: Database connector to save logs.
        broadcaster: Log broadcaster to notify subscribers of new logs.
        metrics_service: Service to record metrics about requests.
    
    Returns:
        A FastAPI middleware function. yay
    """
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable):
        request_data = await _capture_request_data(request, options)

        if _should_skip_logging(request, request_data["url"], options):
            return await call_next(request)

        start_time = time.time()
        response: Optional[StreamingResponse] = None
        error_message = None
        stack_trace = None
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code if response else 500
            if status_code >= 400:
                error_message = f"HTTP {status_code} Error"
        except Exception as exc:
            error_message = str(exc)
            stack_trace = traceback.format_exc()
            raise
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            response_headers, response_body, response_size = await _capture_response_data(response, options)

            log_entry = _build_log_entry(
                request_data=request_data,
                response_headers=response_headers,
                response_body=response_body,
                response_size=response_size,
                status_code=status_code,
                duration_ms=duration_ms,
                error_message=error_message,
                stack_trace=stack_trace,
            )

            _persist_log(connector, broadcaster, metrics_service, log_entry)

        return response


def _should_skip_logging(request: Request, url: str, options: SupertracerOptions) -> bool:
    if options.capture_options.save_own_traces:
        return False

    base_url = str(request.base_url).rstrip("/")
    skip_prefixes = [options.ui_options.mount_path, options.api_options.base_path]

    for prefix in skip_prefixes:
        if not prefix:
            continue
        cleaned_prefix = prefix.lstrip("/")
        if not cleaned_prefix:
            continue
        full_prefix = f"{base_url}/{cleaned_prefix}"
        if url.startswith(full_prefix):
            return True
    return False


async def _capture_request_data(request: Request, options: SupertracerOptions) -> Dict[str, Any]:
    headers = _filter_headers(dict(request.headers), options.capture_options.exclude_headers)

    body = None
    if options.capture_options.capture_request_body:
        max_size = options.capture_options.max_request_body_size
        body = await capture_request_body(request, max_size)

    return {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "headers": headers,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": headers.get("user-agent"),
        "body": body,
    }


async def _capture_response_data(response: Optional[StreamingResponse], options: SupertracerOptions) -> Tuple[Optional[Dict[str, Any]], Optional[Any], Optional[int]]:
    if not response:
        return None, None, None

    headers = _filter_headers(dict(response.headers), options.capture_options.exclude_headers)

    body = None
    if hasattr(response, "body_iterator") and options.capture_options.capture_response_body:
        max_size = options.capture_options.max_response_body_size
        body = await capture_response_body(response, max_size)

    size = response.headers.get("content-length")
    if size is not None:
        try:
            size = int(size)
        except ValueError:
            size = None

    return headers, body, size


def _build_log_entry(
    request_data: Dict[str, Any],
    response_headers: Optional[Dict[str, Any]],
    response_body: Optional[Any],
    response_size: Optional[int],
    status_code: int,
    duration_ms: int,
    error_message: Optional[str],
    stack_trace: Optional[str],
) -> Log:
    return {
        "id": 0,
        "content": f"{request_data['method']} {request_data['url']}",
        "timestamp": datetime.now(),
        "method": request_data["method"],
        "path": request_data["path"],
        "url": request_data["url"],
        "headers": request_data["headers"],
        "log_level": "ERROR" if status_code >= 500 else ("WARN" if status_code >= 400 else "HTTP"),
        "status_code": status_code,
        "duration_ms": duration_ms,
        "client_ip": request_data["client_ip"],
        "user_agent": request_data["user_agent"],
        "request_query": request_data["query_params"],
        "request_body": request_data["body"],
        "response_headers": response_headers,
        "response_body": response_body,
        "response_size_bytes": response_size,
        "error_message": error_message,
        "stack_trace": stack_trace,
    }


def _persist_log(connector, broadcaster, metrics_service: MetricsService, log_entry: Log) -> None:
    try:
        log_id = connector.save_log(log_entry)
        log_entry["id"] = log_id
        broadcaster.broadcast(log_entry)

        metrics_service.record_request(
            id=log_id,
            method=log_entry["method"] or "UNKNOWN",
            path=log_entry["path"] or "UNKNOWN",
            status_code=log_entry["status_code"] or 0,
            duration_ms=log_entry["duration_ms"] or 0,
            error_msg=log_entry.get("error_message"),
        )
    except Exception as exc:
        print(f"SuperTracer Error: {exc}")


def _filter_headers(headers: Dict[str, Any], excluded: Optional[list[str]]) -> Dict[str, Any]:
    if not excluded:
        return headers
    excluded_set = {h.lower() for h in excluded}
    return {k: v for k, v in headers.items() if k.lower() not in excluded_set}
    
async def capture_request_body(request: Request, max_size: int) -> Optional[Any]:
    """Capture and return the request body if within size limits."""
    try:
        body_bytes = await request.body()
        if len(body_bytes) < max_size:
            try:
                return json.loads(body_bytes)
            except:
                return body_bytes.decode('utf-8', errors='ignore')
    except Exception:
        pass
    return None

async def capture_response_body(response: StreamingResponse, max_size: int) -> Optional[Any]:
    """Capture and return the response body if within size limits.
    
    Since StreamingResponse body is an async generator, we need to consume it
    and then reconstruct a new generator for the response to use.
    """
    try:
        body_chunks = []
        body_size = 0
        
        # Consume the response body
        async for chunk in response.body_iterator:
            body_chunks.append(chunk)
            body_size += len(chunk)
            
        # Reconstruct the body iterator for the actual response
        async def new_body_iterator():
            for chunk in body_chunks:
                yield chunk
                
        response.body_iterator = new_body_iterator()
        
        # Process captured body if within limits
        if body_size < max_size:
            full_body = b"".join(body_chunks)
            try:
                return json.loads(full_body)
            except:
                return full_body.decode('utf-8', errors='ignore')
                
    except Exception as e:
        print(f"Error capturing response body: {e}")
        pass
    return None


  
