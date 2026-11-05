PORT ?= 3020
OPENAPI ?= ../../contracts/openapi.json
DESIGN_SYSTEM ?= ../../../../../docs/generic/temuriset/design-system
# Pinned here, not in package.json, so the generator never becomes a runtime dependency.
OPENAPI_TYPESCRIPT ?= openapi-typescript@7.13.0

.PHONY: install
install:
	npm ci

.env:
	cp .env.example .env

.PHONY: run
run: .env
	set -a && . ./.env && set +a && npx next dev --port $(PORT)

.PHONY: build
build: .env
	set -a && . ./.env && set +a && npx next build

.PHONY: start
start: .env
	set -a && . ./.env && set +a && npx next start --port $(PORT)

.PHONY: lint
lint:
	npx eslint . --max-warnings=0

.PHONY: typecheck
typecheck:
	npx tsc --noEmit

.PHONY: test
test:
	npx vitest run

.PHONY: test-coverage
test-coverage:
	npx vitest run --coverage

.PHONY: check
check: lint typecheck test-coverage

# Copies the design system stylesheets verbatim. CI fails when the copy drifts from the source.
.PHONY: design
design:
	cp $(DESIGN_SYSTEM)/workbench/tokens.css src/design/tokens.css
	cp $(DESIGN_SYSTEM)/project/components/bundle.css src/design/bundle.css

.PHONY: generate-api
generate-api:
	npx --yes $(OPENAPI_TYPESCRIPT) $(OPENAPI) --default-non-nullable=false --output src/api/schema.generated.ts
