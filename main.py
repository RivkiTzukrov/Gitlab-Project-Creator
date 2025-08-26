from uvicorn import run
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from fastapi.exceptions import RequestValidationError

from app.api.routes import router
from app.core.config import settings
from app.core.exception_handlers import (
    base_api_exception_handler,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.exceptions import BaseAPIException
from app.core.logger import setup_logging

setup_logging()


def create_app() -> FastAPI:
    app = FastAPI(title="GitLab Repository Sculptor")
    app.include_router(router)

    app.add_exception_handler(BaseAPIException, base_api_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8080"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

    return app


app = create_app()

if __name__ == "__main__":
    run("main:app", host="127.0.0.1", port=settings.port, reload=True)
