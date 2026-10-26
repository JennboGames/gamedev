import json

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from src.errors.error_handler import handle_error
from src.errors.error_types import BadRequestError, NotFoundError, UpstreamError, ValidationError


def body_of(response) -> dict:
    return json.loads(response.get_body())


def test_status_codes_and_codes():
    cases = [
        (NotFoundError("Product", "abc"), 404, "NOT_FOUND"),
        (ValidationError("Bad input"), 422, "VALIDATION_ERROR"),
        (BadRequestError("Bad"), 400, "BAD_REQUEST"),
        (UpstreamError("Amazon down"), 502, "UPSTREAM_ERROR"),
        (RuntimeError("boom"), 500, "INTERNAL_ERROR"),
    ]
    for error, status, code in cases:
        response = handle_error(error)
        assert response.status_code == status
        assert body_of(response)["error"]["code"] == code


def test_unknown_errors_do_not_leak_messages():
    assert "secret detail" not in json.dumps(body_of(handle_error(RuntimeError("secret detail"))))


def test_pydantic_errors_become_validation_errors_with_field_details():
    class Model(BaseModel):
        name: str

    try:
        Model.model_validate({})
    except PydanticValidationError as exc:
        response = handle_error(exc)

    assert response.status_code == 422
    assert body_of(response)["error"]["details"][0]["field"] == "name"


def test_error_shape_is_consistent():
    for error in (NotFoundError("X"), ValidationError("Y"), RuntimeError("Z")):
        payload = body_of(handle_error(error))
        assert set(payload) == {"error"}
        assert {"code", "message"} <= set(payload["error"])
