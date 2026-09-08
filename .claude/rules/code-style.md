# Reglas de estilo de código

## No reescribir código para repartir o reorganizar cambios

Ninguna automatización de este proyecto que reparta o reorganice cambios ya
existentes en el árbol de trabajo (por ejemplo, para armar commits separados
a partir de un conjunto de cambios sin commitear) edita ni reescribe el
contenido de un archivo para simular el estado que tendría en un paso
intermedio.

- Cada paso de ese reparto se arma exclusivamente con `git add`, completo o
  con `git add -p`, sobre el cambio que ya existe en el árbol de trabajo.
- Cuando el split automático de `git add -p` no alcanza para separar dos
  cambios dentro de un mismo hunk, se resuelve con la edición manual del
  hunk (opción `e` de `git add -p`), quitando del parche las líneas que no
  correspondan a ese paso — eso cambia únicamente qué queda en el índice,
  nunca el archivo del árbol de trabajo.
- El archivo en disco no se toca en ningún momento de este proceso.
