from fastapi import FastAPI
from supertracer.types.options import RetentionOptions
import asyncio
from logging import Logger

class CleanupService:
    """
    Service to handle periodic cleanup of old logs based on retention options.
    
    Args:
        app (FastAPI): The FastAPI application instance.
        connector: The connector instance with a cleanup method.
        retention_options (RetentionOptions): Options defining retention policy.
        logger (Logger): Logger instance for logging cleanup actions.
        
    """
    def __init__(self, app: FastAPI, connector, retention_options: RetentionOptions, logger: Logger):
        self.app = app
        self.connector = connector
        self.retention_options = retention_options
        self.logger = logger
        self._setup_cleanup_task()

    def _setup_cleanup_task(self):
        if not self.retention_options.enabled:
            return

        @self.app.on_event("startup")
        async def start_cleanup_task():
            asyncio.create_task(self._cleanup_task())

    async def _cleanup_task(self):
        while True:
            try:
                # Run cleanup in executor to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.connector.cleanup, self.retention_options)
                self.logger.info("SUPERTRACER: Cleanup task executed successfully")
            except Exception as e:
                self.logger.error(f"SUPERTRACER: Cleanup task failed: {e}")

            # Wait for interval
            await asyncio.sleep(self.retention_options.cleanup_interval_minutes * 60)