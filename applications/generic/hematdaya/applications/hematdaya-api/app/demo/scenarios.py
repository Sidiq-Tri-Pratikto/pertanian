"""The named demo scenarios, built as pure plans. Seeding them belongs to the demo session service."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from app.assets.model.models import ExpectedUse, RelationKind, ScopeKind, SourceOrigin, TransportStatus
from app.core.errors.base import NotFoundError
from app.demo.fixtures import (
    FACTORY,
    HOUSEHOLD,
    NOW_CURRENT,
    NOW_MAIN,
    TIMEZONE,
    FixtureAsset,
    ReadingSpec,
    WhRule,
    hourly,
    in_selected_week,
)
from app.sites.model.models import SiteContext

SYNTHETIC_TARIFF = {
    "milli_rupiah_per_kwh": 1_500_000,
    "provenance": "synthetic",
    "label": "Tarif simulasi, bukan tarif PLN",
}
INDUSTRY_SCHEDULE = {"days": [0, 1, 2, 3, 4, 5], "start": "07:00", "end": "17:00", "label": "Jadwal lokasi v1"}
DEMO_SOURCE_LABEL = "Sumber demo (simulasi)"


@dataclass(frozen=True)
class Scenario:
    """A catalog entry clients choose from."""

    id: str
    segment: str
    name: str
    description: str


@dataclass(frozen=True)
class AssetSpec:
    """An asset to create."""

    key: str
    name: str
    scope_kind: ScopeKind
    category: str | None = None
    location: str | None = None
    expected_use: ExpectedUse = ExpectedUse.UNKNOWN


@dataclass(frozen=True)
class SourceSpec:
    """A source to create and bind. Unauthoritative bindings model unresolved alternative sources."""

    key: str
    asset_key: str
    label: str
    origin: SourceOrigin = SourceOrigin.SIMULATED
    transport_status: TransportStatus = TransportStatus.NONE
    cadence_seconds: int = 3600
    resolution_mwh: int = 1000
    authoritative: bool = True


@dataclass(frozen=True)
class RelationSpec:
    """What is known about two assets' loads."""

    from_key: str
    to_key: str
    kind: RelationKind


@dataclass(frozen=True)
class ScenarioPlan:
    """Everything a scenario seeds, with no database access. Optional inputs stay declarative until their
    modules store them (tariff 018, schedule 030, metric 032)."""

    scenario: Scenario
    site_name: str
    context: SiteContext
    timezone: str
    virtual_now: datetime
    initial_period: dict[str, str]
    assets: tuple[AssetSpec, ...] = ()
    sources: tuple[SourceSpec, ...] = ()
    readings: tuple[ReadingSpec, ...] = ()
    relations: tuple[RelationSpec, ...] = ()
    tariff: dict[str, Any] | None = None
    schedule: dict[str, Any] | None = None
    metric: dict[str, Any] | None = None
    client_offline: bool = False
    labels: tuple[str, ...] = field(default=("Demo dengan data simulasi",))


