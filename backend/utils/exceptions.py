"""
Custom exception handlers for FastAPI.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


class MediqrException(Exception):
    """Base exception for MEDIQR application."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(MediqrException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", 404)


class DuplicateException(MediqrException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} already exists", 409)


class InsufficientStockException(MediqrException):
    def __init__(self, medicine_name: str, available: int, requested: int):
        super().__init__(
            f"Insufficient stock for {medicine_name}: available={available}, requested={requested}",
            400,
        )


class UnauthorizedException(MediqrException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, 401)


async def mediqr_exception_handler(request: Request, exc: MediqrException):
    """Global handler for MediqrException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "status_code": exc.status_code,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Global handler for HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "status_code": 500,
        },
    )
