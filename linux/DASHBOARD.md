# 150 HTTPS Dashboard

Compatible source: `3b421578588243f920886e6fe79a6faa87ea026e`; reuse the installed image, do not build on the server.

Public URL: https://hermes.whclaw.top. Caddy has **no basic_auth**; Hermes native password login protects the dashboard. Preserve `/health` and `/v1/*` routes to gateway port 8642. All remaining paths go to dashboard port 9119 over the existing caddy-net network. Do not publish port 9119 on the host.

Append `-f compose.dashboard.yml` to the instance's existing Compose file list (including offline, Caddy, Kimi and knowledgebase overrides). The image's native s6 service supervises the dashboard. Create root-only `dashboard.env` outside Git with `HERMES_DASHBOARD_BASIC_AUTH_USERNAME`, `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD`, and a random >=32-byte `HERMES_DASHBOARD_BASIC_AUTH_SECRET`. Store the password in a separate root-only credentials file for operator retrieval; never print it in deployment logs or commit it.

Back up the existing Compose/Caddy files and persistent data before recreating only gateway using `up -d --no-deps --pull never gateway`. Preserve image identity, resource limits, data, secrets and Caddy certificate volumes. Validate Caddy before reload. Gateway recreation briefly interrupts sessions. Use strict HTTPS verification: page/assets, native login, anonymous/wrong-password rejection, and API health/token checks. Verify process supervision, limits and absence of a host 9119 binding. A page HTTP 200 alone is not authenticated UI acceptance.

Rollback: restore only this change's Caddy block, validate/reload, remove the dashboard override from the recorded Compose list and recreate gateway using the original overrides and unchanged image. Keep data/credentials/backups; no volume deletion. Actual rollback execution must be separately recorded.

2026-11-19 user approved this configuration-only change on 150 and a temporary delivery exception through 2026-11-20 for incomplete Actions/config-package, complete Hermes orchestration and rollback evidence. This does not close existing GOV findings or authorize a new image build.

## Execution evidence (2026-11-19)

- Reused image ID `sha256:0130dc0d8009361876ff9b04ada62bc125e4057839573c5fa0f1bfffe97c8409`, source SHA above, original image-build config `6802f2de3d1f38140515b84d18358f2dca8530f6`. No image build/pull/publication.
- Consistent stopped-container data backup and original configurations: `/opt/stevenzxs-hermes/dashboard-backup-20261119T023530Z/`. Earlier live backup `dashboard-backup-20261119T023413Z` reported changing files and is not the consistent recovery copy. Socket files are intentionally omitted by tar.
- Deployed dashboard override and updated only the Hermes Caddy block; Caddy validate/reload passed. s6 reported `HERMES_DASHBOARD_READY port=9119`. Native credentials: `/opt/stevenzxs-hermes/dashboard-credentials.txt` (root-only, username `steven`); env file root-only, neither tracked.
- Strict HTTPS checks: login page 200; anonymous config 401; wrong password 401; native login 200 with cookies; authenticated home/config 200; three referenced JS assets 200 with JavaScript content type. Health 200; models anonymous/wrong token 401, existing valid token 200; main site 200.
- Running, OOM false, restart count 0; 1GiB RAM and 1536MiB combined limit restored online and persisted in instance Compose (original instance file omitted the swap limit). Only loopback 8642 is published; no host 9119 binding.
- Initial startup probes returned 502/empty response before readiness; subsequent checks above passed. Existing pnpm install-sync warning remains; no server build attempted. Native login/API checks are HTTP-level, not a full browser, model or Android regression. Rollback procedure is documented, not exercised. Governance findings remain open.
