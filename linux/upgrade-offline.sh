#!/usr/bin/env bash
# Upgrade existing Hermes deployment with verified offline image.
# Preserves data, secrets, and configuration. Requires explicit operator selection.
set -euo pipefail

test "$(id -u)" = 0 || { echo 'Run via sudo'; exit 1; }
bundle=$(cd "$(dirname "$0")" && pwd)
target=/opt/stevenzxs-hermes

# Validate mode: this script is for upgrade only, not first-install.
if [ ! -d "$target" ]; then
    echo 'No existing deployment found; use install-offline.sh for first-install'
    exit 1
fi

# Verify bundle before any service disruption.
python3 "$bundle/offline_bundle.py" verify "$bundle"
image_id=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["imageId"])' "$bundle/manifest.json")
tag=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["localTag"])' "$bundle/manifest.json")

# Load and validate image before stopping services.
gzip -dc "$bundle/image.tar.gz" | docker load
test "$(docker image inspect "$tag" --format '{{.Id}}')" = "$image_id"
docker run --rm --network none --entrypoint /opt/hermes/.venv/bin/python "$image_id" -c \
  'import json,sys; s=json.load(open("/opt/hermes/install-stamp.json")); p=json.load(open("/etc/hermes/image-provenance.json")); assert s["commit"] == sys.argv[1] == p["revision"]; assert s["baseVersion"] == "0.23.1"; assert s["distribution"] == "docker"; assert s["updateMechanism"] == "external"; print("Internal source identity verified")' \
  "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["sourceCommit"])' "$bundle/manifest.json")"

# Consistent backup before mutation.
backup_dir="$target/backup-$(date +%Y%m%dT%H%M%SZ)"
install -d -m 0700 "$backup_dir"
cp -a "$target/.env" "$backup_dir/"
install -m 0644 "$target/compose.yml" "$backup_dir/compose.yml"
# Data directory is preserved in place; only configuration and image reference are updated.

# Build the compose argument list from the instance's complete existing override
# stack; never silently drop caddy/kimi/dashboard/knowledgebase overrides.
compose_args=(-f compose.yml)
for override in "$target"/compose.*.yml; do
    [ -e "$override" ] || continue
    install -m 0644 "$override" "$backup_dir/"
    compose_args+=(-f "$override")
done

# Update image reference only; preserve runtime.env and all other files.
printf 'HERMES_IMAGE=%s\n' "$tag" > "$target/.env"
chmod 0600 "$target/.env"
install -m 0644 "$bundle/manifest.json" "$target/offline-manifest.json"

cd "$target"
docker compose "${compose_args[@]}" config --quiet
docker compose "${compose_args[@]}" up -d --pull never

# Health check.
sleep 2
for i in $(seq 1 30); do
    code=$(curl -s -o /dev/null -w '%{http_code}' -m 2 http://127.0.0.1:8642/health || true)
    [ "$code" = "200" ] && break
    sleep 2
done
[ "$code" = "200" ] || { echo 'Health check failed after upgrade'; exit 1; }

echo 'Upgrade complete. Rollback: restore .env from backup and restart compose.'
echo "Backup location: $backup_dir"
