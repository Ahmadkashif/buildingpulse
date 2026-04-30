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
	cd $(BACKEND) && $(PY) -m mutmut run --paths-to-mutate app/domain

e2e:
	@echo "e2e: Playwright suite not yet wired (issue #51 et al.) — placeholder target."
	@cd frontend 2>/dev/null && [ -f package.json ] && npm run e2e || echo "frontend e2e not configured yet"

schema:
	@echo "schema: OpenAPI + frontend codegen drift check not yet wired — placeholder target."

clean:
	rm -f $(BACKEND)/coverage.xml $(BACKEND)/.coverage
	rm -rf $(BACKEND)/.pytest_cache $(BACKEND)/.mypy_cache $(BACKEND)/.ruff_cache
