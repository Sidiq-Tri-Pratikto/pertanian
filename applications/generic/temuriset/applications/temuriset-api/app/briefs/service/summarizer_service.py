"""The provider-neutral extractive summary contract. The default adapter is off."""

import asyncio
import json
from dataclasses import dataclass
from typing import Protocol

from httpx import AsyncClient, ConnectError, HTTPError, TimeoutException
from pydantic import SecretStr

from app.briefs.model.schema import BriefSentence, SummaryProvenance
from app.core.errors import codes
from app.core.errors.base import AppError

SUMMARY_ATTEMPT_TIMEOUT_SECONDS = 3.0
_MAX_RELAY_REQUEST_BYTES = 64 * 1024
_MAX_RELAY_RESPONSE_BYTES = 16 * 1024


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


@dataclass(frozen=True, slots=True)
class LocalRelaySummarizer:
    """Send authorized candidate data to a development-only loopback contract double.

    Attributes:
        endpoint (SecretStr): Startup-validated loopback URL.
        provenance (SummaryProvenance): Model and prompt provenance from local configuration.
    """

    endpoint: SecretStr
    provenance: SummaryProvenance
    name = "local-relay"

    async def summarize(self, candidates: tuple[SummaryCandidate, ...]) -> object:
        """Read one bounded JSON selection from the relay.

        Args:
            candidates (tuple[SummaryCandidate, ...]): Authorized text and per-attempt IDs.

        Returns:
            object: Untrusted decoded selection for the server to validate.
        """
        payload = {"candidates": [{"id": candidate.id, "text": candidate.text} for candidate in candidates]}
        content = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        if len(content) > _MAX_RELAY_REQUEST_BYTES:
            raise SummaryRefusedError()

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "identity",
        }
        body = bytearray()
        try:
            async with (
                AsyncClient(timeout=SUMMARY_ATTEMPT_TIMEOUT_SECONDS, trust_env=False, follow_redirects=False) as client,
                client.stream("POST", self.endpoint.get_secret_value(), headers=headers, content=content) as response,
            ):
                response.raise_for_status()
                media_type = response.headers.get("content-type", "").partition(";")[0].strip().lower()
                if (
                    media_type != "application/json"
                    or response.headers.get("content-encoding", "identity") != "identity"
                ):
                    raise SummaryRefusedError()
                async for chunk in response.aiter_bytes():
                    if len(body) + len(chunk) > _MAX_RELAY_RESPONSE_BYTES:
                        raise SummaryRefusedError()
                    body.extend(chunk)
        except HTTPError as error:
            raise _relay_failure(error) from error

        try:
            return json.loads(body.decode(), object_pairs_hook=_unique_json_object)
        except (UnicodeError, ValueError, RecursionError) as error:
            raise SummaryRefusedError() from error


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value = dict(pairs)
    if len(value) != len(pairs):
        raise SummaryRefusedError()
    return value


def _relay_failure(error: HTTPError) -> TimeoutError | ConnectionError | SummaryUnavailableError:
    # HTTP errors can include relay-controlled text. Keep the cause without copying it into diagnostics.
    if isinstance(error, TimeoutException):
        return TimeoutError()
    if isinstance(error, ConnectError):
        return ConnectionError()
    return SummaryUnavailableError()


async def request_selection(summarizer: SummarizerPort, candidates: tuple[SummaryCandidate, ...]) -> object:
    """Get one selection under a finite timeout.

    Timeout and connection errors are the port's transient signals. Other adapter exceptions carry
    untrusted content and are chained without copying their text into diagnostics.
    """
    try:
        async with asyncio.timeout(SUMMARY_ATTEMPT_TIMEOUT_SECONDS):
            return await summarizer.summarize(candidates)
    except (TimeoutError, ConnectionError, SummaryRefusedError, SummaryUnavailableError):
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
