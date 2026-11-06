"""The summarizer port. ``off`` is the default; real adapters arrive in 044. Any output is checked against the
supplied sentences, and a claim that cannot be traced to them is refused (AC35, AC68)."""

import re
from typing import Any, Protocol

_NUMBER = re.compile(r"\d[\d.,]*")
_WORD = re.compile(r"[^\W\d_]{4,}", re.UNICODE)


class SummarizerPort(Protocol):
    """Turns supplied sentences into a shorter brief, or returns None when it has nothing."""

    name: str

    async def summarize(self, sentences: list[dict[str, Any]]) -> str | None:
        """Summarize.

        Args:
            sentences (list[dict[str, Any]]): The template's sentences with their references.

        Returns:
            str | None: The summary, or None.
        """
        ...


class OffSummarizer:
    """The default: no summary, so the template brief is used."""

    name = "off"

    async def summarize(self, sentences: list[dict[str, Any]]) -> str | None:  # noqa: ARG002 - the port's signature
        """Return nothing.

        Args:
            sentences (list[dict[str, Any]]): Ignored.

        Returns:
            str | None: None.
        """
        return None


def traceable(summary: str, sentences: list[dict[str, Any]]) -> bool:
    """Whether every sentence of a summary rests on the supplied text: each number appears there, and most words do.

    Args:
        summary (str): The output to check.
        sentences (list[dict[str, Any]]): The supplied sentences.

    Returns:
        bool: True only when nothing in the summary is new.
    """
    supplied = " ".join(sentence["text"] for sentence in sentences).casefold()
    known_words = set(_WORD.findall(supplied))
    known_numbers = {number.rstrip(".,") for number in _NUMBER.findall(supplied)}
    for line in filter(None, (part.strip() for part in re.split(r"[.\n]+(?=\s|$)", summary))):
        numbers = {number.rstrip(".,") for number in _NUMBER.findall(line)}
        if not numbers <= known_numbers:
            return False
        words = set(_WORD.findall(line.casefold()))
        if words and len(words - known_words) * 2 > len(words):
            return False
    return True
