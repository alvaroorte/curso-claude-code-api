# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Fuentes de verdad

- `docs/contrato-api.md` fija el comportamiento observable de la API. Solo se
  modifica cuando el ticket dice explícitamente que cambia el contrato; ante
  una discrepancia entre código y contrato, el contrato manda.
- `docs/decisiones-ingenieria.md` recoge decisiones del equipo que no se
  deducen del código (base de datos, pruebas, datos locales). Consúltalo antes
  de decidir cómo implementar algo, no solo qué implementar.
- `README.md` contiene los comandos canónicos del repositorio.

## Comandos canónicos

```bash
uv sync --frozen      # instalar dependencias
uv run pytest -q      # tests
uv run ruff check .   # lint
```

Para el resto (levantar la API, infraestructura Docker, configuración), ver
`README.md`.

## Base de datos

- Las pruebas que ejercitan persistencia corren contra PostgreSQL. No uses
  SQLite: no reproduce las mismas restricciones, tipos ni migraciones.
  Detalle en `docs/decisiones-ingenieria.md`.

## Datos locales

- No abras, muestres, edites ni confirmes (`git add`/commit) `.env`: puede
  contener secretos. Para nombres de variables usa `.env.example`.

## Pruebas

- No debilites ni elimines un test existente para conseguir verde. Si el
  comportamiento acordado cambió, primero se actualiza el contrato
  (`docs/contrato-api.md`) y después el test, en un commit separado.
