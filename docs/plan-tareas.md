# Plan: Tareas (v1 y v2 completas)

**Alcance**: `docs/contrato-api.md`, secciones "Tareas v1" y "Tareas v2:
Fechas Límite" completas — `POST /tasks`, `GET /tasks` (con filtros
`project_id`, `state_id` y `overdue=true`, solos o combinados),
`GET /tasks/{id}`, `PATCH /tasks/{id}`, `DELETE /tasks/{id}` — incluyendo la
normalización de `title`, la validación de `project_id`/`state_id`
referenciados, `due_at` (opcional, con zona horaria, normalizado y
serializado a UTC con `Z`) y el esquema de respuesta exacto de Tarea.
También incluye, por decisión explícita al planificar, reactivar la
comprobación pendiente en `DELETE /projects/{id}` (`409` si el proyecto
tiene tareas) que `docs/plan-proyectos.md` dejó señalada para este momento.

**Fuera de alcance** (declarado por nombre):

- Recordatorios, scheduler, zona horaria preferida del usuario y cambio
  automático de estado — el contrato los excluye explícitamente en la
  sección Tareas v2.
- Cualquier otro cambio a `POST/GET/PATCH /projects` más allá de la
  reactivación puntual de la comprobación de tareas en `DELETE
  /projects/{id}`.
- El catálogo de Estados y sus migraciones existentes — no se tocan.
- `docs/contrato-api.md`, `docs/decisiones-ingenieria.md`, `CLAUDE.md`,
  `.gitignore`, `.env` — no se modifican ni se abren.
- Skills, hooks, CI.

## Qué existe ya

- `app/main.py` expone `GET /health`, `GET /states` y el CRUD completo de
  `POST/GET/GET-by-id/PATCH/DELETE /projects` (SQL crudo vía `text()` sobre
  `engine.connect()`/`engine.begin()`, sin ORM ni router separado). No hay
  ningún código de Tareas.
- `alembic/versions/` tiene tres migraciones encadenadas: `65c1e1fe2aac`
  (`states`) → `f84889a78c54` (seed de `states`) → `bf89f20664d1`
  (`projects`, head actual). No existe ninguna migración de `tasks`.
- `pyproject.toml` no tiene dependencias nuevas que agregar: Pydantic v2
  (vía FastAPI) ya parsea `datetime` ISO 8601 con offset de forma nativa,
  sin librería adicional.
- `tests/` sigue el patrón ya usado en `test_projects.py` y
  `test_projects_migration.py`: `command.downgrade(config, "base")` →
  `command.upgrade(config, "head")` al inicio de cada test, `TestClient`
  contra `app.main.app`, limpieza con `downgrade("base")` al final.
- La rama actual (`feature/tasks`) arrancó desde `main` con la base ya
  migrada a `bf89f20664d1`.

## Decisiones ya resueltas (no quedan aplazadas)

- **`project_id`/`state_id` inexistentes → `404`**: confirmado por el
  usuario al planificar, entre las dos lecturas posibles de la sección
  Convenciones del contrato.
- **`DELETE /projects/{id}` reactiva su comprobación de tareas en este
  plan**: confirmado por el usuario, cerrando la deuda señalada en
  `docs/plan-proyectos.md`.
