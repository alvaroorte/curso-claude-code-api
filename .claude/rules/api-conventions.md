# Convenciones de la API

Los endpoints de la API viven en `app/main.py`.

## Esquema de respuesta exacto

Cualquier endpoint nuevo o modificado en `app/main.py` respeta el esquema de
respuesta exacto que fija `docs/contrato-api.md`: ni un campo de más ni de
menos. Un campo de sobra rompe a quien consuma la API igual que uno que
falta — esa es la regla del propio contrato, no una preferencia de estilo.

Si el endpoint necesita devolver un campo que el contrato todavía no
describe, primero se actualiza `docs/contrato-api.md` (en su propio commit)
y recién después se toca `app/main.py` y sus tests.

## Un campo nuevo se agrega en sus tres capas

Cualquier campo nuevo en un recurso existente se agrega en tres capas,
igual que se hizo con `priority` en la tabla `tasks`:

1. **Migración** (`alembic/versions/`): una migración nueva que agrega la
   columna, con `upgrade` y `downgrade` simétricos — nunca se edita una
   migración ya integrada.
2. **Esquema** (`app/main.py`): el campo se agrega a los modelos Pydantic
   de request y de respuesta del recurso (creación, actualización y
   lectura), y a las consultas SQL de los endpoints que leen o escriben ese
   recurso.
3. **Validación** (`app/main.py`): el endpoint valida el campo nuevo según
   lo que diga el contrato para él — tipo, obligatoriedad, rango o catálogo
   si lo tiene. Si el contrato no le impone una restricción (como pasó con
   `priority`), no se inventa una que el contrato no pide.

Las tres capas se agregan juntas, no una capa comprometida sin las otras dos.
