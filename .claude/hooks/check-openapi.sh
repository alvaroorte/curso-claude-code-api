#!/usr/bin/env bash
set -euo pipefail

tmp="$(mktemp)"
cleanup() { rm -f "$tmp"; }
trap cleanup EXIT

if ! uv run python -c "import json; from app.main import app; json.dump(app.openapi(), open('$tmp', 'w'), indent=2)" >/dev/null 2>&1; then
  echo "No se pudo regenerar el esquema OpenAPI para compararlo (falló el comando de regeneración)." >&2
  echo "Corré el comando de docs/README.md (sección 'Especificación OpenAPI'), revisá el error y reintentá el commit." >&2
  exit 2
fi

if diff -q "$tmp" openapi.json >/dev/null 2>&1; then
  exit 0
fi

echo "openapi.json no coincide con lo que genera app/main.py ahora mismo." >&2
echo "Regeneralo y agregalo al commit:" >&2
echo "  uv run python -c \"import json; from app.main import app; json.dump(app.openapi(), open('openapi.json', 'w'), indent=2)\"" >&2
echo "  git add openapi.json" >&2
echo "Después reintentá el commit." >&2
exit 2
