from typing import Optional, TypedDict

class LoggerOptions(TypedDict, total=False):
    level: int  # Logging level (e.g., logging.INFO, logging.DEBUG)
    format: str  # Log message format
    datefmt: str  # Date format in log messages
    
class SupertracerOptions(TypedDict, total=False):
    logger_options: LoggerOptions  # Options for configuring the logger