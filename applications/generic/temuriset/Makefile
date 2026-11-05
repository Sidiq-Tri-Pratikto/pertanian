API := applications/temuriset-api
WEB := applications/temuriset-web

.DEFAULT_GOAL := help

.PHONY: help
help: ## List every command
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "  make %-16s %s\n", $$1, $$2}'

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

.PHONY: stop
stop: ## Stop the local Postgres
	$(MAKE) -C $(API) stop-dependencies

.PHONY: reset-db
reset-db: ## Delete the local database volume and start empty
	$(MAKE) -C $(API) reset-dependencies
