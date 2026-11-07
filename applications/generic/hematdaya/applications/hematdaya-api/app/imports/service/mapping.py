"""Maps a file's streams to assets and sources by identity, never by name alone."""

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.assets.model.models import AssetModel, BindingModel, SourceModel, SourceOrigin
from app.assets.service.service import SiteSnapshot
from app.core.errors.base import NotFoundError
from app.imports.model.models import ValueKind
from app.imports.model.schema import (
    AssetCandidateResponse,
    ImportMappingRequest,
    ImportQuestionKind,
    ImportQuestionResponse,
)
from app.imports.service.classify import StreamFacts, bound_text
from app.imports.service.parser import MAX_INTERVAL_MINUTES, MIN_INTERVAL_MINUTES

_NEW = "new"
_MAX_SOURCE_LABEL = 120
_LABEL_KEPT = 103
_LABEL_HASH = 16
_SECOND_SOURCE_NEXT_STEP = 'pilih "Buat perangkat baru" lalu tentukan sumber acuan di Cakupan & sumber.'


def source_label(stream_key: str) -> str:
    """Return the fixed label that ties a stream to its stored source. ``sources`` has no stream column.

    A label that fits ``sources.label`` must never change its format, or reimports of stored sources stop matching.
    ``lower()`` can double a name, so a longer one keeps its start and a hash of the key, which keeps two keys apart.

    Args:
        stream_key (str): The stream.

    Returns:
        str: The label, at most 120 characters.
    """
    label = f"Impor CSV · {stream_key}"
    if len(label) <= _MAX_SOURCE_LABEL:
        return label
    digest = hashlib.sha256(stream_key.encode()).hexdigest()[:_LABEL_HASH]
    return f"{label[:_LABEL_KEPT]}·{digest}"


def resolve_source(asset_id: UUID, stream_key: str, kind: ValueKind, snapshot: SiteSnapshot) -> SourceModel | None:
    """Find the stored source a stream already feeds: bound to its asset, imported, of its kind, with its label.

    Args:
        asset_id (UUID): The target asset.
        stream_key (str): The stream.
        kind (ValueKind): What the stream's values mean.
        snapshot (SiteSnapshot): The site's assets, sources and bindings.

    Returns:
        SourceModel | None: The source, or None when this stream has none yet.
    """
    bound = {binding.source_id for binding in snapshot.bindings if binding.asset_id == asset_id}
    label = source_label(stream_key)
    matches = [
        source
        for source in snapshot.sources
        if source.id in bound
        and source.origin is SourceOrigin.IMPORT
        and source.measurement_kind.value == kind.value
        and source.label == label
    ]
    return min(matches, key=lambda source: source.id, default=None)


def _instant(moment: datetime | None) -> str | None:
    return None if moment is None else moment.isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class ResolvedStream:
    """A stream with its target, as far as the answers so far decide it.

    Attributes:
        facts (StreamFacts): What the file says about it.
        asset_id (UUID | None): Its target asset; None for a new asset or an open choice.
        source (SourceModel | None): The stored source it already feeds.
        cadence_seconds (int | None): The cadence its source should declare.
    """

    facts: StreamFacts
    asset_id: UUID | None
    source: SourceModel | None
    cadence_seconds: int | None

    def as_json(self) -> dict[str, Any]:
        """Render it for ``imports.mapping``, as 026 reads it.

        Returns:
            dict[str, Any]: The stored stream.
        """
        facts = self.facts
        return {
            "stream_key": facts.stream_key,
            "label": source_label(facts.stream_key),
            "asset_name": next(iter(facts.names)),
            "asset_id": None if self.asset_id is None else str(self.asset_id),
            "source_id": None if self.source is None else str(self.source.id),
            "kind": None if facts.kind is None else facts.kind.value,
            "unit": facts.unit,
            "cadence_seconds": self.cadence_seconds,
            "period_start": _instant(facts.period_start),
            "period_end": _instant(facts.period_end),
            "interval_basis": None if facts.interval_basis is None else facts.interval_basis.value,
        }


@dataclass(frozen=True, slots=True)
class ResolvedMapping:
    """Every stream's target, and what must be answered before they can be trusted.

    Attributes:
        streams (list[ResolvedStream]): Streams in first-seen order.
        questions (list[ImportQuestionResponse]): Open questions, scope first.
    """

    streams: list[ResolvedStream]
    questions: list[ImportQuestionResponse]


