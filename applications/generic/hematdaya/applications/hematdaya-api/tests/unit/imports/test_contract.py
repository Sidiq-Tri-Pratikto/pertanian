"""The import routes' published contract."""

import pytest

from app.main import app

PREVIEW = "/api/v1/sites/{site_id}/imports/preview"
GET_IMPORT = "/api/v1/imports/{import_id}"
GET_ERRORS = "/api/v1/imports/{import_id}/errors"
OPERATIONS = [(PREVIEW, "post"), (GET_IMPORT, "get"), (GET_ERRORS, "get")]
PREVIEW_FIELDS = {
    "id",
    "status",
    "file_name",
    "expires_at",
    "total_rows",
    "accepted_rows",
    "invalid_rows",
    "duplicate_rows",
    "conflict_rows",
    "pending_rows",
    "blocked",
    "block_reasons",
    "needs_acknowledgment",
    "questions",
    "mapping",
    "assumptions",
    "period",
    "errors",
    "next_error_cursor",
}


def _ref(schema: dict) -> str:
    return schema["$ref"].rsplit("/", 1)[-1]


@pytest.mark.parametrize(("path", "method"), OPERATIONS)
def test_operation_documents_the_error_envelope(path: str, method: str) -> None:
    """
    Condition:
    - One of the three import operations.

    Expected:
    - It exists, has a summary, and documents the error envelope as its default response.
    """
    operation = app.openapi()["paths"][path][method]

    assert operation["summary"]
    default = operation["responses"]["default"]["content"]["application/json"]["schema"]
    assert _ref(default) == "ErrorEnvelope"


def test_preview_documents_its_multipart_body() -> None:
    """
    Condition:
    - The preview route, which takes ``Request`` so a foreign upload is never read.

    Expected:
    - OpenAPI still documents ``file`` as binary, ``text`` and ``mapping`` as a multipart body.
    """
    body = app.openapi()["paths"][PREVIEW]["post"]["requestBody"]

    properties = body["content"]["multipart/form-data"]["schema"]["properties"]
    assert properties["file"] == {
        "type": "string",
        "format": "binary",
        "description": properties["file"]["description"],
    }
    assert properties["text"]["type"] == "string"
    assert properties["mapping"]["type"] == "string"


def test_preview_answers_201_with_the_preview_schema() -> None:
    """
    Condition:
    - The preview route's responses.

    Expected:
    - 201 with ``ImportPreviewResponse``, holding every field in the plan.
    """
    document = app.openapi()

    created = document["paths"][PREVIEW]["post"]["responses"]["201"]["content"]["application/json"]["schema"]
    assert _ref(created) == "ImportPreviewResponse"
    assert PREVIEW_FIELDS <= set(document["components"]["schemas"]["ImportPreviewResponse"]["properties"])


def test_get_import_answers_the_preview_schema() -> None:
    """
    Condition:
    - The read route's responses.

    Expected:
    - 200 with ``ImportPreviewResponse``.
    """
    ok = app.openapi()["paths"][GET_IMPORT]["get"]["responses"]["200"]["content"]["application/json"]["schema"]

    assert _ref(ok) == "ImportPreviewResponse"


def test_errors_route_documents_its_page_parameters() -> None:
    """
    Condition:
    - The error page route.

    Expected:
    - ``limit`` runs from 1 to 100, defaulting to 50, ``cursor`` is documented, and the response is the page schema.
    """
    operation = app.openapi()["paths"][GET_ERRORS]["get"]

    parameters = {parameter["name"]: parameter["schema"] for parameter in operation["parameters"]}
    assert (parameters["limit"]["minimum"], parameters["limit"]["maximum"], parameters["limit"]["default"]) == (
        1,
        100,
        50,
    )
    assert "cursor" in parameters
    ok = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert _ref(ok) == "ImportErrorPageResponse"
