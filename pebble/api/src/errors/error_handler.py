"""Standardized `{ error: { code, message, details? } }` responses."""

import json

import azure.functions as func
from pydantic import ValidationError as PydanticValidationError

from src.errors.error_types import AppError, ValidationError
from src.logger import get_logger

logger = get_logger("errors")


def error_response(
    status_code: int, code: str, message: str, details: object | None = None
) -> func.HttpResponse:
    error: dict[str, object] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return func.HttpResponse(
        json.dumps({"error": error}),
        status_code=status_code,
        mimetype="application/json",
    )


def pydantic_to_validation_error(exc: PydanticValidationError) -> ValidationError:
    details = [
        {"field": ".".join(str(p) for p in err["loc"]), "message": err["msg"]}
        for err in exc.errors(include_url=False, include_context=False, include_input=False)
    ]
    return ValidationError("Request validation failed", details=details)


def handle_error(error: Exception) -> func.HttpResponse:
    if isinstance(error, PydanticValidationError):
        error = pydantic_to_validation_error(error)

    if isinstance(error, AppError):
        if error.status_code >= 500:
            logger.error("request_failed", code=error.code, message=error.message)
        return error_response(error.status_code, error.code, error.message, error.details)

    logger.error("unhandled_error", error=repr(error))
    return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
