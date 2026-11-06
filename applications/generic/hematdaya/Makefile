API := applications/hematdaya-api
MOBILE := applications/hematdaya-mobile

.PHONY: setup
setup:
	$(MAKE) -C $(API) install
	$(MAKE) -C $(MOBILE) install

# Fast feedback: no Docker, no database.
.PHONY: test
test:
	$(MAKE) -C $(API) test-unit
	$(MAKE) -C $(MOBILE) test

# Everything a pull request must pass. Leaves Postgres running; `make stop` stops it.
.PHONY: check
check:
	$(MAKE) -C $(API) run-dependencies
	$(MAKE) -C $(API) check
	$(MAKE) -C $(MOBILE) check
	python3 docs/roadmap/check_traceability.py

.PHONY: stop
stop:
	$(MAKE) -C $(API) stop-dependencies
