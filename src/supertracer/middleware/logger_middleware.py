from typing import Any, Callable, Optional
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
  # Capture request details
      method = request.method
      url = str(request.url)
      path = request.url.path
      headers = dict(request.headers)
      query_params = dict(request.query_params)
      client_ip = request.client.host if request.client else None
      user_agent = headers.get('user-agent')
      
      body = None
      if options.capture_options.capture_request_body:
          max_size = options.capture_options.max_request_body_size
          body = await capture_request_body(request, max_size)

      start_time = time.time()
      
      if not options.capture_options.save_own_traces:
          # Skip logging if the request is to Supertracer itself
          if url.startswith(str(request.base_url) + "supertracer"):
              return await call_next(request)

      # Process the request
      response: Optional[StreamingResponse] = None
      error_message = None
      stack_trace = None
      status_code = 500
      
      try:
          response = await call_next(request)
          status_code = response.status_code if response else 500
          if status_code >= 400:
              error_message = f"HTTP {status_code} Error"
      except Exception as e:
          # Capture error if exception occurs
          error_message = str(e)
          stack_trace = traceback.format_exc()
          raise e # Re-raise to let FastAPI handle it
      finally:
          # Calculate duration
          duration_ms = int((time.time() - start_time) * 1000)
          
          # Capture response details if response exists
          response_headers = dict(response.headers) if response else None
          response_body = None
          
          if response and hasattr(response, 'body_iterator') and options.capture_options.capture_response_body:
              max_size = options.capture_options.max_response_body_size
              response_body = await capture_response_body(response, max_size)
          
          response_size = response.headers.get('content-length') if response and 'content-length' in response.headers else None
          if response_size is not None:
              try:
                  response_size = int(response_size)
              except ValueError:
                  response_size = None
          


          # Save to DB after processing
          try:
              log: Log = {
                  'id': 0,  # Will be auto-generated
                  'content': f"{method} {url}",
                  'timestamp': datetime.now(),
                  'method': method,
                  'path': path,
                  'url': url,
                  'headers': headers,
                  'log_level': 'ERROR' if status_code >= 500 else ('WARN' if status_code >= 400 else 'HTTP'),
                  'status_code': status_code,
                  'duration_ms': duration_ms,
                  'client_ip': client_ip,
                  'user_agent': user_agent,
                  'request_query': query_params,
                  'request_body': body,
                  'response_headers': response_headers,
                  'response_body': response_body,
                  'response_size_bytes': response_size,
                  'error_message': error_message,
                  'stack_trace': stack_trace
              }
              log_id = connector.save_log(log)
              log['id'] = log_id
              broadcaster.broadcast(log)
              
              metrics_service.record_request(
                    id=log_id,
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    error_msg=error_message
                )
          except Exception as e:
              print(f"SuperTracer Error: {e}")

      return response
    
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


  
