"""Typed application errors mapped to HTTP responses by error_handler."""

from typing import Any, Literal

ErrorCode = Literal[
    "BAD_REQUEST",
    "VALIDATION_ERROR",
    "NOT_FOUND",
    "UPSTREAM_ERROR",
    "CONFIGURATION_ERROR",
    "INTERNAL_ERROR",
]


class AppError(Exception):
    code: ErrorCode = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class BadRequestError(AppError):
    code: ErrorCode = "BAD_REQUEST"
    status_code = 400


class ValidationError(AppError):
    code: ErrorCode = "VALIDATION_ERROR"
    status_code = 422


class NotFoundError(AppError):
    code: ErrorCode = "NOT_FOUND"
    status_code = 404

    def __init__(self, resource: str, resource_id: str | None = None) -> None:
        suffix = f" '{resource_id}'" if resource_id else ""
        super().__init__(f"{resource}{suffix} was not found")


class UpstreamError(AppError):
    """An external dependency (Amazon, image host) failed."""

    code: ErrorCode = "UPSTREAM_ERROR"
    status_code = 502


class ConfigurationError(AppError):
    code: ErrorCode = "CONFIGURATION_ERROR"
    status_code = 500
