# Plan: Proyectos conectados a PostgreSQL

**Alcance**: `docs/contrato-api.md`, sección Proyectos completa — `POST
/projects`, `GET /projects`, `GET /projects/{id}`, `PATCH /projects/{id}`,
`DELETE /projects/{id}` — incluyendo el esquema de respuesta exacto
(`{"id", "name", "description"}`) y el orden determinista de `GET /projects`
(`id` ascendente).

**Fuera de alcance** (declarado por nombre):

- Todo lo relacionado con Tareas: no se crea tabla `tasks`, no se
  implementan sus endpoints, y `DELETE /projects/{id}` **no** comprueba
  tareas asociadas — en este incremento responde `204` siempre que el
  proyecto exista, sin la rama `409` que el contrato describe para "si
  tiene tareas". Esa rama queda pendiente para el incremento que planifique
  Tareas.
- `due_at`, filtros de tareas y cualquier otro contenido de la sección
  Tareas v1/v2.
- El catálogo de Estados y sus migraciones existentes (`states`) — no se
  tocan.
- `docs/contrato-api.md`, `docs/decisiones-ingenieria.md`, `CLAUDE.md`,
  `.gitignore`, `.env` — no se modifican ni se abren.
- Skills, hooks, CI.

## Qué existe ya

- `app/main.py` expone `GET /health` y `GET /states` (leído directamente de
  la tabla `states` vía SQL crudo con `engine.connect()`); no hay módulo de
  modelos ni router para proyectos.
- `app/db.py` ya define `engine` con la URL construida desde variables
  `POSTGRES_*`; no requiere cambios.
- `alembic/versions/` tiene dos migraciones encadenadas: `65c1e1fe2aac`
  (crea `states`) → `f84889a78c54` (seed de `states`, head actual). No
  existe ninguna migración de `projects`.
- `pyproject.toml` ya incluye `fastapi`, `sqlalchemy`, `psycopg[binary]`,
  `alembic` como dependencias de runtime, y `httpx`, `pytest`, `ruff` como
  dev. No se necesita agregar ninguna dependencia nueva para Proyectos.
- `tests/` sigue el patrón: cada archivo de test que ejercita persistencia
  llama `command.downgrade(config, "base")` y `command.upgrade(config,
  "head")` al inicio (y limpia con `downgrade("base")` al final), usando
  `TestClient` contra `app.main.app` para los tests de endpoint. No hay
  `conftest.py` ni fixtures compartidas.
- No existe archivo de plan previo sobre Proyectos; `docs/plan-persistencia.md`
  cubre solo Salud y Estados y declaró explícitamente Proyectos y Tareas
  fuera de su alcance.

## Decisiones ya resueltas (no quedan aplazadas)

- **Sin comprobación de tareas en `DELETE`**: confirmado por el usuario —
  todo lo de Tareas queda fuera de alcance, así que este incremento no crea
  ni consulta ninguna tabla `tasks`.
- **Sin validación de contenido en `name`** más allá de que sea un campo
  requerido: la normalización de texto (`strip`, rechazo de invisibles
  Unicode) que exige el contrato está explícitamente acotada a "`title` de
  tarea" (`docs/contrato-api.md`, sección "Normalización de texto"), no a
  `name` de proyecto. No se inventa una regla que el contrato no pide.
- **`description` ausente se guarda y devuelve como `null`**: por la regla
  general "un campo opcional ausente se devuelve como `null`, no se omite"
  y por el ejemplo de esquema del contrato.
- **`id` autogenerado por la base**: mismo patrón que la tabla `states`
  (`sa.Integer()` como `primary_key`, que Alembic/SQLAlchemy traduce a
  columna autoincremental en PostgreSQL).
- **`PATCH` distingue "campo no enviado" de "campo enviado como `null`"**:
  usando `exclude_unset` de Pydantic, para que enviar `{"description":
  null}` borre la descripción, mientras que omitir `description` del
  cuerpo no la toque. Es una técnica estándar, no una ambigüedad del
  contrato sobre qué debe pasar.

