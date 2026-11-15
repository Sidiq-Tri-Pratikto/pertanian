"""Which topic groups an invention matches, and the honest reason line (spec 046 FR-003).

A direct alert needs every topic group the subscriber filled in to match; the weekly digest needs at least one. The
reason states a topic match only, never fit, readiness or trend (invariant 6).
"""

import re
from dataclasses import dataclass
from typing import Any, Literal

STAGE_LABEL = {
    "IDEA": "Ide",
    "PROTOTYPE": "Prototipe",
    "PILOT": "Pilot",
    "WORKING": "Sudah berfungsi",
    "MARKET": "Sudah di pasar",
}

Level = Literal["ALERT", "DIGEST"]


@dataclass(frozen=True)
class Match:
    """How an invention matched a subscriber.

    Attributes:
        level (Level): ``ALERT`` when every filled group matched, ``DIGEST`` when some did.
        reasons (list[str]): The matched terms, in Indonesian.
    """

    level: Level
    reasons: list[str]


def _words(text: str) -> set[str]:
    return set(re.findall(r"[0-9a-zà-ÿ]+", text.lower()))


def match(topics: dict[str, Any], invention: dict[str, Any]) -> Match | None:
    """Match one subscriber's topics against one public invention.

    Args:
        topics (dict[str, Any]): ``sectors``, ``stages`` and ``keywords``.
        invention (dict[str, Any]): ``sector``, ``stage``, ``title``, ``summary`` and ``keywords``.

    Returns:
        Match | None: The level and reasons, or None when no group matched.
    """
    groups: list[str | None] = []
    sectors = {sector.lower() for sector in topics.get("sectors", [])}
    if sectors:
        sector = invention.get("sector") or ""
        groups.append(f"sektor {sector}" if sector.lower() in sectors else None)
    stages = set(topics.get("stages", []))
    if stages:
        stage = invention.get("stage")
        groups.append(f"tahap {STAGE_LABEL.get(stage, stage)}" if stage in stages else None)
    keywords = [keyword for keyword in topics.get("keywords", []) if keyword.strip()]
    if keywords:
        text = " ".join([invention.get("title", ""), invention.get("summary", ""), *invention.get("keywords", [])])
        present = _words(text)
        hits = [keyword for keyword in keywords if _words(keyword) and _words(keyword) <= present]
        groups.append("kata kunci " + ", ".join(f"“{hit}”" for hit in hits) if hits else None)
    reasons = [group for group in groups if group]
    if not reasons:
        return None
    return Match(level="ALERT" if len(reasons) == len(groups) else "DIGEST", reasons=reasons)
