API := applications/temuriset-api
WEB := applications/temuriset-web
E2E_API_PORT ?= 8029
# CI provides Postgres as a service, so it clears this.
API_DEPENDENCIES ?= run-dependencies

.DEFAULT_GOAL := help

.PHONY: help
help: ## List every command
	@grep -E '^[a-z0-9-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "  make %-16s %s\n", $$1, $$2}'

.PHONY: setup
setup: ## Install API and web dependencies
	$(MAKE) -C $(API) install
	$(MAKE) -C $(WEB) install

.PHONY: dev
dev: ## Run Postgres, API and web together; Ctrl+C stops all
	./local-start.sh

.PHONY: test
test: ## Fast tests, no Docker: API unit tests and web tests
	$(MAKE) -C $(API) test-unit
	$(MAKE) -C $(WEB) test

.PHONY: test-api
test-api: ## All API tests, including Postgres integration tests
	$(MAKE) -C $(API) run-dependencies
	$(MAKE) -C $(API) test

.PHONY: test-web
test-web: ## Web unit, page and accessibility tests
	$(MAKE) -C $(WEB) test

# Everything a pull request must pass. Leaves Postgres running; `make stop` stops it.
.PHONY: check
check: ## Everything a pull request must pass (needs Docker)
	$(MAKE) -C $(API) run-dependencies
	$(MAKE) -C $(API) check
	$(MAKE) -C $(WEB) check
	python3 docs/roadmap/check_traceability.py

# Starts Postgres, the API and the worker, runs the web browser checks against a production build, then stops them.
.PHONY: e2e
e2e: ## Browser checks in Chromium against a production build (needs Docker)
	$(if $(API_DEPENDENCIES),$(MAKE) -C $(API) $(API_DEPENDENCIES))
	$(MAKE) -C $(API) migrate
	@(cd $(API) && WEB_ORIGIN=http://localhost:3029 CODE_REQUESTS_PER_ADDRESS_PER_HOUR=1000 exec .venv/bin/python -m uvicorn app.main:app --port $(E2E_API_PORT) > /dev/null 2>&1) & api=$$!; \
	(cd $(API) && exec .venv/bin/python -m app.worker > /dev/null 2>&1) & worker=$$!; \
	trap 'kill $$api $$worker' EXIT; \
	for i in $$(seq 1 60); do curl -sf http://localhost:$(E2E_API_PORT)/health/ready > /dev/null && break; sleep 0.5; done; \
	E2E_API_URL=http://localhost:$(E2E_API_PORT) $(MAKE) -C $(WEB) e2e

.PHONY: stop
stop: ## Stop the local Postgres
	$(MAKE) -C $(API) stop-dependencies

.PHONY: reset-db
reset-db: ## Delete the local database volume and start empty
	$(MAKE) -C $(API) reset-dependencies
