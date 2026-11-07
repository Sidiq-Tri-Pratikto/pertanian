"""Streams resolved to assets and sources by identity, against the port of ``defaultMapping`` and L722–L733."""

import io
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.assets.model.models import (
    AssetModel,
    BindingModel,
    ExpectedUse,
    MeasurementKind,
    ScopeKind,
    SourceModel,
    SourceOrigin,
    TransportStatus,
)
from app.assets.service.service import SiteSnapshot
from app.core.errors.base import NotFoundError
from app.imports.model.models import IntervalBasis, MeaningAnswers, ValueKind
from app.imports.model.schema import ImportMappingRequest
from app.imports.service import mapping as mapping_module
from app.imports.service.classify import StreamFacts, stage_file
from app.imports.service.mapping import source_label
from app.imports.service.parser import parse

SITE = uuid4()
JAN = datetime(2026, 1, 1, tzinfo=UTC)
OCT_20 = datetime(2026, 10, 20, tzinfo=UTC)
OCT_21 = datetime(2026, 10, 21, tzinfo=UTC)
SCOPED = {"scope": "disjoint"}
OTHER_SOURCE = (
    '{asset} sudah memiliki sumber lain. Sumber ganda untuk satu beban tidak dijumlahkan; pilih "Buat perangkat baru" '
    "lalu tentukan sumber acuan di Cakupan & sumber."
)
SCOPE_TEXT = "Pilih apakah beban perangkat dalam berkas ini terukur terpisah."


def _asset(name: str = "Kulkas", *, location: str | None = None, archived: bool = False) -> AssetModel:
    return AssetModel(
        id=uuid4(),
        site_id=SITE,
        name=name,
        category="Pendingin",
        location=location,
        scope_kind=ScopeKind.DEVICE,
        parent_asset_id=None,
        expected_use=ExpectedUse.UNKNOWN,
        archived_at=JAN if archived else None,
    )


def _source(
    label: str = "Meter lain",
    *,
    origin: SourceOrigin = SourceOrigin.IMPORT,
    kind: MeasurementKind = MeasurementKind.INTERVAL_ENERGY,
) -> SourceModel:
    return SourceModel(
        id=uuid4(),
        site_id=SITE,
        label=label,
        origin=origin,
        measurement_kind=kind,
        cadence_seconds=3600,
        resolution_mwh=None,
        transport_status=TransportStatus.HISTORICAL,
    )


def _binding(
    asset: AssetModel, source: SourceModel, start: datetime = JAN, end: datetime | None = None
) -> BindingModel:
    return BindingModel(
        id=uuid4(),
        site_id=SITE,
        source_id=source.id,
        asset_id=asset.id,
        effective_from=start,
        effective_to=end,
        authoritative=True,
    )


def _snapshot(
    assets: list[AssetModel], sources: list[SourceModel] | None = None, bindings: list[BindingModel] | None = None
) -> SiteSnapshot:
    return SiteSnapshot(assets=assets, bindings=bindings or [], sources=sources or [], relations=[], containment=[])


def _stream(key: str = "kulkas", *names: str, **overrides: object) -> StreamFacts:
    values = {
        "stream_key": key,
        "names": dict.fromkeys(names or ("Kulkas",)),
        "kind": ValueKind.INTERVAL_ENERGY,
        "unit": "Wh",
        "period_start": OCT_20,
        "period_end": OCT_21,
    }
    return StreamFacts(**(values | overrides))


def _resolve(streams: list[StreamFacts], snapshot: SiteSnapshot, **answers: object) -> mapping_module.ResolvedMapping:
    return mapping_module.resolve_streams(streams, ImportMappingRequest(**(SCOPED | answers)), snapshot)


def _kinds(resolved: mapping_module.ResolvedMapping) -> list[str]:
    return [question.kind.value for question in resolved.questions]


def test_one_active_same_name_asset_is_the_default_target() -> None:
    """
    Condition:
    - One active asset whose name differs from the file's only in case.

    Expected:
    - It is the default target, with no question.
    """
    asset = _asset("KULKAS")

    resolved = _resolve([_stream()], _snapshot([asset]))

    assert resolved.questions == []
    assert resolved.streams[0].asset_id == asset.id


