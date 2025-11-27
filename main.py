from fastapi import FastAPI
from src.supertracer import SuperTracer
import logging

app = FastAPI()

# Initialize SuperTracer
tracer = SuperTracer(app, options={
    "logger_options": {
        "level": logging.INFO,
        "format": "%(message)s"
    }
})  

logger = tracer.get_logger('supertracer')

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    logger.error("An error occurred at root endpoint")
    logger.warning("This is a warning at root endpoint")
    return {"Hello": "World", "message": "Visit /logs to see the requests!"}


