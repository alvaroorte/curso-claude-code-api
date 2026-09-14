---
name: describir-esquema
description: Genera o actualiza docs/esquema.md con un diagrama de las tablas de la base de datos y sus relaciones, y un diccionario de datos con una fila por columna. Parte del estado real de alembic/versions/ y de los modelos de app/main.py en el momento de invocarla, no de lo ya conversado. Enlaza a docs/contrato-api.md en vez de repetir lo que ya dice ahí. Usar cuando se pide documentar, describir o dejar constancia del esquema de la base de datos. No modifica modelos, migraciones, el contrato ni la base de datos.
---

# describir-esquema

Esta skill describe el esquema de la base de datos tal como queda tras
aplicar todas las migraciones. No modifica nada: no toca `alembic/versions/`,
no toca `app/main.py`, no toca `docs/contrato-api.md` y no se conecta a
ninguna base de datos (ni para leerla). Si en algún paso hiciera falta correr
una migración o consultar Postgres para completar una respuesta, es señal de
que la migración correspondiente no está clara por sí sola — se detiene y se
lo dice al usuario, no se conecta a la base para salir del paso.

## Punto de partida: el estado real, no el recordado

Antes de escribir nada, se reconstruye el estado actual leyendo directamente
del repositorio en el momento de la invocación — nunca a partir de lo que
esta conversación ya discutió sobre el esquema, que puede haber cambiado.

Primero el mapa, sin leer contenido completo todavía:

```bash
ls alembic/versions/*.py
grep -n "^revision\|^down_revision" alembic/versions/*.py
grep -n "^class .*BaseModel" app/main.py
```

- El listado de archivos dice cuántas migraciones hay.
- Los `revision`/`down_revision` de cada archivo son lo único que hace falta
  para reconstruir el orden real de la cadena: los nombres de archivo son
  hashes, no fechas, así que un orden alfabético no sirve. Con este grep se
  arma la cadena completa (de `down_revision: None` hasta el head) sin abrir
  el cuerpo de ningún archivo todavía.
- Los nombres de clase de `app/main.py` dan el inventario de modelos sin
  traer al contexto los endpoints, las validaciones ni las consultas SQL,
  que no aportan nada a un diagrama de tablas.

Con la cadena ya ordenada, recién ahí se lee el cuerpo completo de cada
migración, en ese orden — `upgrade()` y `downgrade()` de punta a punta,
porque cada `create_table`, `add_column`, `alter_column` o `drop_column` es
un hecho del esquema que hay que capturar; no hay un atajo tipo `diff --stat`
para el contenido de una migración. De `app/main.py` solo se lee el bloque
de cada clase `BaseModel` señalada por el grep anterior, no el archivo
entero.

Si `docs/esquema.md` ya existe, también se lee antes de proponer nada: la
skill lo actualiza sobre lo que ya hay, no lo reescribe a ciegas.

## Qué produce

Un solo archivo: `docs/esquema.md`, con exactamente dos partes.

### 1. Diagrama

Un diagrama Mermaid `erDiagram`, en un bloque ```mermaid dentro del propio
Markdown. Se eligió ese formato porque:

- Es texto plano: se versiona y se diferencia como cualquier otro archivo,
  sin binarios ni herramientas externas para generarlo.
- GitHub (y la mayoría de los visores de Markdown) lo renderiza nativo, sin
  plugins ni pasos de build.

Cada tabla del dominio es una entidad, con sus columnas y el marcador de
clave primaria/foránea que reconoce la sintaxis de Mermaid (`PK`/`FK`). Cada
relación declarada por una foreign key de una migración es una línea de
relación, con la cardinalidad real (`||--o{` para "un proyecto tiene cero o
más tareas", por ejemplo) y una etiqueta corta. No se incluye
`alembic_version`: es la tabla de control de Alembic, ajena al dominio.

### 2. Diccionario de datos

Una tabla Markdown con una fila por columna de cada tabla del dominio,
columnas: `Tabla`, `Columna`, `Tipo`, `Nulable`, `Significado`.

- `Tipo` y `Nulable` se toman literalmente de la migración que crea o altera
  esa columna — nunca del modelo Pydantic, que describe la forma de la API,
  no el tipo real de la columna en Postgres.
- `Significado` se completa solo cuando el nombre y el tipo no bastan por sí
  solos (por ejemplo, qué es `sort_order`, qué garantiza el `unique` de
  `states.code`, por qué las foreign keys de `tasks` no tienen `ondelete`).
  Si el comportamiento de esa columna ya está descrito en
  `docs/contrato-api.md`, la celda enlaza a la sección correspondiente en vez
  de repetir el texto. Si el nombre y el tipo ya son evidentes
  (`projects.name: text, not null`), la celda de `Significado` se deja
  vacía — no se rellena por completar la tabla.

## No duplicar el contrato

Antes de escribir cualquier celda de `Significado`, se busca en
`docs/contrato-api.md` si ese comportamiento ya está descrito. Si está, se
enlaza; si no está —porque es un detalle de la base que el contrato omite a
propósito, o que solo se ve leyendo las migraciones en orden— se describe en
`docs/esquema.md`, que es precisamente el lugar para eso.

## Procedimiento paso a paso

1. Correr el mapa (`ls`, los dos `grep`) descrito arriba.
2. Reconstruir la cadena de migraciones desde `down_revision: None` hasta el
   head, usando solo los encabezados.
3. Leer el cuerpo completo de cada migración, en ese orden, acumulando el
   estado final de cada tabla (columnas, tipos, nulabilidad, PK, FK,
   constraints) tal como queda después de aplicar todas.
4. Leer el bloque de cada modelo Pydantic señalado por el segundo grep, solo
   como referencia para redactar `Significado` cuando haga falta — nunca
   como fuente del tipo o la nulabilidad de una columna.
5. Leer `docs/contrato-api.md` completo y, si existe, `docs/esquema.md`
   completo.
6. Armar el diagrama Mermaid con las tablas y relaciones del paso 3.
7. Armar el diccionario de datos, enlazando a `docs/contrato-api.md` en vez
   de repetir lo que ya dice, y dejando vacías las celdas de `Significado`
   que no aportan nada nuevo.
8. Mostrar el archivo completo al usuario, tal como quedaría escrito.
9. Detenerse ahí y esperar la aprobación explícita del usuario. No usar la
   herramienta de escritura de archivos sobre `docs/esquema.md` en este
   paso ni en el anterior — mostrar no es guardar, son dos pasos distintos
   y el segundo no sigue automáticamente del primero.
10. Solo después de esa aprobación, escribir (o actualizar) `docs/esquema.md`.

## Antes de guardar

El paso 8 (mostrar) y el paso 10 (escribir) nunca se colapsan en uno solo.
Terminar de armar el contenido no es la señal para guardarlo: la señal es
la respuesta del usuario aprobándolo. Si el archivo ya existe y se está
actualizando, esto aplica igual — no se sobrescribe el archivo existente
para después mostrar el resultado, se muestra el contenido propuesto y se
guarda recién después de la aprobación.

## Límite

Esta skill describe, no modifica. No escribe ni propone cambios en
`alembic/versions/`, `app/main.py` ni `docs/contrato-api.md`. No se conecta a
ninguna base de datos, ni siquiera para leerla: todo el esquema se
reconstruye de las migraciones tal como están en el repositorio. No guarda
ni sobrescribe `docs/esquema.md` sin la aprobación explícita del usuario
sobre el contenido ya mostrado. Su único artefacto de salida es
`docs/esquema.md`.
