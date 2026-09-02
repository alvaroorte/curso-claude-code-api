# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

TaskFlow API — a FastAPI project managed with `uv` on Python 3.12, built incrementally across a course. The current implementation exposes only `GET /health`; the full contract in `docs/contrato-api.md` (projects, tasks, states, due dates) is implemented in later sessions. Do not assume unimplemented endpoints exist — check `app/main.py` for what's actually built.

## Commands

```bash
uv sync --frozen                       # install exact locked dependencies
uv run pytest -q                       # run all tests
uv run pytest -q tests/test_health.py  # run a single test file
uv run pytest -q -k test_health_returns_ok  # run a single test by name
uv run ruff check .                    # lint
docker compose up -d                   # start Postgres (infra)
docker compose down                    # stop Postgres
uv run uvicorn app.main:app --reload   # run the API locally
```

Copy `.env.example` to `.env` to override Postgres defaults; `compose.yaml` works with its built-in defaults even without a `.env` file.

## Contract-driven development

`docs/contrato-api.md` is the binding spec for this project — it fixes *observable* behavior (status codes, response shapes, ordering, error format) while leaving internal structure open. Treat it as authoritative over any inference from code:

- Response schemas are exact — a response must have neither more nor fewer fields than documented (e.g. optional fields absent are serialized as `null`, never omitted).
- List endpoints must return a stable order between identical calls (see the ordering table in the contract), not just "some" order.
- Errors follow `{"detail": "<message>"}`.
- `due_at` is always serialized in UTC with a trailing `Z` (no `+00:00` offset, no microseconds); a `due_at` submitted without a timezone is rejected with `422` rather than assumed.
- Task `title` normalization strips edge whitespace, then rejects (`422`) any value with no visible character left — checked by Unicode category (`Cc`, `Cf`, `Zl`, `Zp`, `Zs`), not just `strip()`, since invisible characters like `U+200B` survive a plain strip.
- The states catalog (`PENDIENTE`, `EN_CURSO`, `BLOQUEADA`, `HECHA`) has no create/delete endpoints — it's seeded via a database migration (run on every `upgrade`, not a Docker init script, so it reaches every environment including pre-existing volumes) and that seed must be idempotent — see `docs/glosario.md`.
- Deleting a project with tasks returns `409`, never an implicit cascade delete.
- A reference to a nonexistent project or state is never implicitly created.

When implementing a new part of the contract, check `docs/contrato-api.md`'s "Matriz Mínima de Tests" section for the minimum test cases expected, and don't weaken those invariants even when adding extra test cases.