def test_no_same_name_asset_means_new() -> None:
    """
    Condition:
    - No asset has the name.

    Expected:
    - The stream targets a new asset with no source, and no question opens.
    """
    resolved = _resolve([_stream()], _snapshot([_asset("Pompa")]))

    assert resolved.questions == []
    assert (resolved.streams[0].asset_id, resolved.streams[0].source) == (None, None)


def test_two_same_name_assets_ask_with_their_context() -> None:
    """
    Condition:
    - PRD §5.1: two active assets share one name.

    Expected:
    - The exact question, with both candidates carrying location, category, scope kind and ID.
    """
    first, second = _asset(location="Dapur"), _asset(location="Gudang")

    resolved = _resolve([_stream()], _snapshot([first, second]))

    question = resolved.questions[0]
    assert question.kind.value == "asset_choice"
    assert (
        question.message
        == 'Ada lebih dari satu perangkat bernama "Kulkas". Pilih perangkat yang dimaksud atau buat baru.'
    )
    assert question.asset_name == "Kulkas"
    assert question.streams == ["kulkas"]
    candidates = {candidate.id: candidate for candidate in question.candidates}
    assert set(candidates) == {first.id, second.id}
    assert candidates[first.id].location == "Dapur"
    assert candidates[first.id].category == "Pendingin"
    assert candidates[first.id].scope_kind == "device"
    assert candidates[first.id].name == "Kulkas"


@pytest.mark.parametrize("answer", ["new", "first"], ids=["new", "by_id"])
def test_answering_the_choice_clears_it(answer: str) -> None:
    """
    Condition:
    - Two same-name assets, answered with a new asset or one of them by ID.

    Expected:
    - No question remains, and the answer decides the target.
    """
    first, second = _asset(), _asset()
    target = "new" if answer == "new" else str(first.id)

    resolved = _resolve([_stream()], _snapshot([first, second]), asset_map={"Kulkas": target})

    assert resolved.questions == []
    assert resolved.streams[0].asset_id == (None if answer == "new" else first.id)


def test_archived_assets_are_never_matched() -> None:
    """
    Condition:
    - An archived asset with the name, beside one active one, and an archived one alone.

    Expected:
    - Only the active asset counts, and an archived one alone means a new asset.
    """
    active, archived = _asset(), _asset(archived=True)

    assert _resolve([_stream()], _snapshot([active, archived])).streams[0].asset_id == active.id
    assert _resolve([_stream()], _snapshot([archived])).streams[0].asset_id is None


def test_unanswered_scope_asks() -> None:
    """
    Condition:
    - No scope answer.

    Expected:
    - The exact question comes first.
    """
    resolved = mapping_module.resolve_streams([_stream()], ImportMappingRequest(), _snapshot([]))

    assert _kinds(resolved) == ["scope"]
    assert resolved.questions[0].message == SCOPE_TEXT


@pytest.mark.parametrize("scope", ["disjoint", "unknown_overlap"])
def test_both_scope_answers_are_accepted(scope: str) -> None:
    """
    Condition:
    - Scope answered either way.

    Expected:
    - No question opens: unknown overlap stays visible on totals later, and does not block a preview.
    """
    assert _resolve([_stream()], _snapshot([]), scope=scope).questions == []


def test_other_source_over_the_period_asks() -> None:
    """
    Condition:
    - The target asset has another source whose binding covers the stream's period.

    Expected:
    - The exact question, never a silent addition.
    """
    asset, other = _asset(), _source()

    resolved = _resolve([_stream()], _snapshot([asset], [other], [_binding(asset, other)]))

    assert _kinds(resolved) == ["other_source"]
    assert resolved.questions[0].message == OTHER_SOURCE.format(asset="Kulkas")
    assert resolved.questions[0].asset_name == "Kulkas"


def test_other_source_is_cleared_by_choosing_new() -> None:
    """
    Condition:
    - D24: the same other source, with the stream mapped to a new asset.

    Expected:
    - No question: source authority is then chosen in 028.
    """
    asset, other = _asset(), _source()
    snapshot = _snapshot([asset], [other], [_binding(asset, other)])

    assert _resolve([_stream()], snapshot, asset_map={"Kulkas": "new"}).questions == []


