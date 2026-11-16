#!/usr/bin/env bash
# Run on the approved Ubuntu server from a reviewed configuration checkout/package.
set -euo pipefail
image=${1:?verified immutable image reference}
[[ "$image" =~ ^(ghcr.io|ghcr.nju.edu.cn)/stevenzxs/hermes-agent@sha256:[0-9a-f]{64}$ ]]
target=/opt/stevenzxs-hermes
test ! -e "$target" || { echo 'Deployment already exists; first-install refuses overwrite'; exit 1; }
test -z "$(ss -H -ltn 'sport = :8642')" || { echo 'Port 8642 occupied'; exit 1; }
docker image inspect "$image" >/dev/null
docker run --rm --network none --entrypoint /opt/hermes/.venv/bin/python "$image" -c \
  'import json; s=json.load(open("/opt/hermes/install-stamp.json")); assert s["commit"]=="3b421578588243f920886e6fe79a6faa87ea026e"; assert s["baseVersion"]=="0.23.1"'
install -d -m 0750 "$target"
install -d -m 0700 -o 1000 -g 1000 "$target/data"
install -m 0644 "$(dirname "$0")/compose.yml" "$target/compose.yml"
printf 'HERMES_IMAGE=%s\n' "$image" > "$target/.env"
chmod 0600 "$target/.env"
python3 - "$target/runtime.env" <<'PY'
import os, secrets, sys
fd = os.open(sys.argv[1], os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as f:
    f.write('API_SERVER_KEY=' + secrets.token_urlsafe(48) + '\n')
PY
cd "$target"
docker compose config --quiet
docker compose up -d
echo 'Started; health, authentication, persistence and resource checks still required'
