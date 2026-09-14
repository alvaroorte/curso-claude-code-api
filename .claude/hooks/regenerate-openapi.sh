#!/usr/bin/env bash
set -uo pipefail

if uv run python -c "import json; from app.main import app; json.dump(app.openapi(), open('openapi.json', 'w'), indent=2)" >/tmp/regenerate-openapi-err.log 2>&1; then
  msg="openapi.json se regeneró automáticamente. docs/esquema.md puede haber quedado desactualizado: regeneralo con la skill describir-esquema."
else
  msg="No se pudo regenerar openapi.json automáticamente (ver /tmp/regenerate-openapi-err.log). Corré el comando de docs/README.md a mano. docs/esquema.md también puede haber quedado desactualizado: regeneralo con la skill describir-esquema."
fi

python3 -c "import json,sys; print(json.dumps({'systemMessage': sys.argv[1]}))" "$msg"
