# Plan: Conexión de la API a PostgreSQL

Alcance: `docs/contrato-api.md`, secciones Salud y Estados. Fuera de alcance:
proyectos, tareas, filtros, `due_at`, skills, hooks y CI.

Cada incremento se implementa, se confirma por separado y se detiene para
esperar aprobación antes de encadenar el siguiente.

## Qué existe ya

- `app/main.py` solo expone `GET /health` (in-memory, sin estado). No hay
  módulos de base de datos, config, ni modelos.
- `pyproject.toml`: dependencias de runtime `fastapi`, `uvicorn`; dev `httpx`,
  `pytest`, `ruff`. No hay `sqlalchemy`, `psycopg` ni `alembic` todavía.
- `compose.yaml` define un servicio `db` (Postgres 18-alpine) con variables
  `POSTGRES_USER/PASSWORD/DB/PORT`, con defaults que coinciden con
  `.env.example`. No hay volumen de seed ni migraciones.
- `tests/test_health.py` es el único test, contra `TestClient` directo, sin
  fixtures de base de datos ni `conftest.py`.
- No existe carpeta de migraciones ni `alembic.ini`.

## Incremento 1 — Scaffolding de conexión a PostgreSQL

- Agregar `sqlalchemy`, un driver de Postgres (`psycopg[binary]`) y `alembic`
  a `pyproject.toml`.
- `app/db.py`: construir la URL de conexión a partir de las variables
  `POSTGRES_*` (mismos nombres y defaults que `.env.example`/`compose.yaml`),
  y crear el engine de SQLAlchemy.
- Test nuevo (`tests/test_db.py`) que abre una conexión real y ejecuta
  `SELECT 1` — falla primero por ausencia de `app/db.py`, luego pasa.
- **Comprobación**: `docker compose up -d`, `uv sync --frozen`,
  `uv run pytest -q` (test nuevo y `test_health` en verde),
  `uv run ruff check .`.

## Incremento 2 — Alembic y migración inicial de `states` (solo esquema)

- Inicializar Alembic (`alembic.ini`, carpeta de migraciones), `env.py`
  apuntando a la URL del incremento 1.
- Primera migración: crea la tabla `states` con `id`, `code` y una columna de
  orden explícita (el contrato exige ordenar por "el campo de orden del
  catálogo", distinto de `id`). Sin datos todavía.
- Test que corre `upgrade` desde base vacía y luego `downgrade`, verificando
  que la tabla aparece y desaparece.
- **Comprobación**: `docker compose up -d`, `uv run pytest -q` (incluye el
  test de upgrade/downgrade), `uv run ruff check .`.

## Incremento 3 — Seed idempotente del catálogo de estados

- Migración que inserta los cuatro estados fijos (`PENDIENTE`, `EN_CURSO`,
  `BLOQUEADA`, `HECHA`), escrita para que aplicarla dos veces no duplique ni
  falle.
- Test que corre la migración dos veces seguidas y verifica exactamente 4
  filas con los códigos esperados.
- **Comprobación**: `docker compose up -d`, `uv run pytest -q` (test de
  doble-migración en verde), `uv run ruff check .`.

## Incremento 4 — `GET /states` conectado a PostgreSQL

- Implementar el endpoint leyendo de la tabla `states`, con el orden exacto
  del contrato (campo de orden, luego `id`) y el esquema de respuesta exacto
  (`{"id": ..., "code": ...}`, sin campos de más).
- Test de integración vía `TestClient` que aplica migraciones y verifica
  `200`, orden estable entre dos llamadas, y esquema exacto.
- **Comprobación**: `docker compose up -d`, `uv run pytest -q` (suite
  completa en verde, incluyendo `test_health` sin cambios de comportamiento),
  `uv run ruff check .`.

## Restricciones que se mantienen en todos los incrementos

- No se modifica `docs/contrato-api.md`, `docs/decisiones-ingenieria.md`,
  `CLAUDE.md`, `.gitignore` ni `.env`. No se abre `.env`.
- No se debilita ni elimina un test existente para conseguir verde.
