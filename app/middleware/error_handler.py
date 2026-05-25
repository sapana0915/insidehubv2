from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import DetailedException
import logging

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(DetailedException)
    async def detail_exception_handler(request: Request, exc: DetailedException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
