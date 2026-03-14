"""Error handling utilities and middleware."""

from typing import Any, Dict, Optional, Tuple
from functools import wraps
from logging import getLogger
import traceback
import json

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import get_settings

logger = getLogger(__name__)
settings = get_settings()


class ErrorResponse:
    """Standardized error response structure."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ):
        self.message = message
        self.code = code
        self.details = details
        self.status_code = status_code

    def to_dict(self) -> Dict[str, Any]:
        response = {
            "error": {
                "message": self.message,
                "code": self.code,
            }
        }
        if self.details:
            response["error"]["details"] = self.details
        return response


# Error codes
class ErrorCode:
    """Standard error codes."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    SCAN_ERROR = "SCAN_ERROR"
    PAYMENT_ERROR = "PAYMENT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# Custom exceptions
class AccessibleAIException(Exception):
    """Base exception for AccessibleAI."""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundException(AccessibleAIException):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.NOT_FOUND, 404, details)


class UnauthorizedException(AccessibleAIException):
    """Unauthorized access."""

    def __init__(self, message: str = "Unauthorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.AUTHORIZATION_ERROR, 401, details)


class ForbiddenException(AccessibleAIException):
    """Forbidden access."""

    def __init__(self, message: str = "Forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.AUTHORIZATION_ERROR, 403, details)


class ValidationException(AccessibleAIException):
    """Validation error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.VALIDATION_ERROR, 422, details)


class ConflictException(AccessibleAIException):
    """Conflict error."""

    def __init__(self, message: str = "Conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.CONFLICT, 409, details)


class RateLimitException(AccessibleAIException):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.RATE_LIMIT_EXCEEDED, 429, details)


class PaymentException(AccessibleAIException):
    """Payment processing error."""

    def __init__(self, message: str = "Payment error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.PAYMENT_ERROR, 402, details)


async def accessible_ai_exception_handler(request: Request, exc: AccessibleAIException) -> JSONResponse:
    """Handle AccessibleAI exceptions."""
    error_response = ErrorResponse(
        message=exc.message,
        code=exc.code,
        details=exc.details,
        status_code=exc.status_code,
    )

    # Log the error
    logger.warning(
        f"AccessibleAI Exception: {exc.code} - {exc.message}",
        extra={"path": request.url.path, "method": request.method, "details": exc.details}
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict(),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    error_response = ErrorResponse(
        message=exc.detail,
        code=getattr(exc, "code", "HTTP_ERROR"),
        status_code=exc.status_code,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict(),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions."""
    # Log the full traceback
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={"path": request.url.path, "method": request.method},
    )

    # Send to Sentry if configured
    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.capture_exception(exc)

    if settings.debug:
        # Return detailed error in debug mode
        error_response = ErrorResponse(
            message=str(exc),
            code=ErrorCode.INTERNAL_ERROR,
            details={"traceback": traceback.format_exc()},
        )
    else:
        # Generic error message in production
        error_response = ErrorResponse(
            message="An internal server error occurred",
            code=ErrorCode.INTERNAL_ERROR,
        )

    return JSONResponse(
        status_code=500,
        content=error_response.to_dict(),
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle database exceptions."""
    logger.error(f"Database error: {str(exc)}", exc_info=True)

    error_response = ErrorResponse(
        message="A database error occurred",
        code=ErrorCode.DATABASE_ERROR,
    )

    return JSONResponse(
        status_code=500,
        content=error_response.to_dict(),
    )


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for consistent error handling and logging."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Log all requests
        logger.info(f"{request.method} {request.url.path}")

        try:
            response = await call_next(request)

            # Log non-200 responses
            if response.status_code >= 400:
                logger.warning(
                    f"{request.method} {request.url.path} -> {response.status_code}",
                )

            return response

        except Exception as exc:
            # Exception will be caught by exception handlers above
            raise


def error_decorator(func):
    """Decorator for consistent error handling in endpoints."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AccessibleAIException:
            raise  # Re-raise to be handled by exception handler
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(f"Unhandled error in {func.__name__}")
            raise AccessibleAIException(
                message="An unexpected error occurred",
                code=ErrorCode.INTERNAL_ERROR,
            )

    return wrapper


def safe_execute(func):
    """Decorator to safely execute functions with error handling."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AccessibleAIException:
            raise
        except Exception as exc:
            logger.error(f"Error in {func.__name__}: {str(exc)}")
            raise AccessibleAIException(
                message=f"Operation failed: {func.__name__}",
                code=ErrorCode.INTERNAL_ERROR,
            )

    return wrapper


def validate_request(*validators):
    """Decorator for request validation.

    Usage:
        @validate_request(
            validate_email,
            validate_password,
        )
        async def create_user(data: UserCreate):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for validator in validators:
                validator(kwargs)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def log_errors(func):
    """Decorator to log all errors from a function."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            logger.exception(f"Error in {func.__name__}: {str(exc)}")
            raise

    return wrapper