@pytest.mark.parametrize(
    ("start", "end", "asks"),
    [
        (JAN, OCT_20, False),
        (JAN, OCT_20 + timedelta(seconds=1), True),
        (OCT_21, None, False),
        (OCT_21 - timedelta(seconds=1), None, True),
    ],
    ids=["closed_at_period_start", "closed_inside", "starts_at_period_end", "starts_inside"],
)
def test_other_source_is_time_aware(start: datetime, end: datetime | None, asks: bool) -> None:
    """
    Condition:
    - A binding at and around the edges of the stream's half-open period.

    Expected:
    - Only a binding overlapping the period asks.
    """
    asset, other = _asset(), _source()

    resolved = _resolve([_stream()], _snapshot([asset], [other], [_binding(asset, other, start, end)]))

    assert bool(resolved.questions) is asks


def test_other_source_reaches_a_counter_point_at_the_period_end() -> None:
    """
    Condition:
    - A counter stream whose last point is exactly where another binding starts.

    Expected:
    - The binding covers that point, so it asks.
    """
    asset, other = _asset(), _source(kind=MeasurementKind.COUNTER)
    stream = _stream(kind=ValueKind.COUNTER)

    resolved = _resolve([stream], _snapshot([asset], [other], [_binding(asset, other, OCT_21)]))

    assert _kinds(resolved) == ["other_source"]


def test_a_stream_with_no_readable_period_raises_no_source_question() -> None:
    """
    Condition:
    - A stream whose rows are all invalid or waiting on an answer, so it has no period.

    Expected:
    - No source question opens from it, because it has no rows to add. Any answer it waits for has its own question.
    """
    asset, other = _asset(), _source()
    stream = _stream(period_start=None, period_end=None)

    assert _resolve([stream], _snapshot([asset], [other], [_binding(asset, other)])).questions == []


def test_earlier_import_source_resolves_with_no_question() -> None:
    """
    Condition:
    - The target already has an import source with this stream's label and kind, whose binding closed long ago.

    Expected:
    - It resolves to that source, so a reimport matches its stored data.
    """
    asset, source = _asset(), _source(source_label("kulkas"))
    binding = _binding(asset, source, JAN, JAN + timedelta(days=1))

    resolved = _resolve([_stream()], _snapshot([asset], [source], [binding]))

    assert resolved.questions == []
    assert resolved.streams[0].source == source


@pytest.mark.parametrize(
    "source",
    [
        _source(source_label("kulkas"), kind=MeasurementKind.AVERAGE_POWER),
        _source(source_label("kulkas"), origin=SourceOrigin.SIMULATED),
        _source(source_label("lain")),
    ],
    ids=["other_kind", "other_origin", "other_label"],
)
def test_a_source_that_does_not_fully_match_is_another_source(source: SourceModel) -> None:
    """
    Condition:
    - A bound source that differs from the stream in kind, origin or label.

    Expected:
    - It does not resolve, and it asks ``other_source``.
    """
    asset = _asset()

    resolved = _resolve([_stream()], _snapshot([asset], [source], [_binding(asset, source)]))

    assert _kinds(resolved) == ["other_source"]
    assert resolved.streams[0].source is None


def test_a_matching_source_beside_another_still_asks() -> None:
    """
    Condition:
    - The target has its import source and another source over the period.

    Expected:
    - The stream resolves to its source, and the other one still asks.
    """
    asset, own, other = _asset(), _source(source_label("kulkas")), _source()
    snapshot = _snapshot([asset], [own, other], [_binding(asset, own), _binding(asset, other)])

    resolved = _resolve([_stream()], snapshot)

    assert resolved.streams[0].source == own
    assert _kinds(resolved) == ["other_source"]


def test_a_stream_with_two_names_asks() -> None:
    """
    Condition:
    - One source cell used under two asset names.

    Expected:
    - The exact question naming both.
    """
    resolved = _resolve([_stream("meter-1", "Kulkas", "Pompa")], _snapshot([]))

    assert _kinds(resolved) == ["stream_assets"]
    assert resolved.questions[0].message == (
        'Sumber "meter-1" dipakai oleh lebih dari satu perangkat: Kulkas, Pompa. '
        "Pisahkan sumbernya atau samakan nama perangkatnya."
    )
    assert resolved.questions[0].streams == ["meter-1"]


def test_a_name_written_two_ways_is_one_name() -> None:
    """
    Condition:
    - One stream with ``Kulkas`` and ``KULKAS``, which ``defaultMapping`` treats as one name.

    Expected:
    - No question.
    """
    assert _resolve([_stream("kulkas", "Kulkas", "KULKAS")], _snapshot([])).questions == []


