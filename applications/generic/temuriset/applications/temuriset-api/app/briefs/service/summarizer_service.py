"""The provider-neutral extractive summary contract. The default adapter is off."""

import asyncio
from dataclasses import dataclass
from typing import Protocol

from app.briefs.model.schema import BriefSentence, SummaryProvenance
from app.core.errors import codes
from app.core.errors.base import AppError

SUMMARY_ATTEMPT_TIMEOUT_SECONDS = 3.0


class SummaryRefusedError(AppError):
    """The selection cannot safely be used."""

    code = codes.APP_SUMMARY_REFUSED


class SummaryUnavailableError(AppError):
    """The configured adapter could not supply a selection."""

    code = codes.APP_SUMMARY_UNAVAILABLE


@dataclass(frozen=True, slots=True)
class SummaryCandidate:
    """The opaque identifier and exact sentence text supplied to the adapter."""

    id: str
    text: str


class SummarizerPort(Protocol):
    """Select from the supplied text. Adapter configuration owns provenance."""

    @property
    def name(self) -> str:
        """The configured adapter name."""
        ...

    @property
    def provenance(self) -> SummaryProvenance | None:
        """The trusted model and prompt versions, or None when off."""
        ...

    async def summarize(self, candidates: tuple[SummaryCandidate, ...]) -> object:
        """Return a decoded selection whose entire structure is validated by the caller."""
        ...


class OffSummarizer:
    """The default keeps the template brief."""

    name = "off"
    provenance = None

    async def summarize(self, candidates: tuple[SummaryCandidate, ...]) -> None:  # noqa: ARG002 - port signature
        """Return no selection."""
        return None


async def request_selection(summarizer: SummarizerPort, candidates: tuple[SummaryCandidate, ...]) -> object:
    """Get one selection under a finite timeout.

    Timeout and connection errors are the port's transient signals. Other adapter exceptions carry
    untrusted content and are chained without copying their text into diagnostics.
    """
    try:
        async with asyncio.timeout(SUMMARY_ATTEMPT_TIMEOUT_SECONDS):
            return await summarizer.summarize(candidates)
    except (TimeoutError, ConnectionError):
        raise
    except Exception as error:  # noqa: BLE001 - isolate unexpected adapter failures from the editable template
        raise SummaryUnavailableError() from error


def select_sentences(output: object, originals: dict[str, BriefSentence]) -> list[BriefSentence]:
    """Resolve a nonempty proper subset of unique IDs to the original sentences in template order.

    Args:
        output (object): Untrusted adapter response.
        originals (dict[str, BriefSentence]): Authorized originals keyed by per-attempt ID.

    Returns:
        list[BriefSentence]: Exact originals with their references.

    Raises:
        SummaryRefusedError: The response violates the selection contract.
    """
    if not isinstance(output, dict) or output.keys() != {"sentence_ids"}:
        raise SummaryRefusedError()
    identifiers = output["sentence_ids"]
    if not isinstance(identifiers, list) or not 0 < len(identifiers) < len(originals):
        raise SummaryRefusedError()
    if any(not isinstance(identifier, str) or identifier not in originals for identifier in identifiers):
        raise SummaryRefusedError()
    selected = set(identifiers)
    if len(selected) != len(identifiers):
        raise SummaryRefusedError()
    return [sentence for identifier, sentence in originals.items() if identifier in selected]
