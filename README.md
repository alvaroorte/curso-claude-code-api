# TaskFlow API

API de TaskFlow construida con FastAPI, gestionada con `uv` sobre Python 3.12.
Esta primera entrega expone únicamente `GET /health`; el resto del contrato
(`docs/contrato-api.md`) se implementa en entregas posteriores.

## Recorrido canónico

1. Instalar dependencias exactas del lockfile:

   ```bash
   uv sync --frozen
   ```

2. Ejecutar la batería de tests:

   ```bash
   uv run pytest -q
   ```

3. Ejecutar el linter:

   ```bash
   uv run ruff check .
   ```

4. Levantar los servicios de infraestructura (PostgreSQL):

   ```bash
   docker compose up -d
   ```

5. Arrancar la API en local:

   ```bash
   uv run uvicorn app.main:app --reload
   ```

6. Al terminar, detener los servicios de infraestructura:

   ```bash
   docker compose down
   ```

## Configuración

Copia `.env.example` a `.env` y ajusta los valores si lo necesitas.
`compose.yaml` funciona con valores por defecto locales aunque no exista `.env`.
