"""Maps headers to roles."""

from dataclasses import dataclass
from enum import StrEnum

from app.imports.model.models import StructuralError, StructuralReason, ValueKind


class Role(StrEnum):
    """What a column means."""

    TIMESTAMP = "timestamp"
    INTERVAL_START = "interval_start"
    INTERVAL_END = "interval_end"
    ASSET = "asset"
    ENERGY = "energy"
    POWER = "power"
    COUNTER = "counter"
    SOURCE = "source"


ALIASES: dict[Role, tuple[str, ...]] = {
    Role.TIMESTAMP: ("timestamp", "waktu", "tanggal", "datetime", "time"),
    Role.INTERVAL_START: ("interval_start",),
    Role.INTERVAL_END: ("interval_end",),
    Role.ASSET: ("asset", "perangkat", "mesin", "device", "nama", "alat"),
    Role.ENERGY: ("energy_wh", "energi_wh", "wh", "energi"),
    Role.POWER: ("average_power_w", "daya_w", "watt", "daya", "power_w"),
    Role.COUNTER: ("cumulative_wh",),
    Role.SOURCE: ("source", "sumber", "source_id"),
}
VALUE_ROLES: dict[ValueKind, Role] = {
    ValueKind.INTERVAL_ENERGY: Role.ENERGY,
    ValueKind.AVERAGE_POWER: Role.POWER,
    ValueKind.COUNTER: Role.COUNTER,
}
_ROLE_BY_ALIAS = {alias: role for role, aliases in ALIASES.items() for alias in aliases}


@dataclass(frozen=True)
class ColumnMap:
    """What a header row means.

    Attributes:
        columns (dict[Role, int]): Position of each role present.
        ignored_columns (list[str]): Headers with no role, as written after strip.
        value_kinds (list[ValueKind]): Value roles present, in the order energy, power, counter.
        errors (list[StructuralError]): Why these headers cannot be read.
    """

    columns: dict[Role, int]
    ignored_columns: list[str]
    value_kinds: list[ValueKind]
    errors: list[StructuralError]


def resolve_columns(headers: list[str]) -> ColumnMap:
    """Match headers to roles, ignoring case and surrounding spaces.

    Args:
        headers (list[str]): The header cells.

    Returns:
        ColumnMap: Their meaning, with any structural errors.
    """
    names = [header.strip() for header in headers]
    columns: dict[Role, int] = {}
    ignored: list[str] = []
    errors: list[StructuralError] = []
    for position, name in enumerate(names):
        role = _ROLE_BY_ALIAS.get(name.lower())
        if role is None:
            ignored.append(name)
        elif role in columns:
            errors.append(
                StructuralError(
                    reason=StructuralReason.DUPLICATE_ROLE,
                    message=(
                        f'Kolom "{names[columns[role]]}" dan "{name}" memiliki arti yang sama. Hapus salah satunya.'
                    ),
                )
            )
        else:
            columns[role] = position
    errors += _missing_roles(names, columns)
    value_kinds = [kind for kind, role in VALUE_ROLES.items() if role in columns]
    return ColumnMap(columns=columns, ignored_columns=ignored, value_kinds=value_kinds, errors=errors)


def _missing_roles(names: list[str], columns: dict[Role, int]) -> list[StructuralError]:
    errors: list[StructuralError] = []
    has_timestamp = Role.TIMESTAMP in columns
    bound = columns.get(Role.INTERVAL_START, columns.get(Role.INTERVAL_END))
    if has_timestamp and bound is not None:
        errors.append(
            StructuralError(
                reason=StructuralReason.COMPETING_TIME_COLUMNS,
                message=(
                    f'Kolom "{names[columns[Role.TIMESTAMP]]}" dan "{names[bound]}" sama-sama menyatakan waktu. '
                    "Gunakan timestamp saja atau pasangan interval_start dan interval_end."
                ),
            )
        )
    if Role.ASSET not in columns:
        errors.append(
            StructuralError(
                reason=StructuralReason.MISSING_ASSET,
                message=(
                    "Kolom perangkat tidak ditemukan. Gunakan header asset, perangkat, mesin, device, nama atau alat."
                ),
            )
        )
    if not has_timestamp and (Role.INTERVAL_START not in columns or Role.INTERVAL_END not in columns):
        errors.append(
            StructuralError(
                reason=StructuralReason.MISSING_TIME,
                message=(
                    "Kolom waktu tidak ditemukan. Gunakan timestamp (atau waktu/tanggal) "
                    "atau pasangan interval_start dan interval_end."
                ),
            )
        )
    if not any(role in columns for role in VALUE_ROLES.values()):
        errors.append(
            StructuralError(
                reason=StructuralReason.MISSING_VALUE,
                message=(
                    "Kolom nilai tidak ditemukan. Gunakan energy_wh/energi_wh, average_power_w/daya_w, "
                    "atau cumulative_wh."
                ),
            )
        )
    if Role.COUNTER in columns and not has_timestamp:
        errors.append(
            StructuralError(
                reason=StructuralReason.COUNTER_NEEDS_TIMESTAMP,
                message="Kolom cumulative_wh memerlukan kolom timestamp titik waktu.",
            )
        )
    return errors
