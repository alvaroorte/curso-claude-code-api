---
name: actualizar-memoria
description: Al cierre de una sesión de trabajo, o cuando el usuario lo pide explícitamente ("actualiza las memorias", "guarda lo que aprendimos"), repasa toda la conversación y el estado del repositorio para actualizar el sistema de memoria persistente de Claude Code (memorias user/feedback/project/reference y su índice MEMORY.md) y, si corresponde, propone cambios a los documentos de contexto del proyecto versionados en git (docs/decisiones-ingenieria.md, CLAUDE.md). No implementa código, nunca toca docs/contrato-api.md, y no commitea nada por su cuenta.
---

# actualizar-memoria

Esta skill no escribe código de la aplicación ni toca la base de datos. Su
único trabajo es dejar registrado, en el lugar correcto, lo que se aprendió
en la sesión: memoria personal persistente y, cuando aplica, documentos de
contexto del proyecto.

## Dos sistemas distintos, con reglas distintas

"Memorias" y "contexto" no son lo mismo, y esta skill no los mezcla:

1. **Memoria personal** (`~/.claude/projects/.../memory/`, con su índice
   `MEMORY.md`): persiste entre conversaciones, es propia de este usuario y
   no está versionada en git. Aquí van preferencias de colaboración,
   correcciones, confirmaciones de enfoque, estado efímero del proyecto
   (ramas, PRs, plazos) y referencias a sistemas externos.
2. **Contexto del proyecto versionado en git** (`CLAUDE.md`,
   `docs/decisiones-ingenieria.md`, `docs/contrato-api.md`): lo ve cualquiera
   que clone el repo, no solo este usuario. Cambiarlo es una decisión de
   equipo, no un efecto secundario de esta skill.

Esta skill puede tocar el primero directamente. Del segundo, solo
**propone** un texto y espera aprobación antes de editar el archivo; y
`docs/contrato-api.md` no lo toca bajo ninguna circunstancia, porque
`CLAUDE.md` ya fija que solo se modifica cuando un ticket lo pide
explícitamente.

## Punto de partida

Antes de escribir nada:

1. Lee `MEMORY.md` completo.
2. Abre los archivos de memoria existentes que puedan relacionarse con lo
   conversado en esta sesión (por nombre o por tema), no solo los que
   recuerdes de memoria de la propia conversación — pueden haber cambiado.
3. Relee la sesión actual completa, no un resumen de ella: los aprendizajes
   suelen estar en correcciones o confirmaciones puntuales, fáciles de
   perder si se trabaja solo con la impresión general de lo hablado.

## Qué cuenta como aprendizaje a guardar

Para cada tipo, la sesión puede haber dejado candidatos:

- **user**: algo nuevo sobre el rol, los objetivos o el conocimiento previo
  del usuario que cambia cómo conviene explicarle o proponerle cosas.
- **feedback**: una corrección explícita ("no hagas X", "dejá de hacer Y") o
  una confirmación de un enfoque no obvio que el usuario aceptó sin
  objeción. Ambas cuentan — no guardar solo correcciones hace que la skill
  olvide enfoques ya validados y se vuelva innecesariamente cautelosa.
- **project**: hechos sobre trabajo en curso (quién hace qué, por qué,
  para cuándo) que no se deducen leyendo el código o el git log.
- **reference**: dónde vive información externa al repo (tableros, canales,
  sistemas de tickets) que se mencionó y no vivía ya en una memoria.

## Qué no va a memoria

Se descarta cualquier candidato que caiga en estas categorías, incluso si el
usuario pidió "guardar todo":

- Patrones de código, convenciones, arquitectura o estructura de archivos —
  se leen del repo en el momento en que hagan falta.
- Historial de cambios o autoría — `git log`/`git blame` son la fuente.
- Recetas de depuración puntuales — la corrección queda en el código y su
  commit.
- Cualquier cosa que ya esté en un `CLAUDE.md` o en `.claude/rules/`.
- Detalles efímeros de la tarea en curso (eso es trabajo para un Plan o una
  lista de tareas de la sesión, no para memoria entre sesiones).

## Memoria personal vs. propuesta a un documento versionado

Un aprendizaje va a **memoria personal** cuando es sobre cómo trabajar con
este usuario o sobre el estado del proyecto en un momento dado.

Un aprendizaje es candidato a **`docs/decisiones-ingenieria.md`** cuando es
una decisión de equipo, no una preferencia del usuario en esta herramienta —
algo que cualquier persona que trabaje en el repo necesitaría conocer (base
de datos, forma de probar, manejo de datos locales). En ese caso:

- No se edita el archivo directamente. Se muestra al usuario el texto
  propuesto y se espera su aprobación.
- Si el aprendizaje implica un cambio de **comportamiento observable de la
  API**, no se resuelve aquí en absoluto: se señala la discrepancia contra
  `docs/contrato-api.md` y se pregunta al usuario, porque ese archivo solo
  cambia cuando un ticket lo pide explícitamente.

## Procedimiento paso a paso

1. Leer `MEMORY.md` y las memorias relacionadas ya existentes (ver "Punto de
   partida").
2. Releer la sesión completa e identificar candidatos por tipo (ver "Qué
   cuenta como aprendizaje a guardar").
3. Filtrar cada candidato contra "Qué no va a memoria". Descartar los que
   apliquen.
4. Para cada candidato que sobrevive, revisar si ya existe una memoria que
   cubra el mismo hecho:
   - Si existe y sigue vigente, actualizarla en el mismo archivo en vez de
     crear una nueva.
   - Si existe y el aprendizaje nuevo la contradice, corregir esa memoria
     para que quede una sola versión vigente — nunca dejar dos memorias
     contradictorias conviviendo.
   - Si no existe, crear un archivo nuevo con el frontmatter completo
     (`name`, `description`, `metadata.type`) y, para `feedback` y
     `project`, las líneas **Why:** y **How to apply:**. Enlazar con
     `[[nombre]]` a memorias relacionadas, existan o no todavía.
5. Actualizar `MEMORY.md`: una línea por memoria creada o cuyo resumen
   cambió, bajo 150 caracteres, sin contenido de memoria en el índice mismo.
6. Revisar los candidatos descartados en el paso 3 que sean decisiones de
   equipo (no de usuario): para esos, redactar el texto propuesto para
   `docs/decisiones-ingenieria.md` y mostrarlo al usuario, dejando claro que
   no se ha escrito todavía.
7. Cerrar con un resumen breve: qué memorias se crearon, cuáles se
   actualizaron, y qué quedó propuesto para `docs/decisiones-ingenieria.md`
   pendiente de aprobación (si algo quedó pendiente).

## Límite

- No borra memorias salvo pedido explícito del usuario.
- No inventa aprendizajes que no ocurrieron en la conversación ni los
  infiere de fuentes fuera de ella.
- No escribe nunca en `docs/contrato-api.md`.
- No commitea ningún cambio por su cuenta: si `docs/decisiones-ingenieria.md`
  o `CLAUDE.md` terminan editados, quedan en el árbol de trabajo para que el
  usuario decida cuándo y cómo confirmarlos.
- No reemplaza a un Plan ni a una lista de tareas de la sesión: no registra
  estado de una tarea en curso, solo lo que ya se aprendió o decidió.
