# Glosario

## Idempotente

Una operación es idempotente cuando ejecutarla varias veces produce el mismo
resultado que ejecutarla una sola vez: no hay efectos acumulados por repetir
la llamada.

Ejemplo en este proyecto: el seed del catálogo de estados
(`docs/contrato-api.md`) debe ser idempotente —correr la migración que lo
inserta dos veces deja la base en el mismo estado que correrla una vez, sin
duplicar filas ni fallar por conflicto.
