"""Clock, money and cursor tests."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import BaseModel, ValidationError

from app.core import clock
from app.core.errors.base import RequestInvalidError
from app.core.types import CurrencyCode, Limit, Money, Page, decode_cursor, encode_cursor


class Amount(BaseModel):
    """A money field as clients send it."""

    amount: Money
    currency: CurrencyCode


class Listing(BaseModel):
    """A list request."""

    limit: Limit


def test_frozen_clock_is_the_product_time_and_restores() -> None:
    """
    Condition:
    - Product time is frozen, then released.

    Expected:
    - ``now()`` returns the frozen instant in UTC, then the wall clock again.
    """
    at = datetime(2026, 11, 5, 16, tzinfo=UTC) + timedelta(hours=7)

    with clock.frozen(at):
        assert clock.now() == at
    assert abs(clock.now() - datetime.now(UTC)) < timedelta(seconds=5)


def test_naive_time_cannot_freeze_the_clock() -> None:
    """
    Condition:
    - A time without a zone.

    Expected:
    - Refused: product time is always an instant.
    """
    with pytest.raises(ValueError, match="time zone aware"), clock.frozen(datetime(2026, 11, 5)):
        pass


@pytest.mark.parametrize("amount", ["0", "15000000", "1.5", "9999999999999999.9999"])
def test_money_accepts_decimal_strings(amount: str) -> None:
    """
    Condition:
    - A decimal string within 16 integer and 4 fraction digits.

    Expected:
    - Accepted unchanged.
    """
    assert Amount(amount=amount, currency="IDR").amount == amount


@pytest.mark.parametrize("amount", [1500, 1.5, "1,5", "-1", "1.23456", "12345678901234567", ""])
def test_money_rejects_numbers_and_malformed_strings(amount: object) -> None:
    """
    Condition:
    - A JSON number, a negative, a comma, too many digits or nothing.

    Expected:
    - Rejected, so no client float ever becomes money.
    """
    with pytest.raises(ValidationError):
        Amount.model_validate({"amount": amount, "currency": "IDR"})


@pytest.mark.parametrize("currency", ["idr", "RUPIAH", "ID"])
def test_currency_is_three_capital_letters(currency: str) -> None:
    """
    Condition:
    - Not an ISO 4217 shaped code.

    Expected:
    - Rejected.
    """
    with pytest.raises(ValidationError):
        Amount(amount="1", currency=currency)


@pytest.mark.parametrize("limit", [0, 101])
def test_page_limit_is_between_one_and_one_hundred(limit: int) -> None:
    """
    Condition:
    - A limit outside 1–100.

    Expected:
    - Rejected.
    """
    with pytest.raises(ValidationError):
        Listing(limit=limit)


def test_cursor_round_trips_and_pages_carry_it() -> None:
    """
    Condition:
    - A position is encoded into a page's cursor.

    Expected:
    - Decoding returns the same position.
    """
    position = {"created_at": "2026-11-05T09:00:00+00:00", "id": "a"}
    page = Page[str](items=["a"], next_cursor=encode_cursor(position))

    assert page.next_cursor is not None
    assert decode_cursor(page.next_cursor) == position


@pytest.mark.parametrize("cursor", ["%%%", "bm90IGpzb24", "WzFd"])
def test_foreign_cursor_is_a_bad_request(cursor: str) -> None:
    """
    Condition:
    - A cursor this service did not make: not base64, not JSON, or not an object.

    Expected:
    - ``BAD_REQUEST`` with an Indonesian message telling the client to reload the list.
    """
    with pytest.raises(RequestInvalidError) as raised:
        decode_cursor(cursor)

    assert str(raised.value) == "Penanda halaman tidak dikenali. Muat ulang daftar dari awal lalu coba lagi."