SCENARIOS = (
    Scenario(
        "h-base",
        "household",
        "Rumah tangga · dasar",
        "4 perangkat tanpa AC, tarif simulasi Rp1.500/kWh, tanpa jadwal atau output.",
    ),
    Scenario(
        "h-notariff", "household", "Rumah tangga · tanpa tarif", "Data sama; tarif belum diatur, biaya tidak dihitung."
    ),
    Scenario(
        "h-change", "household", "Rumah tangga · perubahan TV", "+200 Wh pada TV pukul 19.00 selama 19–25 Oktober."
    ),
    Scenario("h-current", "household", "Rumah tangga · periode berjalan", "Waktu virtual Rabu 21 Oktober 2026 12.00."),
    Scenario(
        "h-learning-partial",
        "household",
        "Belajar + tanpa tarif + sebagian data",
        "Riwayat mulai 12 Oktober, Pompa Air tanpa data 24–25 Oktober, Kulkas tanpa data 22 Oktober 14.00–16.00.",
    ),
    Scenario("h-zero", "household", "Nol terukur + tanpa tarif", "Semua interval tercatat 0 Wh dengan data lengkap."),
    Scenario(
        "h-stale-offline",
        "household",
        "Sumber tidak diperbarui + offline",
        "Router (simulasi koneksi) terakhir 25 Oktober 18.00; perangkat Anda offline.",
    ),
    Scenario(
        "h-historical-offline",
        "household",
        "Data historis + offline",
        "Tampilan data historis dengan data simulasi; perangkat Anda offline.",
    ),
    Scenario(
        "h-scope",
        "household",
        "Meter utama, sumber ganda, tumpang tindih",
        "Meter utama mencakup Kulkas, Router dan TV; Kulkas punya dua sumber; hubungan Pompa Air dengan Meter utama"
        " belum diketahui.",
    ),
    Scenario(
        "empty",
        "household",
        "Ruang kerja kosong",
        "Belum ada perangkat atau data. Mulai dari impor atau tambah perangkat.",
    ),
    Scenario(
        "i-base",
        "industry",
        "Industri · dasar",
        "Oven, Kompresor, Mesin Press, Lampu Area; tanpa jadwal dan tanpa output.",
    ),
    Scenario(
        "i-optional",
        "industry",
        "Industri · jadwal + output aktual",
        "Jadwal Senin–Sabtu 07.00–17.00 dan 2.880 unit per minggu.",
    ),
    Scenario(
        "i-change",
        "industry",
        "Industri · kompresor di luar jadwal",
        "+500 Wh Kompresor pukul 18.00 pada enam hari produksi 19–24 Oktober; jadwal aktif.",
    ),
    Scenario("i-current", "industry", "Industri · periode berjalan", "Waktu virtual Rabu 21 Oktober 2026 12.00."),
)
_BY_ID = {scenario.id: scenario for scenario in SCENARIOS}
_TARIFF_SCENARIOS = {"h-base", "h-change", "h-current", "h-stale-offline", "h-historical-offline", "h-scope"}
LAST_WEEK = {"preset": "last_7_days", "start_date": "2026-10-19", "end_date": "2026-10-25"}


def _wib(*parts: int) -> datetime:
    """Return a WIB wall time as UTC. WIB has no daylight saving, so the offset is fixed."""
    return datetime(*parts, tzinfo=UTC) - timedelta(hours=7)


def _disjoint(keys: list[str]) -> tuple[RelationSpec, ...]:
    return tuple(
        RelationSpec(first, second, RelationKind.DISJOINT) for i, first in enumerate(keys) for second in keys[i + 1 :]
    )


def _rule(scenario_id: str, asset: FixtureAsset) -> WhRule:
    if scenario_id == "h-change" and asset.key == "tv":
        return lambda h, wd, d: asset.wh(h, wd, d) + (200 if h == 19 and in_selected_week(d) else 0)
    if scenario_id == "i-change" and asset.key == "kompresor":
        return lambda h, wd, d: asset.wh(h, wd, d) + (500 if h == 18 and wd <= 5 and in_selected_week(d) else 0)
    if scenario_id == "h-zero":
        return lambda h, wd, d: 0
    return asset.wh