def test_one_name_written_two_ways_mapped_apart_asks() -> None:
    """
    Condition:
    - One stream with ``Kulkas`` and ``KULKAS``, the two spellings answered with different targets.

    Expected:
    - The stream reaches two assets, so it asks.
    """
    resolved = _resolve([_stream("kulkas", "Kulkas", "KULKAS")], _snapshot([_asset()]), asset_map={"KULKAS": "new"})

    assert _kinds(resolved) == ["stream_assets"]


def test_two_streams_on_one_new_asset_ask() -> None:
    """
    Condition:
    - Two source cells under one new asset name.

    Expected:
    - The exact question.
    """
    resolved = _resolve([_stream("meter-1", "Kulkas"), _stream("meter-2", "kulkas")], _snapshot([]))

    assert _kinds(resolved) == ["asset_streams"]
    assert resolved.questions[0].message == (
        'Perangkat "Kulkas" menerima lebih dari satu sumber dalam berkas ini. Sumber ganda tidak dijumlahkan; '
        'pilih "Buat perangkat baru" lalu tentukan sumber acuan di Cakupan & sumber.'
    )
    assert resolved.questions[0].streams == ["meter-1", "meter-2"]


def test_two_names_mapped_to_one_asset_id_ask() -> None:
    """
    Condition:
    - Two names with their own streams, both answered with one asset ID.

    Expected:
    - The question names the stored asset, because two sources must never be added.
    """
    asset = _asset("Mesin utama")
    streams = [_stream("a", "A"), _stream("b", "B")]

    resolved = _resolve(streams, _snapshot([asset]), asset_map={"A": str(asset.id), "B": str(asset.id)})

    assert _kinds(resolved) == ["asset_streams"]
    assert 'Perangkat "Mesin utama" menerima' in resolved.questions[0].message
    assert resolved.questions[0].asset_name == "Mesin utama"


def test_a_long_list_of_names_is_bounded() -> None:
    """
    Condition:
    - One stream under a thousand names.

    Expected:
    - The message stays bounded.
    """
    names = [f"Perangkat {index}" for index in range(1000)]

    resolved = _resolve([_stream("meter", *names)], _snapshot([]))

    assert len(resolved.questions[0].message) <= 500


def test_oversized_and_invalid_names_raise_no_question() -> None:
    """
    Condition:
    - L725: a 61-character name and an empty name, beside two assets sharing the oversized name's first 60 characters.

    Expected:
    - Neither name yields a stream, so neither asks.
    """
    long_name = "K" * 61
    text = (
        "interval_start,interval_end,asset,energy_wh\n"
        f"2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,{long_name},1\n"
        "2026-10-20T01:00:00+07:00,2026-10-20T02:00:00+07:00,,1\n"
    )
    source = io.BytesIO(text.encode())
    parsed = parse(source, site_timezone="Asia/Jakarta", answers=MeaningAnswers())

    streams = stage_file(source, parsed).streams

    assert streams == []
    assert _resolve(streams, _snapshot([_asset(long_name), _asset(long_name)])).questions == []


def test_a_stream_of_invalid_values_still_asks_about_its_name() -> None:
    """
    Condition:
    - A readable name whose rows all have invalid values, with two assets of that name.

    Expected:
    - As in the prototype, the name still asks, because the file names it.
    """
    text = (
        "interval_start,interval_end,asset,energy_wh\n2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,Kulkas,dua\n"
    )
    source = io.BytesIO(text.encode())
    parsed = parse(source, site_timezone="Asia/Jakarta", answers=MeaningAnswers())

    resolved = _resolve(stage_file(source, parsed).streams, _snapshot([_asset(), _asset()]))

    assert _kinds(resolved) == ["asset_choice"]


@pytest.mark.parametrize("kind", ["unknown", "archived", "foreign"])
def test_a_target_outside_the_active_assets_is_not_found(kind: str) -> None:
    """
    Condition:
    - An asset ID that is unknown, archived, or of another site, even for a name the file does not hold.

    Expected:
    - ``NotFoundError``, so an asset's existence never leaks.
    """
    archived = _asset(archived=True)
    target: UUID = archived.id if kind == "archived" else uuid4()

    with pytest.raises(NotFoundError):
        _resolve([_stream()], _snapshot([archived]), asset_map={"Lain": str(target)})


