PORT ?= 8081
OPENAPI ?= ../../contracts/openapi.json
# Pinned here, not in package.json: it peers on TypeScript 5 while Expo SDK 58 needs TypeScript 6.
OPENAPI_TYPESCRIPT ?= openapi-typescript@7.13.0

.PHONY: install
install:
	npm ci

.env:
	cp .env.example .env

.PHONY: run
run: .env
	npx expo start --port $(PORT)

.PHONY: web
web: .env
	npx expo start --web --port $(PORT)

.PHONY: lint
lint:
	npx expo lint

.PHONY: typecheck
typecheck:
	npx tsc --noEmit

.PHONY: test
test:
	npx jest

.PHONY: test-coverage
test-coverage:
	npx jest --coverage

.PHONY: check
check: lint typecheck test-coverage

.PHONY: doctor
doctor:
	npx expo-doctor

.PHONY: export
export:
	npx expo export --platform android --platform ios --platform web

.PHONY: tokens
tokens:
	node scripts/generate-tokens.mjs

.PHONY: generate-api
generate-api:
	npx --yes $(OPENAPI_TYPESCRIPT) $(OPENAPI) --default-non-nullable=false --output src/api/schema.generated.ts
