# Reglas de testing

## Reproducir antes de corregir

Ante cualquier fallo reportado, antes de tocar el código que lo corrige:

- Se reproduce primero con un caso real contra el sistema: un test que se
  ejecuta y falla en rojo, o una ejecución real (manual, contra la API
  corriendo, un script) que deja evidencia concreta del fallo.
- La corrección se escribe recién después de tener esa reproducción, nunca
  antes ni en paralelo.

## La corrección nunca oculta la reproducción

- El caso que reprodujo el fallo se queda tal como se escribió: no se borra,
  no se debilita ni se reescribe para que deje de fallar en rojo antes de
  aplicar la corrección. Si es un test, sigue existiendo y pasa a estar en
  verde una vez corregido el código — no se retira ni se reemplaza por otro.
- Si la reproducción fue una ejecución real sin test dedicado, la evidencia
  de esa ejecución (comando y salida) se muestra tal como salió, sin editarla
  para que parezca que el fallo nunca ocurrió.
