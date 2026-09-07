---
name: segmentar-commits
description: Reparte los cambios pendientes del working tree en commits atómicos, cada uno con una sola intención, en un orden donde cada commit deja el repositorio en un estado comprobable, usando Conventional Commits con el prefijo elegido por intención y no por tipo de archivo. Empieza del estado real del repositorio (git status y diffstat), no de lo ya conversado. Muestra el reparto propuesto y espera aprobación antes de confirmar cualquier commit. Usar cuando hay cambios sin commitear que hace falta dividir en varios commits.
---

# segmentar-commits

Esta skill reparte los cambios sin commitear del working tree en varios
commits atómicos. No escribe código de la aplicación, no corrige nada de lo
que encuentra: toma los cambios tal como están y decide cómo agruparlos.

## Punto de partida: el estado real del repositorio

Antes de proponer nada, se inyecta:

```bash
git status --porcelain=v1
git diff --stat
```

No se inyecta `git diff` completo. Lo que hace falta en este punto es el
**mapa** del cambio (qué archivos, cuántas líneas por archivo, si es nuevo,
modificado o borrado), no su contenido. El reparto en commits se decide casi
siempre con ese mapa: un archivo nuevo suele ser una sola intención, una
migración nueva junto con su test suele ser una sola intención, etc.

No se asume el estado del repositorio a partir de lo hablado antes en la
conversación — puede haber cambiado desde entonces. Se lee de nuevo cada vez
que se invoca la skill.

## Cuándo hace falta leer el diff completo de un archivo

Solo cuando el mapa no alcanza para decidir: un archivo aparece en el
diffstat con cambios que, por su tamaño o por lo que se sabe del trabajo
hecho, mezclan más de una intención (por ejemplo, un mismo archivo de
endpoints al que se le agregaron varias rutas independientes entre sí). En
ese caso, y solo para ese archivo, se lee su `git diff` completo para decidir
qué hunks van en cada commit. Nunca se lee el diff completo de un archivo
cuya asignación a un único commit ya es clara por el mapa.

## Cómo se agrupan los cambios en commits

- Cada commit tiene **una sola intención**: un cambio de comportamiento, una
  migración, un conjunto de tests que prueba lo que el commit anterior ya
  dejó en pie. Si un archivo mezcla dos intenciones, se separa por hunks
  (`git add -p`, con edición manual del hunk si hace falta) en vez de
  meterlo entero en un solo commit.
- El **orden** entre commits no es arbitrario: cada commit, aplicado sobre el
  anterior, debe dejar el repositorio en un estado que se pueda comprobar
  (correr, testear, lintear) sin depender de un cambio que todavía no se
  commiteó. Ejemplos de este orden: una migración de esquema antes que el
  código que la usa; un modelo o helper antes que el endpoint que lo llama;
  el código de un endpoint antes que uses tests adicionales que dependen de
  otro endpoint todavía no commiteado.
- Los tests que prueban un cambio van en el mismo commit que ese cambio,
  salvo que el propio reparto tenga una intención dedicada a tests (por
  ejemplo, tests de regresión agregados aparte, después de que el
  comportamiento ya está commiteado).

## Prefijo de Conventional Commits

El prefijo se elige por lo que el commit **hace**, nunca por la extensión o
carpeta del archivo que toca. Un cambio a un archivo de test no es
automáticamente `test:` si su intención real es agregar comportamiento nuevo
(`feat:`) o corregir uno existente (`fix:`); un cambio a un `.md` no es
automáticamente `docs:` si en realidad documenta una decisión de
`chore:`. Guía de intención → prefijo (no exhaustiva, se razona caso por
caso):

| Intención del commit | Prefijo |
|---|---|
| Agrega comportamiento observable nuevo | `feat:` |
| Corrige un comportamiento incorrecto | `fix:` |
| Reordena o limpia código sin cambiar comportamiento | `refactor:` |
| Agrega o cambia tests sin tocar el comportamiento probado | `test:` |
| Cambia solo documentación | `docs:` |
| Cambia configuración, dependencias o tareas de mantenimiento | `chore:` |

## Procedimiento paso a paso

1. Correr `git status --porcelain=v1` y `git diff --stat` para obtener el
   mapa real del cambio.
2. Agrupar los archivos (y, cuando el mapa no alcance, los hunks dentro de un
   archivo — leyendo su diff completo solo en ese caso) en commits de una
   sola intención cada uno.
3. Ordenar los commits para que cada uno, aplicado sobre el anterior, deje el
   repositorio en un estado comprobable.
4. Elegir el prefijo de Conventional Commits de cada commit por su intención,
   no por el tipo de archivo que toca.
5. Mostrar al usuario el reparto propuesto completo: qué archivos (o qué
   hunks, si aplica) y con qué mensaje va en cada commit, en el orden
   propuesto.
6. Esperar la aprobación explícita del usuario. No preparar (`git add`) ni
   commitear nada antes de esa aprobación.
7. Tras la aprobación, ejecutar el reparto commit por commit (`git add` o
   `git add -p` según corresponda, luego `git commit`), verificando con
   `git status` entre uno y otro que solo se preparó lo que correspondía a
   ese commit.

## Límite

Esta skill no corrige, reescribe ni mejora el código que encuentra: reparte
los cambios tal como están. No hace `git push`, no reescribe historia
existente (`rebase`, `commit --amend`) y no commitea nada sin aprobación
explícita del reparto propuesto.
