from typing import Optional
from fastapi import FastAPI, Response
from src.supertracer import SuperTracer
import logging
import time


app = FastAPI()

# Initialize SuperTracer
tracer = SuperTracer(app, options={
    "logger_options": {
        "level": logging.DEBUG,
        "format": "%(message)s"
    },
    "save_own_traces": False
})  

logger = tracer.get_logger('supertracer')

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    logger.error("An error occurred at root endpoint")
    logger.warning("This is a warning at root endpoint")
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
def custom_method_endpoint(response: Response, wait: int=0, status: int=200, log_type: Optional[str]=None, log_text: Optional[str]=None):
    logger_method = logger.info
    if log_type == 'error':
        logger_method = logger.error
    elif log_type == 'warning':
        logger_method = logger.warning

    logger_method(f"Custom endpoint accessed with wait={wait}, status={status}, log_type={log_type}, log_text={log_text}")
    if wait > 0:
        time.sleep(wait)
        logger_method(f"Waited for {wait} seconds")

    response.status_code = status
    return {"message": f"Custom endpoint response with status {status}"}

if __name__ == "__main__":
    import uvicorn
    # Run the app
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)



