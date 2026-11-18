#!/usr/bin/env bash
# Run on the approved Ubuntu amd64 controller host; no container restart.
set -euo pipefail
version=2.45.0-1ubuntu0.3
sha=200baf40742053089d945c83f9f1f5f57124b801d86af89da5ead9eeac90f4a0
container=stevenzxs-hermes-gateway-1
root=/opt/stevenzxs-hermes/data/delivery-controller
stage=$(mktemp -d)
trap 'echo "Bootstrap staging retained: $stage"' EXIT
cd "$stage"
apt-get download "gh=$version"
printf '%s  %s\n' "$sha" "gh_${version}_amd64.deb" | sha256sum -c -
dpkg-deb -x "gh_${version}_amd64.deb" extracted
install -d -m 700 -o 1000 -g 1000 "$root" "$root/auth"
install -m 700 -o 1000 -g 1000 extracted/usr/bin/gh "$root/gh-2.45.0-ubuntu0.3"
cat > "$root/gh" <<'SH'
#!/bin/sh
export GH_CONFIG_DIR=/opt/data/delivery-controller/auth
exec /opt/data/delivery-controller/gh-2.45.0-ubuntu0.3 "$@"
SH
chown 1000:1000 "$root/gh"
chmod 700 "$root/gh"
docker exec -u 1000 "$container" /opt/data/delivery-controller/gh --version