def require_active_targets(request: ImportMappingRequest, snapshot: SiteSnapshot) -> None:
    """Refuse an answer naming anything but an active asset of this site, so no asset's existence leaks.

    Args:
        request (ImportMappingRequest): The answers.
        snapshot (SiteSnapshot): The site's assets.

    Raises:
        NotFoundError: When an asset ID is unknown here, archived, or another site's.
    """
    active = {asset.id for asset in snapshot.assets if asset.archived_at is None}
    if any(target != _NEW and target not in active for target in request.asset_map.values()):
        raise NotFoundError()


def _cadence_seconds(facts: StreamFacts, request: ImportMappingRequest) -> int | None:
    if facts.kind is ValueKind.COUNTER:
        return None
    declared = request.interval_minutes.get(facts.stream_key)
    if declared is not None and MIN_INTERVAL_MINUTES <= declared <= MAX_INTERVAL_MINUTES:
        return declared * 60
    return None if facts.cadence is None else max(1, round(facts.cadence.total_seconds()))


def _covers_period(binding: BindingModel, facts: StreamFacts) -> bool:
    """Tell whether a half-open binding overlaps a stream's period, whose last counter point is itself included."""
    if facts.period_start is None or facts.period_end is None:
        return False
    if binding.effective_to is not None and binding.effective_to <= facts.period_start:
        return False
    if facts.kind is ValueKind.COUNTER:
        return binding.effective_from <= facts.period_end
    return binding.effective_from < facts.period_end


def _question(
    kind: ImportQuestionKind,
    message: str,
    *,
    streams: Sequence[str] = (),
    asset_name: str | None = None,
    candidates: Sequence[AssetModel] = (),
) -> ImportQuestionResponse:
    return ImportQuestionResponse(
        kind=kind,
        message=bound_text(message),
        streams=list(streams),
        asset_name=asset_name,
        candidates=[
            AssetCandidateResponse(
                id=asset.id,
                name=asset.name,
                location=asset.location,
                category=asset.category,
                scope_kind=asset.scope_kind.value,
            )
            for asset in candidates
        ],
    )


