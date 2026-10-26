"""Shared HTTP helpers for function handlers: parsing, JSON responses, error + request logging."""

import functools
import json
import time
from collections.abc import Callable
from typing import TypeVar
from urllib.parse import urlparse
from uuid import UUID

import azure.functions as func
from pydantic import BaseModel

from src.errors.error_handler import handle_error
from src.errors.error_types import BadRequestError, ValidationError
from src.logger import get_logger
from src.models.api import ApiModel

logger = get_logger("http")

M = TypeVar("M", bound=BaseModel)


def json_response(payload: ApiModel | dict, status_code: int = 200) -> func.HttpResponse:
    body = payload.to_json() if isinstance(payload, ApiModel) else payload
    return func.HttpResponse(json.dumps(body), status_code=status_code, mimetype="application/json")


def parse_body(req: func.HttpRequest, model: type[M], *, optional: bool = False) -> M:
    if optional and not req.get_body():
        return model()
    try:
        raw = req.get_json()
    except ValueError as exc:
        raise BadRequestError("Request body must be valid JSON") from exc
    return model.model_validate(raw)


def parse_uuid_param(req: func.HttpRequest, name: str) -> str:
    value = req.route_params.get(name, "")
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise ValidationError(
            f"Path parameter '{name}' must be a UUID",
            details=[{"field": name, "message": "Invalid UUID"}],
        ) from exc


def api_handler(handler: Callable[[func.HttpRequest], func.HttpResponse]):  # noqa: ANN201
    """Standard error mapping plus one request-completed log line per call."""

    @functools.wraps(handler)
    def wrapper(req: func.HttpRequest) -> func.HttpResponse:
        started = time.perf_counter()
        try:
            response = handler(req)
        except Exception as exc:  # noqa: BLE001
            response = handle_error(exc)
        logger.info(
            "request_completed",
            method=req.method,
            path=urlparse(req.url).path,
            status=response.status_code,
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
        )
        return response

    return wrapper
