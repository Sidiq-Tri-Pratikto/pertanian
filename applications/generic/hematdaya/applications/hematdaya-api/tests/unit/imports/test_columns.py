"""Header aliases and their structural errors. Port of L663–L675 plus D18."""

import pytest

from app.imports.model.models import StructuralError, StructuralReason, ValueKind
from app.imports.service.columns import ALIASES, Role, resolve_columns

MISSING_ASSET = "Kolom perangkat tidak ditemukan. Gunakan header asset, perangkat, mesin, device, nama atau alat."
MISSING_TIME = (
    "Kolom waktu tidak ditemukan. Gunakan timestamp (atau waktu/tanggal) atau pasangan interval_start dan interval_end."
)
MISSING_VALUE = "Kolom nilai tidak ditemukan. Gunakan energy_wh/energi_wh, average_power_w/daya_w, atau cumulative_wh."
ALIAS_ROLES = [
    *[(alias, Role.TIMESTAMP) for alias in ("timestamp", "waktu", "tanggal", "datetime", "time")],
    ("interval_start", Role.INTERVAL_START),
    ("interval_end", Role.INTERVAL_END),
    *[(alias, Role.ASSET) for alias in ("asset", "perangkat", "mesin", "device", "nama", "alat")],
    *[(alias, Role.ENERGY) for alias in ("energy_wh", "energi_wh", "wh", "energi")],
    *[(alias, Role.POWER) for alias in ("average_power_w", "daya_w", "watt", "daya", "power_w")],
    ("cumulative_wh", Role.COUNTER),
    *[(alias, Role.SOURCE) for alias in ("source", "sumber", "source_id")],
]


def _reasons(errors: list[StructuralError]) -> list[StructuralReason]:
    return [error.reason for error in errors]


def test_alias_table_is_exactly_the_decided_list() -> None:
    """
    Condition:
    - The alias table against D16's list.

    Expected:
    - Nothing is missing and nothing extra is accepted.
    """
    assert {(alias, role) for role, aliases in ALIASES.items() for alias in aliases} == set(ALIAS_ROLES)


@pytest.mark.parametrize(("alias", "role"), ALIAS_ROLES)
@pytest.mark.parametrize("spell", [str, str.upper, lambda alias: f"  {alias} "], ids=["lower", "upper", "spaced"])
def test_every_alias_resolves_to_its_role(alias: str, role: Role, spell: object) -> None:
    """
    Condition:
    - One alias, as written, upper-cased, or with surrounding spaces.

    Expected:
    - It resolves to its role at its position.
    """
    assert resolve_columns(["catatan", spell(alias)]).columns == {role: 1}


def test_energi_is_energy_never_a_counter() -> None:
    """
    Condition:
    - The ``energi`` alias (PRD §10.2).

    Expected:
    - It means interval energy, and the only value kind is interval energy.
    """
    columns = resolve_columns(["timestamp", "asset", "energi"])
    assert columns.columns[Role.ENERGY] == 2
    assert columns.value_kinds == [ValueKind.INTERVAL_ENERGY]


@pytest.mark.parametrize("header", ["energy_kwh", "kwh", "daya_kw"])
def test_kilo_units_are_ignored_never_read_as_base_units(header: str) -> None:
    """
    Condition:
    - A kWh or kW column, alone as the only value column.

    Expected:
    - It lands in ``ignored_columns``, and the file has ``missing_value``. Reading it would be a silent unit guess.
    """
    columns = resolve_columns(["timestamp", "asset", header])
    assert columns.ignored_columns == [header]
    assert columns.errors == [StructuralError(reason=StructuralReason.MISSING_VALUE, message=MISSING_VALUE)]


def test_two_headers_with_one_role_are_a_structural_error() -> None:
    """
    Condition:
    - ``energy_wh`` and ``wh`` in one file.

    Expected:
    - ``duplicate_role`` naming both as written.
    """
    assert resolve_columns(["timestamp", "asset", "energy_wh", "wh"]).errors == [
        StructuralError(
            reason=StructuralReason.DUPLICATE_ROLE,
            message='Kolom "energy_wh" dan "wh" memiliki arti yang sama. Hapus salah satunya.',
        )
    ]


def test_missing_roles_are_reported_in_order() -> None:
    """
    Condition:
    - Headers with no known alias.

    Expected:
    - Asset, time and value errors, in that order, with exact text.
    """
    assert resolve_columns(["foo", "bar"]).errors == [
        StructuralError(reason=StructuralReason.MISSING_ASSET, message=MISSING_ASSET),
        StructuralError(reason=StructuralReason.MISSING_TIME, message=MISSING_TIME),
        StructuralError(reason=StructuralReason.MISSING_VALUE, message=MISSING_VALUE),
    ]


@pytest.mark.parametrize("headers", [["interval_start", "asset", "wh"], ["interval_end", "asset", "wh"]])
def test_half_an_interval_is_missing_time(headers: list[str]) -> None:
    """
    Condition:
    - Only one interval bound.

    Expected:
    - ``missing_time``.
    """
    assert _reasons(resolve_columns(headers).errors) == [StructuralReason.MISSING_TIME]


def test_counter_needs_a_timestamp_column() -> None:
    """
    Condition:
    - A counter column with explicit interval bounds.

    Expected:
    - ``counter_needs_timestamp`` with exact text.
    """
    assert resolve_columns(["interval_start", "interval_end", "asset", "cumulative_wh"]).errors == [
        StructuralError(
            reason=StructuralReason.COUNTER_NEEDS_TIMESTAMP,
            message="Kolom cumulative_wh memerlukan kolom timestamp titik waktu.",
        )
    ]


@pytest.mark.parametrize(
    ("headers", "interval"),
    [
        (["Timestamp", "interval_start", "interval_end", "asset", "wh"], "interval_start"),
        (["Timestamp", "interval_end", "asset", "wh"], "interval_end"),
    ],
)
def test_timestamp_beside_interval_columns_is_rejected(headers: list[str], interval: str) -> None:
    """
    Condition:
    - A timestamp column next to an interval bound (D18).

    Expected:
    - ``competing_time_columns`` naming both columns as written; neither is silently dropped.
    """
    assert resolve_columns(headers).errors == [
        StructuralError(
            reason=StructuralReason.COMPETING_TIME_COLUMNS,
            message=(
                f'Kolom "Timestamp" dan "{interval}" sama-sama menyatakan waktu. '
                "Gunakan timestamp saja atau pasangan interval_start dan interval_end."
            ),
        )
    ]


def test_value_kinds_list_the_roles_present_in_order() -> None:
    """
    Condition:
    - All three value roles, written in reverse order.

    Expected:
    - Energy, power, counter, whatever the column order.
    """
    columns = resolve_columns(["timestamp", "asset", "cumulative_wh", "power_w", "energy_wh"])
    assert columns.value_kinds == [ValueKind.INTERVAL_ENERGY, ValueKind.AVERAGE_POWER, ValueKind.COUNTER]
    assert columns.errors == []


def test_extra_columns_are_ignored_as_written() -> None:
    """
    Condition:
    - An unknown column, with spaces around it.

    Expected:
    - It lands in ``ignored_columns`` as written after strip, and is no error.
    """
    columns = resolve_columns(["timestamp", "asset", "wh", " Catatan "])
    assert columns.ignored_columns == ["Catatan"]
    assert columns.errors == []