class _Resolver:
    """One file's names and streams against one site's active assets."""

    def __init__(self, request: ImportMappingRequest, snapshot: SiteSnapshot) -> None:
        """Index the snapshot.

        Args:
            request (ImportMappingRequest): The answers.
            snapshot (SiteSnapshot): The site's assets, sources and bindings.
        """
        self.request = request
        self.snapshot = snapshot
        self.active = {asset.id: asset for asset in snapshot.assets if asset.archived_at is None}
        self.same_name: dict[str, list[AssetModel]] = {}
        for asset in sorted(self.active.values(), key=lambda item: str(item.id)):
            self.same_name.setdefault(asset.name.lower(), []).append(asset)

    def target(self, name: str) -> UUID | str | None:
        """Return a name's target: the port of ``defaultMapping``, with the user's answer first.

        Args:
            name (str): The name as written.

        Returns:
            UUID | str | None: An asset ID, ``new``, or None while several assets share the name.
        """
        answer = self.request.asset_map.get(name)
        if answer is not None:
            return answer
        same = self.same_name.get(name.lower(), [])
        if len(same) > 1:
            return None
        return same[0].id if same else _NEW

    def name_questions(self, facts: StreamFacts) -> list[ImportQuestionResponse]:
        """Ask what a stream's names need: a choice among same-name assets, or a choice about another source.

        Args:
            facts (StreamFacts): The stream.

        Returns:
            list[ImportQuestionResponse]: The questions.
        """
        questions: list[ImportQuestionResponse] = []
        for name in facts.names:
            target = self.target(name)
            if target is None:
                questions.append(
                    _question(
                        ImportQuestionKind.ASSET_CHOICE,
                        f'Ada lebih dari satu perangkat bernama "{name}". '
                        "Pilih perangkat yang dimaksud atau buat baru.",
                        streams=[facts.stream_key],
                        asset_name=name,
                        candidates=self.same_name[name.lower()],
                    )
                )
            elif target != _NEW and facts.kind is not None and self._has_other_source(target, facts):
                asset = self.active[target]
                questions.append(
                    _question(
                        ImportQuestionKind.OTHER_SOURCE,
                        f"{asset.name} sudah memiliki sumber lain. Sumber ganda untuk satu beban tidak dijumlahkan; "
                        f"{_SECOND_SOURCE_NEXT_STEP}",
                        streams=[facts.stream_key],
                        asset_name=asset.name,
                    )
                )
        return questions

    def _has_other_source(self, asset_id: UUID, facts: StreamFacts) -> bool:
        own = resolve_source(asset_id, facts.stream_key, facts.kind, self.snapshot)
        return any(
            binding.asset_id == asset_id
            and (own is None or binding.source_id != own.id)
            and _covers_period(binding, facts)
            for binding in self.snapshot.bindings
        )

    def one_to_one_questions(self, streams: Sequence[StreamFacts]) -> list[ImportQuestionResponse]:
        """Ask about any stream reaching two assets, then any asset fed by two streams.

        Args:
            streams (Sequence[StreamFacts]): The file's streams.

        Returns:
            list[ImportQuestionResponse]: The questions.
        """
        questions: list[ImportQuestionResponse] = []
        by_asset: dict[UUID | str, dict[str, str]] = {}
        for facts in streams:
            names = list(facts.names)
            identities = {self._identity(name) for name in names}
            if len({name.lower() for name in names}) > 1 or len(identities) > 1:
                questions.append(
                    _question(
                        ImportQuestionKind.STREAM_ASSETS,
                        f'Sumber "{facts.stream_key}" dipakai oleh lebih dari satu perangkat: {", ".join(names)}. '
                        "Pisahkan sumbernya atau samakan nama perangkatnya.",
                        streams=[facts.stream_key],
                    )
                )
            for name in names:
                by_asset.setdefault(self._identity(name), {}).setdefault(facts.stream_key, name)
        for identity, fed_by in by_asset.items():
            if len(fed_by) > 1:
                asset = self.active.get(identity) if isinstance(identity, UUID) else None
                shown = asset.name if asset is not None else next(iter(fed_by.values()))
                questions.append(
                    _question(
                        ImportQuestionKind.ASSET_STREAMS,
                        f'Perangkat "{shown}" menerima lebih dari satu sumber dalam berkas ini. '
                        f"Sumber ganda tidak dijumlahkan; {_SECOND_SOURCE_NEXT_STEP}",
                        streams=list(fed_by),
                        asset_name=shown,
                    )
                )
        return questions

    def _identity(self, name: str) -> UUID | str:
        """Name what a target is: a stored asset's ID, or a new asset's case-folded name."""
        target = self.target(name)
        return target if isinstance(target, UUID) else name.lower()

    def stream(self, facts: StreamFacts) -> ResolvedStream:
        """Resolve one stream by its first name. A stream with several has a question open.

        Args:
            facts (StreamFacts): The stream.

        Returns:
            ResolvedStream: The stream.
        """
        target = self.target(next(iter(facts.names)))
        asset_id = target if isinstance(target, UUID) else None
        source = None
        if asset_id is not None and facts.kind is not None:
            source = resolve_source(asset_id, facts.stream_key, facts.kind, self.snapshot)
        return ResolvedStream(
            facts=facts, asset_id=asset_id, source=source, cadence_seconds=_cadence_seconds(facts, self.request)
        )


def resolve_streams(
    streams: Sequence[StreamFacts], request: ImportMappingRequest, snapshot: SiteSnapshot
) -> ResolvedMapping:
    """Resolve each stream to an asset and source. Names never decide identity where they are ambiguous.

    Args:
        streams (Sequence[StreamFacts]): The file's streams, including any whose rows are all invalid.
        request (ImportMappingRequest): The answers so far.
        snapshot (SiteSnapshot): The site's assets, sources and bindings.

    Returns:
        ResolvedMapping: The streams and the open questions.

    Raises:
        NotFoundError: When an answer names anything but an active asset of this site.
    """
    require_active_targets(request, snapshot)
    resolver = _Resolver(request, snapshot)
    questions: list[ImportQuestionResponse] = []
    if request.scope is None:
        questions.append(
            _question(ImportQuestionKind.SCOPE, "Pilih apakah beban perangkat dalam berkas ini terukur terpisah.")
        )
    for facts in streams:
        questions += resolver.name_questions(facts)
    questions += resolver.one_to_one_questions(streams)
    return ResolvedMapping(streams=[resolver.stream(facts) for facts in streams], questions=questions)
