#!/usr/bin/env bash
# Optional manual tool only. Never invoked by installation or delivery workflows.
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then
  echo "Run with sudo bash change-dashboard-password.sh" >&2
  exit 1
fi
cd /opt/stevenzxs-hermes
echo "Target: Hermes on this host, /opt/stevenzxs-hermes"
echo "This recreates gateway and briefly interrupts sessions; Caddy/API token stay unchanged."
read -r -p "Type CHANGE to continue: " confirmation </dev/tty
[[ "$confirmation" == CHANGE ]] || exit 1

python3 - <<'PY'
from pathlib import Path
from getpass import getpass
import os
import secrets
import tempfile

root = Path('/opt/stevenzxs-hermes')
env_path = root / 'dashboard.env'
credentials_path = root / 'dashboard-credentials.txt'
if not env_path.is_file():
    raise SystemExit('dashboard.env not found; nothing changed.')
password = getpass('New password (at least 8 characters): ')
confirm = getpass('Confirm password: ')
if password != confirm:
    raise SystemExit('Passwords do not match; nothing changed.')
if len(password) < 8:
    raise SystemExit('Password must contain at least 8 characters.')
if password != password.strip() or any(ord(c) < 32 or ord(c) == 127 for c in password):
    raise SystemExit('No leading/trailing whitespace or control characters allowed.')

def quote(value):
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('$', '$$') + '"'

updates = {
    'HERMES_DASHBOARD_BASIC_AUTH_PASSWORD': quote(password),
    'HERMES_DASHBOARD_BASIC_AUTH_SECRET': secrets.token_hex(32),
}
lines = [line for line in env_path.read_text().splitlines()
         if line.split('=', 1)[0].strip() not in updates]
lines.extend(f'{key}={value}' for key, value in updates.items())

def private_write(path, content):
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

private_write(env_path, '\n'.join(lines) + '\n')
private_write(credentials_path, 'URL: https://hermes.whclaw.top\nUsername: steven\nPassword: ' + password + '\n')
print('Password saved with root-only permissions. Recreating gateway next.')
PY

compose=(docker compose
  -f compose.yml -f compose.offline.yml -f compose.caddy.yml
  -f compose.kimi.yml -f compose.knowledgebase.yml -f compose.dashboard.yml)
"${compose[@]}" config --quiet
"${compose[@]}" up -d --no-deps --pull never --force-recreate gateway
echo "Recreation command completed. Wait for readiness, then verify new login and old-password rejection."
echo "If recreation failed, the saved password takes effect only after successful recreation."
