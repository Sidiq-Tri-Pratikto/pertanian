"""Make the generated OpenAPI document describe the real failure responses.

Run as a module to print the document: ``python -m app.core.openapi``.
"""

import json
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel


class ErrorRecovery(BaseModel):
    """Retry guidance for one failure."""

    retryable: bool
    retry_after_seconds: int | None = None
    max_attempts: int | None = None


class ErrorFieldDetail(BaseModel):
    """One invalid field in a validation failure."""

    loc: list[str | int]
    msg: str
    type: str


class ErrorBody(BaseModel):
    """Public failure content."""

    code: str
    message: str
    request_id: str
    recovery: ErrorRecovery
    details: list[ErrorFieldDetail] | None = None
    current_version: int | None = None


class ErrorEnvelope(BaseModel):
    """The one failure body on every endpoint."""

    error: ErrorBody


def _envelope_response(description: str) -> dict[str, Any]:
    schema = {"$ref": "#/components/schemas/ErrorEnvelope"}
    return {"description": description, "content": {"application/json": {"schema": schema}}}


def install_error_schema(app: FastAPI) -> None:
    """Replace FastAPI's default 422 schema and document the envelope on every operation.

    Args:
        app (FastAPI): The application.
    """
    generate = app.openapi

    def openapi() -> dict[str, Any]:
        document = generate()
        schemas = document.setdefault("components", {}).setdefault("schemas", {})
        if "ErrorEnvelope" in schemas:
            return document
        envelope = ErrorEnvelope.model_json_schema(ref_template="#/components/schemas/{model}")
        schemas.update(envelope.pop("$defs"))
        schemas["ErrorEnvelope"] = envelope
        schemas.pop("HTTPValidationError", None)
        schemas.pop("ValidationError", None)
        for path_item in document["paths"].values():
            for operation in path_item.values():
                responses = operation["responses"]
                responses["default"] = _envelope_response("Failure")
                if "422" in responses:
                    responses["422"] = _envelope_response("Validation failed")
        return document

    app.openapi = openapi


if __name__ == "__main__":
    from app.main import app

    print(json.dumps(app.openapi(), indent=2, sort_keys=True))
