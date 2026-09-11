# TaskFlow API

API de TaskFlow construida con FastAPI, gestionada con `uv` sobre Python 3.12,
persistida en PostgreSQL. El comportamiento observable de cada endpoint está
fijado en `docs/contrato-api.md`; `api.http` recorre ese contrato con una
petición por método y ruta, en un orden ejecutable.

## Puesta en marcha

1. Instalar las dependencias exactas del lockfile:

   ```bash
   uv sync --frozen
   ```

2. Levantar la base de datos:

   ```bash
   docker compose up -d
   ```

3. Aplicar las migraciones:

   ```bash
   uv run alembic upgrade head
   ```

4. Arrancar la API:

   ```bash
   uv run uvicorn app.main:app --reload
   ```

5. Probar un endpoint con `api.http`: abrirlo con un cliente HTTP que
   entienda bloques `###` (por ejemplo, la extensión REST Client de
   VS Code) y ejecutar sus peticiones en el orden en que aparecen en el
   archivo —cada una se apoya en la respuesta de la anterior—. También se
   puede copiar cualquiera de sus peticiones a `curl`.

Al terminar, detener la base de datos:

```bash
docker compose down
```

## Configuración

Copiar `.env.example` a `.env` y ajustar los valores según haga falta.
`compose.yaml` funciona con valores por defecto locales aunque no exista `.env`.

## Contrato y pruebas manuales

- `docs/contrato-api.md` fija el comportamiento observable de cada endpoint,
  sus esquemas de respuesta y sus códigos de error.
- `api.http` recorre ese contrato en la práctica: una petición por método y
  ruta, encadenadas, con casos de error incluidos.

## Especificación OpenAPI

FastAPI la genera sola a partir de las rutas y los modelos: con el servidor
corriendo se sirve en `GET /openapi.json` (y la UI interactiva en `/docs` y
`/redoc`). Sin levantar el servidor ni tocar la base de datos también se
puede obtener, construyéndola en el propio proceso de Python con
`app.openapi()` —crear el `engine` no abre conexión hasta la primera
consulta—. El resultado versionado vive en `openapi.json`; para
regenerarlo:

```bash
uv run python -c "import json; from app.main import app; json.dump(app.openapi(), open('openapi.json', 'w'), indent=2)"
```

## Otros comandos canónicos

```bash
uv run pytest -q       # tests (requieren la base de datos levantada y migrada)
uv run ruff check .    # lint
```
