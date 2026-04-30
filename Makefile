# BuildingPulse — local CI mirror.
#
# Targets mirror the merge gates in prd.md ("Locked CI/quality decisions").
# CI runs the same commands; if `make check && make test` is green locally,
# the build is green.

.PHONY: help install check test e2e schema mutate clean

PY ?= python3
BACKEND := backend

help:
	@echo "make check   — ruff + mypy --strict + lint-imports"
	@echo "make test    — pytest with branch coverage + per-layer rubric"
	@echo "make e2e     — Playwright happy-path E2E (frontend)"
	@echo "make schema  — OpenAPI schema drift + frontend type codegen drift"
	@echo "make mutate  — mutmut run --paths-to-mutate app/domain"
	@echo "make install — pip install -e backend[dev]"

install:
	cd $(BACKEND) && $(PY) -m pip install -e ".[dev]"

check:
	cd $(BACKEND) && $(PY) -m ruff check app tests
	cd $(BACKEND) && $(PY) -m ruff format --check app tests
	cd $(BACKEND) && $(PY) -m mypy app
	cd $(BACKEND) && lint-imports --config .importlinter

test:
	cd $(BACKEND) && $(PY) -m pytest \
		--cov=app --cov-branch \
		--cov-report=term-missing \
		--cov-report=xml:coverage.xml
	cd $(BACKEND) && $(PY) scripts/cov_rubric.py

mutate:
	# paths_to_mutate lives under [tool.mutmut] in backend/pyproject.toml.
	cd $(BACKEND) && $(PY) -m mutmut run

e2e:
	cd frontend && npm run e2e

schema:
	$(PY) $(BACKEND)/scripts/dump_openapi.py --out $(BACKEND)/openapi.json
	cd frontend && npm run codegen --silent
	@if ! git diff --exit-code -- $(BACKEND)/openapi.json frontend/src/types/api.ts; then \
		echo "ERROR: OpenAPI schema or generated frontend types drifted. Commit the regenerated files."; \
		exit 1; \
	fi
	@echo "schema: backend/openapi.json and frontend/src/types/api.ts are in sync."

clean:
	rm -f $(BACKEND)/coverage.xml $(BACKEND)/.coverage
	rm -rf $(BACKEND)/.pytest_cache $(BACKEND)/.mypy_cache $(BACKEND)/.ruff_cache
