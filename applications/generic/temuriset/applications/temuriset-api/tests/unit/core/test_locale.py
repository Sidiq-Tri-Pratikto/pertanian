"""English for every public message, chosen by the request header (spec 050)."""

from app.core.errors import codes, public
from app.core.locale import _request_locale, as_locale


def test_every_public_code_status_and_field_message_has_english() -> None:
    """
    Condition:
    - The Indonesian catalogs of codes, statuses and field types.

    Expected:
    - Each has an English message, and none is left in Indonesian by mistake.
    """
    assert set(public.PUBLIC_ERROR_BY_CODE) <= set(public._EN_BY_CODE)
    assert set(public.PUBLIC_ERROR_BY_STATUS) <= set(public._EN_BY_STATUS)
    assert set(public._FIELD_MESSAGES) <= set(public._FIELD_MESSAGES_EN)
    for code, message in public._EN_BY_CODE.items():
        if code in public.PUBLIC_ERROR_BY_CODE and public.PUBLIC_ERROR_BY_CODE[code].message:
            assert message != public.PUBLIC_ERROR_BY_CODE[code].message, code


def test_lookups_follow_the_request_language_and_keep_codes_and_recovery() -> None:
    """
    Condition:
    - The same lookups in Indonesian, then in English.

    Expected:
    - The message changes; the public code, status and recovery do not.
    """
    code = next(iter(public.PUBLIC_ERROR_BY_CODE))
    indonesian = public.public_error_for_code(codes.APP_RATE_LIMITED)
    token = _request_locale.set("en")
    try:
        english = public.public_error_for_code(codes.APP_RATE_LIMITED)
        assert english.message == "Too many code requests. Wait a moment and try again."
        assert (english.code, english.http_status, english.recovery) == (
            indonesian.code,
            indonesian.http_status,
            indonesian.recovery,
        )
        assert public.public_error_for_status(404).message.startswith("The requested item was not found")
        assert public.public_error_for_status(599).message.startswith("The request could not be completed")
        assert public.field_message("missing") == "This field is required."
        assert public.public_error_for_code(code).message
    finally:
        _request_locale.reset(token)
    assert public.field_message("missing") == "Isian ini wajib diisi."


def test_only_en_selects_english() -> None:
    """
    Condition:
    - Header values in different forms.

    Expected:
    - ``en`` in any case is English; anything else is Indonesian.
    """
    assert [as_locale(value) for value in ("en", " EN ", "id", "fr", None, "")] == ["en", "en", "id", "id", "id", "id"]
