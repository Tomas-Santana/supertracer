from typing import Optional
from fastapi import FastAPI, Request, Response
from src.supertracer import SuperTracer
from src.supertracer.connectors import MemoryConnector
from src.supertracer.types import options
import logging
import time


app = FastAPI()

auth_fn = lambda u, p: True

# Initialize SuperTracer
tracer = SuperTracer(
    app, 
    connector=MemoryConnector(),
    options=options.SupertracerOptions(
        logger_options=options.LoggerOptions(
            level=logging.DEBUG,
            format="%(message)s"
        ),
        auth_options=options.AuthOptions(
            auth_enabled=False,
            auth_fn=auth_fn,
        ),
        api_options=options.ApiOptions(
            api_enabled=True,
            api_auth_fn=lambda key: True,
        ),
        save_own_traces=False,
        retention_options=options.RetentionOptions(
            enabled=True,
            max_records=5000,
            cleanup_interval_minutes=1,
            cleanup_older_than_hours=1,
        ),
        capture_options=options.CaptureOptions(
            capture_request_body=True,
            max_request_body_size=1024 * 5,  # 5 KB
            capture_response_body=True,
            max_response_body_size=1024 * 5,  # 5 KB
        )
                
    )
    )  

logger = logging.getLogger('supertracer')

@app.get("/")
def read_root():
    logger.warning({"event": "root_accessed"})
    return {"Hello": "World", "message": "Visit supertracer/logs to see the requests!"}

@app.post("/hello")
def say_hello():
    logger.info("Hello endpoint accessed")
    return {"message": "Hello from POST endpoint"}

@app.post("/wait")
def wait_endpoint(seconds: int):
    logger.info(f"Wait endpoint accessed, sleeping for {seconds} seconds")
    time.sleep(seconds)
    logger.info("Wait completed")
    return {"message": f"Waited for {seconds} seconds"}

@app.get("/error")
def error_endpoint():
    logger.info("Error endpoint accessed, about to raise an exception")
    1/0  # This will raise a ZeroDivisionError

@app.get("/custom")
@app.post("/custom")
@app.put("/custom")
@app.delete("/custom")
def custom_method_endpoint(
    request: Request, 
    response: Response, 
    wait: int=0, 
    status: int=200, 
    log_type: Optional[str]=None, 
    log_text: Optional[str]=None,
    error: Optional[bool]=False
):
    if error:
        raise ValueError("This is a custom error triggered by the 'error' parameter.")
    
    logger_method = logger.info
    if log_type == 'error':
        logger_method = logger.error
    elif log_type == 'warning':
        logger_method = logger.warning

    logger_method(log_text or f"Custom endpoint accessed with method {request.method}")
    if wait > 0:
        time.sleep(wait)
        logger_method(f"Waited for {wait} seconds")

    response.status_code = status
    return {"message": f"Custom endpoint response with status {status}"}

if __name__ == "__main__":
    import uvicorn
    # Run the app
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)



