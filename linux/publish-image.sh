#!/usr/bin/env bash
set -euo pipefail
delivery=${1:?verified delivery directory}
image=$(cat "$delivery/image.txt")
python3 - "$delivery" "$image" <<'PY'
import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
r = json.loads((p / 'build-record.json').read_text())
assert r['image'] == sys.argv[2]
assert sys.argv[2].startswith('ghcr.io/stevenzxs/hermes-agent:src-')
s = json.loads((p / 'gateway-smoke.json').read_text())
assert s == dict(health=200, unauthenticated=401, wrong_token=401, authenticated=200)
assert 'Internal source identity verified' in (p / 'identity-check.log').read_text()
PY
docker push "$image" 2>&1 | tee "$delivery/push.log"
docker buildx imagetools inspect "$image" | tee "$delivery/registry-inspect.txt"
digest=$(awk '$1 == "Digest:" {print $2; exit}' "$delivery/registry-inspect.txt")
[[ "$digest" =~ ^sha256:[0-9a-f]{64}$ ]]
printf 'ghcr.io/stevenzxs/hermes-agent@%s\n' "$digest" > "$delivery/published-image.txt"
echo 'Registry digest recorded; server pull and deployment are separate verification gates'