def build_scenario(scenario_id: str) -> ScenarioPlan:
    """Build a scenario's plan. Pure and deterministic: the same ID always gives the same plan.

    Args:
        scenario_id (str): A catalog ID.

    Returns:
        ScenarioPlan: The plan.

    Raises:
        NotFoundError: For an unknown ID.
    """
    scenario = _BY_ID.get(scenario_id)
    if scenario is None:
        raise NotFoundError()
    industry = scenario.segment == "industry"
    base = {
        "scenario": scenario,
        "site_name": "Bengkel Roti Sejahtera (demo)" if industry else "Rumah Bandung (demo)",
        "context": SiteContext.INDUSTRY if industry else SiteContext.HOUSEHOLD,
        "timezone": TIMEZONE,
        "virtual_now": NOW_MAIN,
        "initial_period": LAST_WEEK,
    }
    if scenario_id == "empty":
        return ScenarioPlan(**{**base, "site_name": "Lokasi saya (demo)", "context": SiteContext.UNSPECIFIED})

    definitions = FACTORY if industry else HOUSEHOLD
    assets = [AssetSpec(d.key, d.name, ScopeKind.DEVICE, d.category, d.location, d.expected_use) for d in definitions]
    sources: list[SourceSpec] = []
    readings: list[ReadingSpec] = []
    for definition in definitions:
        source = SourceSpec(f"src-{definition.key}", definition.key, DEMO_SOURCE_LABEL)
        options: dict[str, Any] = {}
        if scenario_id == "h-learning-partial":
            options["start"] = _wib(2026, 10, 12)
            if definition.key == "pompa":
                options["until"] = _wib(2026, 10, 24)
            if definition.key == "kulkas":
                options["skip"] = lambda t: _wib(2026, 10, 22, 14) <= t < _wib(2026, 10, 22, 16)
        if scenario_id == "h-stale-offline" and definition.key == "router":
            options["until"] = _wib(2026, 10, 25, 18)
            source = SourceSpec(
                source.key,
                definition.key,
                "Simulasi koneksi · colokan Router",
                transport_status=TransportStatus.SIMULATED_LIVE,
            )
        if scenario_id == "h-historical-offline":
            source = SourceSpec(
                source.key, definition.key, "Data historis (simulasi)", transport_status=TransportStatus.HISTORICAL
            )
        if scenario_id == "h-scope" and definition.key == "kulkas":
            # Two alternative sources for one load, both unresolved candidates with identical values.
            source = SourceSpec(source.key, definition.key, DEMO_SOURCE_LABEL, authoritative=False)
            sources.append(
                SourceSpec("src-kulkas-plug", "kulkas", "Colokan simulasi Kulkas (sumber kedua)", authoritative=False)
            )
            readings.extend(hourly("src-kulkas-plug", lambda h, wd, d: 50 if h < 20 else 0))
            readings.extend(hourly(source.key, lambda h, wd, d: 50 if h < 20 else 0))
            sources.append(source)
            continue
        sources.append(source)
        readings.extend(hourly(source.key, _rule(scenario_id, definition), **options))

    relations = list(_disjoint([d.key for d in definitions]))
    extra: dict[str, Any] = {}
    if scenario_id == "h-scope":
        assets.append(AssetSpec("meter", "Meter utama", ScopeKind.SITE_TOTAL, "Meter rumah", "Teras"))
        sources.append(SourceSpec("src-meter", "meter", DEMO_SOURCE_LABEL))
        readings.extend(hourly("src-meter", lambda h, wd, d: 400 if h < 20 else 500))
        relations += [RelationSpec("meter", key, RelationKind.CONTAINS) for key in ("kulkas", "router", "tv")]
        relations.append(RelationSpec("meter", "pompa", RelationKind.UNKNOWN_OVERLAP))
        extra["initial_period"] = {"preset": "range", "start_date": "2026-10-25", "end_date": "2026-10-25"}
    if scenario_id in ("h-current", "i-current"):
        extra["virtual_now"] = NOW_CURRENT
        extra["initial_period"] = {"preset": "today", "start_date": "2026-10-21", "end_date": "2026-10-21"}
    if scenario_id in _TARIFF_SCENARIOS or industry:
        extra["tariff"] = SYNTHETIC_TARIFF
    if scenario_id in ("i-optional", "i-change"):
        extra["schedule"] = INDUSTRY_SCHEDULE
    if scenario_id == "i-optional":
        extra["metric"] = {
            "name": "Energi per roti",
            "asset_keys": [d.key for d in definitions],
            "unit": "unit",
            "product": "Roti tawar",
            "method": "actual",
            "quantity": 2880,
            "start_date": "2026-10-19",
            "end_date": "2026-10-25",
        }
    if scenario_id in ("h-stale-offline", "h-historical-offline"):
        extra["client_offline"] = True
    return ScenarioPlan(
        **{**base, **extra},
        assets=tuple(assets),
        sources=tuple(sources),
        readings=tuple(readings),
        relations=tuple(relations),
    )
