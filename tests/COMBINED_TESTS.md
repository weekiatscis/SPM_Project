# Combined Tests Documentation

This document merges the key information from `tests/TESTING_CHANGES.md` and `tests/README.md` and focuses on the current test implementation and how to run the tests for the SPM Project.

## Purpose and high-level design
- The test suite combines unit and integration tests for each microservice into a single file per service under `tests/`.
- Goal: make tests easier to find, maintain, and run; improve CI feedback speed while keeping combined coverage (~80% target when unit + integration run).
- Each service has one test file:
  - `tests/test_auth_service.py`
  - `tests/test_notification_service.py`
  - `tests/test_project_service.py`
  - `tests/test_task_service.py`
  - `tests/test_user_service.py`

## File layout and structure (current code)
- Every `tests/test_<service>.py` contains:
  - Top-of-file configuration and imports (pytest, requests, os, mocks).
  - A clear "UNIT TESTS" section with classes testing business logic, helpers, and small functions using mocks where necessary.
  - An "INTEGRATION TESTS" section with classes that call live endpoints (health endpoints, CRUD endpoints) and validate end-to-end behavior.
  - Optional `if __name__ == "__main__": pytest.main([__file__, "-v"])` for running a single file.
- Tests use environment variables to point at services; defaults assume local docker-compose ports:
  - `TASK_SERVICE_URL` (default: http://localhost:8080)
  - `PROJECT_SERVICE_URL` (default: http://localhost:8082)
  - `USER_SERVICE_URL` (default: http://localhost:8081)
  - `AUTH_SERVICE_URL` (default: http://localhost:8086)
  - `NOTIFICATION_SERVICE_URL` (default: http://localhost:8084)

## How tests are run (current commands)
- Run all tests:
  - `pytest tests/ -v`
- Unit tests only (fast, no services required):
  - `pytest tests/ -v -k "not Integration"`
- Integration tests only (services must be running via docker-compose):
  - `pytest tests/ -v -k "Integration"`
- Run a single service's tests:
  - `pytest tests/test_auth_service.py -v`

## Dependencies for testing
- One requirements file for tests: `tests/requirements-test.txt`. Install with:
  - `pip install -r tests/requirements-test.txt`
- Integration tests require docker-compose and the services running as defined in the repository `docker-compose.yml`.

## CI behavior and workflow
- GitHub Actions split testing into two jobs:
  1. Unit Tests job: runs `pytest -k "not Integration"`, uploads coverage artifact (fast feedback).
  2. Integration Tests job: starts docker-compose, waits for healthchecks, runs `pytest -k "Integration"`, uploads coverage artifact.
- Coverage strategy:
  - Unit tests cover helpers and logic (small %).
  - Integration tests exercise endpoints and increase coverage.
  - Combined aim is ~80% coverage.

## Current test coverage & metrics (from docs)
- Approx targets and example outputs:
  - Unit only: ~18–30% coverage
  - Integration only: ~50–65%
  - Combined: ~80% (project target)
- Typical counts: ~5 test files, ~159 test functions total, unit: ~115, integration: ~44.

## Running locally: recommended quick checklist
1. Ensure Python test deps installed:
   - `pip install -r tests/requirements-test.txt`
2. For unit tests (fast):
   - `pytest tests/ -v -k "not Integration"`
3. For integration tests:
   - Start stack (from project root): `docker compose up --build -d`
   - Wait for services to become healthy
   - Run: `pytest tests/ -v -k "Integration"`
   - If a test fails, gather logs: `docker compose logs <service> --tail=500`
4. To get combined coverage:
   - `pytest tests/ -v --cov=src/microservices --cov-report=html`
   - `open htmlcov/index.html`

## Current implementation notes (focus on code)
- Tests are intentionally colocated per-service so each file provides a complete view of what that service expects to provide (helpers + endpoints).
- Unit tests predominantly mock external calls (database, supabase, HTTP) to keep them fast and deterministic.
- Integration tests perform real HTTP calls to service endpoints; they rely on docker-compose ports and healthchecks in `docker-compose.yml`.
- The test files include many focused unit test classes covering:
  - Validation logic (UUID, email, required fields)
  - Data mapping between DB rows and API payloads
  - Date/time parsing and duration calculations (seen in `report_service` tests)
  - Notification payloads and email template generation
  - Recurring task scheduling logic
- Integration tests include health checks plus key endpoint flows (create/update/read/delete, notifications flow).
- Tests assume certain service endpoints exist and return JSON in a specific shape (e.g., `GET /tasks` returns `{"tasks": [...]}`), so services must implement those APIs for integration tests to pass.

## Troubleshooting common failures
- If tests not discovered: ensure you run from repo root.
- If import errors: confirm Python paths and that `src/microservices` code is present and importable.
- If integration tests fail: check docker-compose status and logs, e.g.:
  - `docker compose ps`
  - `docker compose logs <service> --tail=500`
- Healthchecks in compose use wget spider endpoints — on slow machines allow more startup time.

## Recommendations and small improvements (low-risk)
- Keep unit tests fast by increasing use of mocks for external services.
- Consider test fixtures for shared data across services to reduce duplication.
- Add a small wrapper script `scripts/run_integration_tests.sh` that:
  - brings up compose
  - waits for healthchecks (poll endpoints)
  - runs `pytest -k "Integration"`
  - collects failing service logs automatically
- Continue to keep secrets out of the repository (`.env` contains sensitive keys); CI should inject them via secrets.

## One-page quick reference
- Install test deps:
  - `pip install -r tests/requirements-test.txt`
- Unit tests only:
  - `pytest tests/ -v -k "not Integration"`
- Start services for integration:
  - `docker compose up --build -d`
- Run integration tests:
  - `pytest tests/ -v -k "Integration"`
- Combined coverage:
  - `pytest tests/ -v --cov=src/microservices --cov-report=html`

---

If you want, I can further:
- Add this file to the repo (done).
- Create the helper script `scripts/run_integration_tests.sh` to automate the steps described below.
