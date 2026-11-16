#!/usr/bin/env bash
set -euo pipefail
test "$(id -u)" = 0 || { echo 'Run via sudo'; exit 1; }
bundle=$(cd "$(dirname "$0")" && pwd)
target=/opt/stevenzxs-hermes
test ! -e "$target" || { echo 'Existing deployment: refusing overwrite'; exit 1; }
test -z "$(ss -H -ltn 'sport = :8642')" || { echo 'Port occupied'; exit 1; }
python3 "$bundle/offline_bundle.py" verify "$bundle"
image_id=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["imageId"])' "$bundle/manifest.json")
tag=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["localTag"])' "$bundle/manifest.json")
gzip -dc "$bundle/image.tar.gz" | docker load
test "$(docker image inspect "$tag" --format '{{.Id}}')" = "$image_id"
docker run --rm --network none --entrypoint /opt/hermes/.venv/bin/python "$image_id" -c \
  'import json; s=json.load(open("/opt/hermes/install-stamp.json")); assert s["commit"]=="3b421578588243f920886e6fe79a6faa87ea026e"; assert s["baseVersion"]=="0.23.1"'
install -d -m 0750 "$target"
install -d -m 0700 -o 1000 -g 1000 "$target/data"
install -m 0644 "$bundle/compose.yml" "$target/compose.yml"
printf 'services:\n  gateway:\n    pull_policy: never\n' > "$target/compose.offline.yml"
printf 'HERMES_IMAGE=%s\n' "$tag" > "$target/.env"
chmod 0600 "$target/.env"
install -m 0644 "$bundle/manifest.json" "$target/offline-manifest.json"
python3 - "$target/runtime.env" <<'PY'
import os,secrets,sys
fd=os.open(sys.argv[1],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f: f.write('API_SERVER_KEY='+secrets.token_urlsafe(48)+'\n')
PY
cd "$target"
docker compose -f compose.yml -f compose.offline.yml config --quiet
docker compose -f compose.yml -f compose.offline.yml up -d --pull never
echo 'Offline installation started; health/authentication checks remain required'
