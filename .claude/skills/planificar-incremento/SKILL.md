---
name: planificar-incremento
description: Redacta un plan de incremento para este repositorio (TaskFlow), contrastado contra el contrato de API y las decisiones de ingeniería, con incrementos numerados y comprobación ejecutable cada uno. Usar cuando se pide planificar una funcionalidad nueva antes de implementarla. No implementa código, no instala dependencias, no toca la base de datos.
---

# planificar-incremento

Esta skill produce un documento de plan en `docs/`. No escribe ni modifica
código de la aplicación, no instala dependencias, no ejecuta migraciones ni
toca la base de datos. Si en algún paso la tarea pide hacer algo de eso,
deténte y dile al usuario que eso corresponde a la implementación, fuera de
esta skill.

## Contra qué se planifica

Antes de escribir una sola línea del plan, lee estos documentos y planifica
en función de lo que digan, no de buenas prácticas generales:

1. `docs/contrato-api.md` — fija el comportamiento observable de la API. El
   plan no puede proponer un comportamiento que lo contradiga. Si el ticket
   exige cambiar el contrato, el plan debe decir explícitamente qué línea del
   contrato cambia y en qué incremento, nunca dejarlo implícito.
2. `docs/decisiones-ingenieria.md` — decisiones del equipo que no se deducen
   del código (base de datos, pruebas, datos locales). El plan hereda estas
   decisiones sin repetirlas ni cuestionarlas; si un incremento parece
   necesitar contradecir una, pregúntalo (ver más abajo) en vez de resolverlo
   por tu cuenta.
3. `README.md` — comandos canónicos del repositorio. Las comprobaciones de
   cada incremento se construyen con estos comandos, no con comandos
   inventados.
4. El estado real del código en el momento de planificar (estructura de
   `app/`, `tests/`, migraciones existentes en `alembic/versions/` si las
   hay). El plan describe una sección "Qué existe ya" basada en lectura
   directa del repositorio, no en memoria de conversaciones anteriores.

Si existe un plan previo relacionado en `docs/` (por ejemplo, un plan de un
incremento anterior sobre el mismo área), léelo también: el nuevo plan no
debe repetir decisiones ya tomadas ahí ni contradecirlas sin decirlo.

## Dónde se escribe el resultado

El plan se guarda como un archivo nuevo en `docs/`, con un nombre en
kebab-case que diga de qué es el plan (por ejemplo,
`docs/plan-proyectos.md` para un incremento sobre proyectos). No se
sobrescribe un plan anterior de otro alcance; si el plan es una continuación
directa de uno existente, se edita ese mismo archivo en vez de crear uno
paralelo.

## Estructura del plan

1. **Alcance**: qué parte del contrato cubre este plan y qué queda fuera de
   alcance explícitamente. "Fuera de alcance" se declara por nombre (qué
   endpoints, campos o comportamientos no se tocan), nunca se deja implícito
   por omisión.
2. **Qué existe ya**: estado actual del código relevante, verificado por
   lectura directa (archivos, dependencias en `pyproject.toml`, migraciones
   existentes), no asumido.
3. **Incrementos numerados**: cada incremento es una unidad que se
   implementa, se confirma por separado y se detiene a esperar aprobación
   antes de encadenar el siguiente. Cada incremento declara:
   - Qué cambia (archivos o comportamiento).
   - Su propia comprobación ejecutable: los comandos exactos (tomados de
     `README.md`) que otra persona correría para verificar que ese
     incremento, y solo ese incremento, quedó bien. No se acumula toda la
     verificación en un incremento final.
4. **Restricciones que se mantienen en todos los incrementos**: reglas
   heredadas de `docs/decisiones-ingenieria.md` y de instrucciones del
   ticket que aplican a todo el plan (por ejemplo, qué archivos no se tocan).

## Ninguna decisión queda aplazada

El plan no contiene condicionales sobre decisiones que ya se podrían resolver
leyendo el repositorio ("probablemente", "se podría", "si hiciera falta").
Cada elección de diseño se resuelve de una de estas dos formas:

- Se decide, citando en qué parte del contrato, de las decisiones de
  ingeniería o del código existente se apoya la decisión.
- Si no hay con qué decidirla (el contrato no lo cubre, no hay una decisión
  de ingeniería al respecto, y el ticket no lo aclara), se detiene la
  redacción del plan en ese punto y se pregunta al usuario. No se avanza
  proponiendo una opción por defecto "salvo que me digas lo contrario": se
  pregunta y se espera la respuesta antes de seguir.

## Procedimiento paso a paso al invocar esta skill

1. Leer `docs/contrato-api.md`, `docs/decisiones-ingenieria.md`, `README.md`
   y cualquier plan previo relevante en `docs/`.
2. Inspeccionar el estado actual del código relacionado con el alcance
   pedido (sin modificarlo).
3. Redactar la sección de alcance, incluyendo qué queda fuera.
4. Redactar "Qué existe ya" a partir de lo observado en el paso 2.
5. Dividir el trabajo en incrementos numerados, cada uno con su
   comprobación ejecutable propia.
6. Revisar el borrador buscando condicionales o decisiones aplazadas; por
   cada una encontrada, resolverla con una cita del repositorio o preguntar
   al usuario antes de continuar.
7. Mostrar el plan completo al usuario antes de guardar nada.
8. Solo tras la aprobación del usuario, guardar el archivo en `docs/` con el
   nombre acordado.

## Límite

Esta skill planifica. No crea ni modifica código de la aplicación, no
instala dependencias, no ejecuta migraciones y no toca la base de datos. Su
único artefacto de salida es el archivo de plan en `docs/`.