## Incremento 1 — Migración de la tabla `projects` (solo esquema)

- Nueva migración de Alembic encadenada sobre el head actual
  (`f84889a78c54`): crea `projects` con `id` (entero, PK), `name` (texto,
  `nullable=False`) y `description` (texto, `nullable=True`). Sin filas
  todavía.
- Test nuevo `tests/test_projects_migration.py`, con la misma estructura
  que `tests/test_migrations.py`: corre `upgrade` desde base vacía y
  verifica que `projects` aparece en `inspect(connection).get_table_names()`;
  corre `downgrade` y verifica que desaparece.
- **Comprobación**: `docker compose up -d`, `uv run pytest -q` (test nuevo
  en verde, resto de la suite sin cambios), `uv run ruff check .`.

## Incremento 2 — `POST /projects`

- Router/endpoint que valida el cuerpo (`name` requerido, `description`
  opcional), inserta en `projects` y responde `201` con el recurso creado y
  el esquema exacto (`id`, `name`, `description`).
- Test nuevo en `tests/test_projects.py`: crea un proyecto con y sin
  `description`, verifica `201`, esquema exacto (ni un campo de más) y que
  `description` ausente vuelve como `null`.
- **Comprobación**: `docker compose up -d`, `uv run pytest -q`,
  `uv run ruff check .`.

## Incremento 3 — `GET /projects`

- Endpoint que lista todos los proyectos ordenados por `id` ascendente
  (orden fijado por el contrato), devolviendo una lista JSON en la raíz.
- Test que crea varios proyectos vía `POST` y verifica que `GET /projects`
  los devuelve en orden de `id`, con esquema exacto, y que dos llamadas
  idénticas devuelven el mismo orden.
- **Comprobación**: `docker compose up -d`, `uv run pytest -q`,
  `uv run ruff check .`.

## Incremento 4 — `GET /projects/{id}`

- Endpoint que devuelve `200` con el proyecto si existe, `404` con
  `{"detail": "..."}` si no.
- Test que verifica ambos casos (id existente tras `POST`, id inexistente).
- **Comprobación**: `docker compose up -d`, `uv run pytest -q`,
  `uv run ruff check .`.

## Incremento 5 — `PATCH /projects/{id}`

- Endpoint de actualización parcial: acepta `name` y/o `description`; solo
  toca los campos presentes en el cuerpo (`exclude_unset`), permitiendo
  poner `description` en `null` explícitamente. `404` si el proyecto no
  existe.
- Test que verifica: actualizar solo `name` deja `description` intacta;
  actualizar `description` a `null` la borra; `PATCH` sobre id inexistente
  devuelve `404`.
- **Comprobación**: `docker compose up -d`, `uv run pytest -q`,
  `uv run ruff check .`.

## Incremento 6 — `DELETE /projects/{id}`

- Endpoint que borra el proyecto y responde `204` sin cuerpo si existía,
  `404` si no. **No** comprueba tareas asociadas (ver "Fuera de alcance"):
  la rama `409` del contrato no se implementa en este incremento.
- Test que verifica `204` al borrar un proyecto existente (y que un `GET`
  posterior a ese id da `404`), y `404` al borrar un id inexistente.
- **Comprobación**: `docker compose up -d`, `uv run pytest -q` (suite
  completa en verde), `uv run ruff check .`.

## Restricciones que se mantienen en todos los incrementos

- No se modifica `docs/contrato-api.md`, `docs/decisiones-ingenieria.md`,
  `CLAUDE.md`, `.gitignore` ni `.env`. No se abre `.env`.
- No se debilita ni elimina un test existente para conseguir verde.
- No se toca la tabla `states` ni sus migraciones.
- No se crea ninguna tabla, endpoint ni lógica relacionada con Tareas.
