# Implementation Plan: Public invention page (revamp R4)

**Spec**: [spec.md](spec.md)

## API

1. `migrations/versions/0023_public_invention_page.py` and the `InventionRecord` columns.
2. `app/documents/service/public_image.py`: `clean_image()` for JPEG (drops APP1/APP12/APP13/COM, reads SOF size and EXIF orientation), PNG (drops eXIf/tEXt/iTXt/zTXt/tIME) and WebP (drops EXIF/XMP, clears the VP8X flags).
3. `app/documents/service/service.py`: `owned_public_image()` validates the owner's chosen version; `public_image()` reads and cleans it per request (`ponytail:` note on the cost).
4. `app/portfolio`: `PublicPageRequest`/`PublicPageResponse`, `set_public_page()`, `PUT /{id}/public-page`; the invention view echoes the settings.
5. `app/subscriptions`: `_public(gate="digest"|"page")`, the extended `TeaserResponse`, `teaser_photo()` and the photo route with safe headers.

## Web

1. `features/portfolio/PublicPageForm.tsx` on invention detail, next to the investor-news switch; `app/inventions/[id]/page.tsx` loads the owner's documents for the photo choice.
2. `views/subscriptions/TeaserView.tsx`: `.tr-showcase` with the summary, field test and a sized, rotated photo.
3. `app/temuan/[id]/page.tsx`: `generateMetadata` and `notFound()`; `app/temuan/[id]/not-found.tsx`.
4. Design system: `.tr-showcase`, `.tr-showcase__media`, `img.is-turned`.

## Tests

API: `tests/unit/documents/test_public_image.py` (metadata fixture per format), `tests/integration/portfolio/test_public_page.py` (clean photo with alerts off, off/archived 404, validation codes), isolation entries, migration round trip. Web: `tests/public-page.test.tsx`; `e2e/routes.ts` expects 404 for unknown `/temuan/{id}` and `/en/inventions/{id}`.
