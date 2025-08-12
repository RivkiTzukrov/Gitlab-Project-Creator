import logging
from typing import Union

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import BaseAPIException
from app.schemas.error_models import ErrorResponse

logger = logging.getLogger(__name__)


async def base_api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """Handle custom API exceptions"""
    logger.error(f"API Error: {exc.error_type} - {exc.message}", extra={"details": exc.details})
    
    error_response = ErrorResponse(
        status_code=exc.status_code,
        error=exc.error_type,
        message=exc.message,
        details=exc.details,
        timestamp=ErrorResponse.from_exception(exc).timestamp
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPExceptions"""
    logger.error(f"HTTP Error: {exc.status_code} - {exc.detail}")
    
    error_type = "http_error"
    if exc.status_code in [401, 403]:
        error_type = "authentication_error"
    elif exc.status_code == 404:
        error_type = "not_found_error"
    elif exc.status_code == 422:
        error_type = "validation_error"
    
    error_response = ErrorResponse.from_exception(
        exc, 
        status_code=exc.status_code,
        error_type=error_type
    )
    error_response.message = exc.detail
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )


async def validation_exception_handler(request: Request, exc: Union[PydanticValidationError, RequestValidationError]) -> JSONResponse:
    """Handle Pydantic validation errors"""
    logger.error(f"Validation Error: {exc}")
    
    missing_fields = []
    for error in exc.errors():
        if error["type"] == "missing" and "loc" in error:
            field = error["loc"][-1]  # Get the actual field name
            missing_fields.append(field)
    
    if missing_fields:
        message = f"Missing required fields: {', '.join(missing_fields)}"
        details = {"missing_fields": missing_fields}
    else:
        message = "Request validation failed"
        details = {"errors": [f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()]}
    
    error_response = ErrorResponse(
        status_code=422,
        error="validation_error",
        message=message,
        details=details,
        timestamp=ErrorResponse.from_exception(exc).timestamp
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions"""
    logger.error(f"Unexpected error: {type(exc).__name__} - {str(exc)}", exc_info=True)
    
    error_response = ErrorResponse.from_exception(exc)
    
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )