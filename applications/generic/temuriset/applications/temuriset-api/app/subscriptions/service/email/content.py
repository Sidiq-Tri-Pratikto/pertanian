"""Single content model rendered to both plain text and HTML so both parts can never disagree (spec 060)."""

from dataclasses import dataclass, field


def truncate_words(text: str, limit: int) -> str:
    """Collapse whitespace and cut cleanly at a word boundary within ``limit`` characters."""
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    clipped = cleaned[: limit - 1]
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0]
    return clipped.rstrip(" ,;:-") + "…"


@dataclass(frozen=True)
class Card:
    """One invention or update card shown inside an investor email."""

    title: str
    url: str
    facts: list[str]
    summary: str
    reasons: list[str]
    photo_url: str | None
    photo_alt: str | None
    field_test: str | None
    primary: tuple[str, str]
    secondary: tuple[str, str] | None = None
    inventor: str | None = None


@dataclass(frozen=True)
class EmailContent:
    """Complete content of one investor email, shared by text and HTML renderers."""

    lang: str
    subject: str
    preheader: str
    lead: str
    cards: list[Card] = field(default_factory=list)
    action: tuple[str, str] | None = None
    note: str | None = None
    footer_reason: str = ""
    manage_url: str | None = None
    unsubscribe_url: str | None = None
    language_url: str | None = None
    demo: bool = False
    demo_label: str = "Demo · Data fiktif"
    reasons_heading: str = "Mengapa Anda menerima ini"
    reasons_text_template: str = "Mengapa Anda menerima ini: cocok dengan minat Anda, {reasons}."
    inventor_label: str = "Inovator"
    field_test_label: str = "Uji lapangan"
    manage_label: str = "Atur langganan"
    unsubscribe_label: str = "Berhenti berlangganan"
    language_label: str = "Ganti bahasa email: English"
    digest_cta: tuple[str, str] | None = None
    tagline: str = "TemuRiset — pertemuan inovasi dan investor"
