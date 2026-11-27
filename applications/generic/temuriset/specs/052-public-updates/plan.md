# Implementation Plan: Public updates (revamp R5)

**Spec**: [spec.md](spec.md)

## API

1. `migrations/versions/0024_invention_updates.py` and `InventionUpdateRecord` in `app/portfolio/repository/sqlalchemy/models.py`.
2. `app/portfolio/service/updates.py`: `UpdateService` (list, create, edit, publish, withdraw) and `published_updates()` for the public page. Writes lock the invention so a publish never races the page being switched off. The owner list is capped at 100 (`ponytail:` note).
3. `app/portfolio/router.py`: the five routes; `app/portfolio/model/schema.py`: `UpdateRequest`, `EditUpdateRequest`, `InventionUpdateResponse`.
4. `app/subscriptions`: `TeaserUpdate` and `TeaserResponse.latest_updates`.

## Web

1. `features/portfolio/PublicUpdatesPanel.tsx` between the public page form and the investor news switch; `app/inventions/[id]/page.tsx` loads the owner's updates.
2. `views/subscriptions/TeaserView.tsx`: "Kabar terbaru" / "Latest updates" list with `<time>` and language labels.
3. Design system: `.tr-showcase` splits into two columns only when it holds a photo.

## Tests

API: `tests/integration/portfolio/test_public_updates.py` (shown once announced once with a stable `published_at`, refused without a public page or when archived, stale and oversized corrections), isolation entries, teaser key set, migration round trip. Web: `tests/public-updates.test.tsx` (draft with idempotency key and validation, refused publish message, withdraw and correction with versions, English page labels, axe).