@pytest.mark.parametrize(
    ("cadence", "minutes", "kind", "expected"),
    [
        (timedelta(hours=1), None, ValueKind.INTERVAL_ENERGY, 3600),
        (timedelta(seconds=3600, microseconds=400_000), None, ValueKind.INTERVAL_ENERGY, 3600),
        (timedelta(milliseconds=100), None, ValueKind.INTERVAL_ENERGY, 1),
        (None, 30, ValueKind.INTERVAL_ENERGY, 1800),
        (timedelta(hours=1), 30, ValueKind.INTERVAL_ENERGY, 1800),
        (None, None, ValueKind.INTERVAL_ENERGY, None),
        (timedelta(hours=1), None, ValueKind.COUNTER, None),
    ],
    ids=["hour", "rounded", "at_least_one", "declared", "declared_wins", "unknown", "counter"],
)
def test_cadence_seconds(cadence: timedelta | None, minutes: int | None, kind: ValueKind, expected: int | None) -> None:
    """
    Condition:
    - A stream's inferred cadence, declared duration and kind.

    Expected:
    - Whole seconds, at least one, with the declared duration deciding as it does for the rows. A counter has none.
    """
    answers = {} if minutes is None else {"interval_minutes": {"kulkas": minutes}}

    resolved = _resolve([_stream(cadence=cadence, kind=kind)], _snapshot([]), **answers)

    assert resolved.streams[0].cadence_seconds == expected


def test_a_resolved_stream_renders_every_stored_field() -> None:
    """
    Condition:
    - A stream resolved to an existing asset and its source.

    Expected:
    - Its JSON holds every field the plan's Data Model lists, with times in UTC.
    """
    asset, source = _asset(), _source(source_label("kulkas"))
    stream = _stream(interval_basis=IntervalBasis.INFERRED, cadence=timedelta(hours=1))

    resolved = _resolve([stream], _snapshot([asset], [source], [_binding(asset, source)]))

    assert resolved.streams[0].as_json() == {
        "stream_key": "kulkas",
        "label": "Impor CSV · kulkas",
        "asset_name": "Kulkas",
        "asset_id": str(asset.id),
        "source_id": str(source.id),
        "kind": "interval_energy",
        "unit": "Wh",
        "cadence_seconds": 3600,
        "period_start": "2026-10-20T00:00:00Z",
        "period_end": "2026-10-21T00:00:00Z",
        "interval_basis": "inferred",
    }


def test_source_label_keeps_short_keys_unchanged() -> None:
    """
    Condition:
    - A key of 108 characters, whose label just fits 120.

    Expected:
    - Today's format, because stored sources must keep matching on reimport.
    """
    key = "k" * 108

    assert source_label(key) == f"Impor CSV · {key}"
    assert len(source_label(key)) == 120


def test_source_label_fits_a_name_that_lengthens_when_lower_cased() -> None:
    """
    Condition:
    - 60 × ``İ``, valid as a name, lower-cases to a 120-character key (D16).

    Expected:
    - A label of at most 120 characters, the same on every call.
    """
    key = ("İ" * 60).lower()

    assert len(key) == 120
    assert len(source_label(key)) <= 120
    assert source_label(key) == source_label(key)


def test_source_label_keeps_long_keys_distinct() -> None:
    """
    Condition:
    - Two 120-character keys sharing the first 103 characters of their label.

    Expected:
    - Different labels, so two streams never share a source.
    """
    first, second = "k" * 119 + "a", "k" * 119 + "b"

    assert len(source_label(first)) == len(source_label(second)) == 120
    assert source_label(first)[:103] == source_label(second)[:103]
    assert source_label(first) != source_label(second)


def test_resolve_source_matches_a_stored_long_label() -> None:
    """
    Condition:
    - A stored source carrying the shortened label of a long key.

    Expected:
    - The stream resolves to it, so a reimport finds its data.
    """
    key = ("İ" * 60).lower()
    asset, source = _asset(), _source(source_label(key))
    snapshot = _snapshot([asset], [source], [_binding(asset, source)])

    assert mapping_module.resolve_source(asset.id, key, ValueKind.INTERVAL_ENERGY, snapshot) == source
