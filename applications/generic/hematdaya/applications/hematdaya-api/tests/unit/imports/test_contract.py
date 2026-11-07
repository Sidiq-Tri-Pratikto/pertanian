"""The import routes' published contract."""

import pytest

from app.main import app

PREVIEW = "/api/v1/sites/{site_id}/imports/preview"
GET_IMPORT = "/api/v1/imports/{import_id}"
GET_ERRORS = "/api/v1/imports/{import_id}/errors"
COMMIT = "/api/v1/imports/{import_id}/commit"
OPERATIONS = [(PREVIEW, "post"), (GET_IMPORT, "get"), (GET_ERRORS, "get"), (COMMIT, "post")]
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
    - One of the import operations.

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


def test_commit_requires_its_idempotency_key() -> None:
    """
    Condition:
    - The commit route's parameters.

    Expected:
    - A required ``Idempotency-Key`` header with the same pattern as feedback's (D5).
    """
    operation = app.openapi()["paths"][COMMIT]["post"]

    header = next(parameter for parameter in operation["parameters"] if parameter["name"] == "Idempotency-Key")
    assert header["in"] == "header"
    assert header["required"] is True
    assert header["schema"]["pattern"] == "^[A-Za-z0-9_-]{22,128}$"


def test_commit_documents_its_request_and_response() -> None:
    """
    Condition:
    - The commit route's body and responses.

    Expected:
    - A body of ``ImportCommitRequest`` holding only ``acknowledge_skipped``, and a 200 of ``ImportCommitResponse``,
      holding every field in the plan including ``replayed``.
    """
    document = app.openapi()
    operation = document["paths"][COMMIT]["post"]
    schemas = document["components"]["schemas"]

    body = operation["requestBody"]["content"]["application/json"]["schema"]
    assert _ref(body) == "ImportCommitRequest"
    assert set(schemas["ImportCommitRequest"]["properties"]) == {"acknowledge_skipped"}
    assert schemas["ImportCommitRequest"]["additionalProperties"] is False
    ok = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert _ref(ok) == "ImportCommitResponse"
    assert set(schemas["ImportCommitResponse"]["properties"]) == {
        "import_id",
        "status",
        "rows_added",
        "rows_skipped",
        "rows_duplicate",
        "assets_created",
        "assets_mapped",
        "period",
        "affected_from",
        "affected_to",
        "rows_after_site_clock",
        "acknowledge_skipped",
        "committed_at",
        "replayed",
    }


def test_get_import_carries_a_nullable_result() -> None:
    """
    Condition:
    - The stored import's response schema.

    Expected:
    - ``result`` is the first result or null, and it is not the commit response, because only a POST says ``replayed``.
    """
    schemas = app.openapi()["components"]["schemas"]

    variants = schemas["ImportPreviewResponse"]["properties"]["result"]["anyOf"]

    assert {"type": "null"} in variants
    assert _ref(next(variant for variant in variants if "$ref" in variant)) == "ImportCommitResultResponse"
    assert "replayed" not in schemas["ImportCommitResultResponse"]["properties"]