- **La tabla `tasks` incluye `due_at` desde su única migración**, sin pasar
  por un estado intermedio "v1 sin `due_at`": el ticket pide "v1 y v2
  completas" como una sola entrega, no una v1 ya liberada que haya que
  preservar. Pasar por un esquema sin `due_at` obligaría a escribir un test
  de "esquema exacto sin `due_at`" que quedaría invalidado un incremento
  después al agregar la columna — complejidad sin ningún cliente v1 real
  que la necesite. El esquema final que se prueba en todos los incrementos
  de Tareas es siempre el de v2 (`id`, `title`, `description`, `project_id`,
  `state_id`, `due_at`), con `due_at` presente y en `null` cuando se omite
  (regla general del contrato: "un campo opcional ausente se devuelve como
  `null`, no se omite").
- **Orden de validación en `POST`/`PATCH`**: primero se normaliza y valida
  `title` (`422` si no queda ningún carácter visible tras recortar
  espacios), después se valida que `project_id` exista (`404`), después que
  `state_id` exista (`404`). El contrato no fija un orden, pero como los
  tres validan cosas distintas con códigos distintos, cualquier orden
  produce el mismo resultado observable para un cliente que envía un solo
  campo inválido a la vez (los casos de la Matriz Mínima de Tests).
- **`due_at` sin zona horaria → `422`**: cita literal del contrato ("Una
  fecha sin zona se rechaza con `422`: es ambigua"). Se normaliza a UTC
  antes de guardar y se serializa siempre como `...Z`, sin microsegundos ni
  desplazamiento, también por cita literal ("Esquemas de Respuesta").
- **Filtrar por un `project_id`/`state_id` que no existe en `GET /tasks`
  devuelve lista vacía, no error**: a diferencia de `POST`/`PATCH`, donde
  esos campos identifican una referencia que se va a guardar, en `GET` son
  criterios de filtro sobre una colección; el contrato no exige validarlos
  ahí, y la Matriz Mínima solo pide probar "Filtros solos y combinados", no
  un caso de error para un filtro con id inexistente.
- **`overdue=true` es el único valor que activa el filtro** (cualquier otro
  valor, incluida su ausencia, no filtra por vencimiento): cita literal del
  contrato, que solo define comportamiento para `GET /tasks?overdue=true`.
- **No hay borrado en cascada a nivel de base de datos**: las claves foráneas
  de `tasks` hacia `projects` y `states` no declaran `ON DELETE CASCADE`
  (el comportamiento por omisión de PostgreSQL ya impide el borrado si hay
  referencias), consistente con "no hay borrado en cascada implícito" del
  contrato.
- **Tipos de columna sin cota inventada**: `title` y `description` como
  texto sin límite de longitud, mismo criterio ya aplicado a `name`/
  `description` de Proyectos (el contrato no impone una cota).
- **Corte de implementación v1/v2** (confirmado por el usuario después de
  aprobar este plan): "v1" para efectos de implementación son los
  incrementos 1 a 6 tal como están escritos abajo —incluida la columna y
  validación de `due_at`, ya presentes desde el incremento 1 por la
  decisión anterior—; el incremento 7 (filtro `overdue=true`) es el único
  exclusivamente v2, y el incremento 8 (Proyectos) no pertenece a Tareas.

## Incremento 1 — Migración de la tabla `tasks` (solo esquema, v1+v2)

- Nueva migración de Alembic encadenada sobre el head actual
  (`bf89f20664d1`): crea `tasks` con `id` (entero, PK), `title` (texto, not
  null), `description` (texto, nullable), `project_id` (entero, FK a
  `projects.id`, not null), `state_id` (entero, FK a `states.id`, not
  null), `due_at` (timestamp con zona horaria, nullable). Sin filas
  todavía.
- Test nuevo `tests/test_tasks_migration.py`, mismo patrón que
  `tests/test_projects_migration.py`: `upgrade` desde base vacía crea
  `tasks`, `downgrade` la elimina.
- **Comprobación**: `docker compose up -d`, `uv run pytest -q` (test nuevo
  en verde, resto de la suite sin cambios), `uv run ruff check .`.

## Incremento 2 — `POST /tasks`

- Endpoint que: normaliza `title` (recorta espacios, rechaza con `422` si
  no queda ningún carácter visible según las categorías Unicode `Cc`, `Cf`,
  `Zl`, `Zp`, `Zs`); valida que `project_id` exista (`404` si no); valida
  que `state_id` exista (`404` si no); si llega `due_at`, exige zona
  horaria (`422` si no la tiene) y lo normaliza a UTC; inserta y responde
  `201` con el esquema exacto (`id`, `title`, `description`, `project_id`,
  `state_id`, `due_at`), serializando `due_at` como `...Z` sin
  microsegundos o `null` si se omitió.
- Test nuevo en `tests/test_tasks.py`: creación válida con y sin
  `due_at`/`description`; título vacío y solo-espacios ASCII (`422`);
  título compuesto solo por invisibles Unicode como `U+200B` (`422`);
  `project_id` inexistente (`404`); `state_id` inexistente (`404`);
  `due_at` sin zona horaria (`422`); esquema exacto de la respuesta.
- **Comprobación**: `docker compose up -d`, `uv run pytest -q`,
  `uv run ruff check .`.

## Incremento 3 — `GET /tasks` con filtros `project_id` y `state_id`

- Endpoint que lista tareas ordenadas por `id` ascendente, admitiendo
  `project_id` y `state_id` como query params, solos o combinados (`AND`).
  Sin `overdue` todavía (incremento 7).
- Test que crea tareas en distintos proyectos/estados y verifica: lista
  completa ordenada por `id`; filtro por `project_id` solo; filtro por
  `state_id` solo; ambos combinados; filtro con un id que no existe
  devuelve lista vacía; dos llamadas idénticas devuelven el mismo orden.
- **Comprobación**: `docker compose up -d`, `uv run pytest -q`,
  `uv run ruff check .`.

## Incremento 4 — `GET /tasks/{id}`

- Endpoint que devuelve `200` con la tarea si existe, `404` con
  `{"detail": "..."}` si no.
- Test que verifica ambos casos.
- **Comprobación**: `docker compose up -d`, `uv run pytest -q`,
  `uv run ruff check .`.

## Incremento 5 — `PATCH /tasks/{id}`

- Endpoint de actualización parcial (mismo patrón `exclude_unset` que
  `PATCH /projects/{id}`): si el cuerpo incluye `title`, se normaliza y
  valida igual que en `POST` (`422`); si incluye `project_id` o
  `state_id`, se valida que existan (`404`); si incluye `due_at`, se
  valida la zona horaria (`422`) y se normaliza a UTC, permitiendo
  ponerlo en `null` explícitamente para borrarlo; `404` si la tarea no
  existe.
- Test que verifica: actualizar un campo deja los demás intactos; poner
  `due_at` en `null` lo borra; título inválido en el `PATCH` da `422`;
  `project_id`/`state_id` inexistentes en el `PATCH` dan `404`; `PATCH`
  sobre id inexistente da `404`.
- **Comprobación**: `docker compose up -d`, `uv run pytest -q`,
  `uv run ruff check .`.

## Incremento 6 — `DELETE /tasks/{id}`

- Endpoint que borra la tarea y responde `204` sin cuerpo si existía, `404`
  si no.
- Test que verifica `204` (y que un `GET` posterior a ese id da `404`), y
  `404` al borrar un id inexistente.
- **Comprobación**: `docker compose up -d`, `uv run pytest -q`,
  `uv run ruff check .`.

## Incremento 7 — `GET /tasks?overdue=true`

- Agrega el filtro `overdue=true` a `GET /tasks`: devuelve tareas con
  `due_at` anterior al instante de evaluación (UTC, al momento de la
  petición) y estado distinto de `HECHA`; una tarea sin `due_at` nunca
  está vencida; combinable con `project_id`/`state_id` igual que los
  demás filtros.
- Test que verifica: tarea vencida aparece con `overdue=true`; tarea futura
  no aparece; tarea vencida pero en estado `HECHA` no aparece; tarea sin
  `due_at` no aparece; combinación de `overdue=true` con `project_id`/
  `state_id`.
- **Comprobación**: `docker compose up -d`, `uv run pytest -q` (suite de
  Tareas completa en verde), `uv run ruff check .`.

## Incremento 8 — Reactiva la comprobación de tareas en `DELETE /projects/{id}`

- Modifica `delete_project` en `app/main.py`: si el proyecto tiene alguna
  tarea asociada, responde `409` con `{"detail": "..."}` y no borra; si no
  tiene ninguna, sigue respondiendo `204` como hasta ahora. Sin borrado en
  cascada.
- Test nuevo agregado a `tests/test_projects.py` (no se modifica ninguno de
  los existentes): crear un proyecto con una tarea asociada y verificar que
  `DELETE /projects/{id}` da `409`; el test existente de `204` sobre un
  proyecto sin tareas sigue pasando sin cambios.
- **Comprobación**: `docker compose up -d`, `uv run pytest -q` (suite
  completa del repositorio en verde), `uv run ruff check .`.

## Restricciones que se mantienen en todos los incrementos

- No se modifica `docs/contrato-api.md`, `docs/decisiones-ingenieria.md`,
  `CLAUDE.md`, `.gitignore` ni `.env`. No se abre `.env`.
- No se debilita ni elimina un test existente para conseguir verde.
- No se toca la tabla `states` ni sus migraciones.
- No se agregan recordatorios, scheduler, zona horaria preferida del
  usuario ni cambio automático de estado.
