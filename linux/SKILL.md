---
name: hermes-linux-docker-deploy
description: Deploy the pinned Hermes v0.23.1 Linux AMD64 image to an explicitly approved Ubuntu Docker host; verify identity, health, authentication and persistent storage without changing existing services.
---

# Hermes Linux Docker delivery

Scope: Hermes source 3b421578588243f920886e6fe79a6faa87ea026e, Linux AMD64, Docker Compose. Never default to a production host. Obtain explicit host and operation approval. Current approved target: ubuntu@150.158.83.70, first install /opt/stevenzxs-hermes, loopback 8642 only.

## Prerequisites and artifact verification

Read the knowledgebase delivery standard and ledger. Check stevenzxs Packages inventory before building. Use build-image.sh in WSL only with approved resource budget, then identity/version and gateway-smoke evidence, then publish-image.sh. Preserve source/config SHAs and registry digest; local tests do not replace Actions acceptance. Never build on this resource-constrained server.

Pull only the verified ghcr.io/stevenzxs/hermes-agent@sha256 digest. Public package needs no credential. Private package requires separately approved read-only access, never the local write token. Compare remote RepoDigests, architecture, OCI source/config labels and internal install-stamp. Do not trust latest.

Approved transport alternative: ghcr.nju.edu.cn/stevenzxs/hermes-agent with the exact same verified digest. Validate the proxy manifest digest against GHCR before pulling. This changes only the project's image reference; do not change global Docker registry configuration or restart Docker. Cancel any old pull/waiting installer before switching to prevent concurrent installs.

## First install

Review compose.yml and install-first.sh. Transfer the reviewed files to a new private staging directory on the approved host, then run sudo -n bash install-first.sh IMAGE. It refuses an existing target and occupied port. Data belongs to UID/GID 1000; runtime.env is root-only and receives a new random API key without printing it. Do not copy local user secrets or model configuration. No Docker socket or host networking. No changes to Caddy, firewall or unrelated containers.

## Acceptance

Wait for /health HTTP 200. Check /v1/models without auth and with wrong token returns 401, valid key returns 200; load key into process memory, never command-line args or logs. Confirm 127.0.0.1:8642 binding, 1GiB memory / 1536MiB combined memory-and-swap / 1CPU / 256 PID limits, no OOM/restart loops and healthy existing containers. Host swap capacity is managed separately: the 150.158.83.70 instance has approximately 4GiB swap, which does not increase container limits automatically. Restart this project's service and repeat checks; verify the API key and a non-secret data marker persist. Record image digest, source/build/deployment config SHA, evidence and untested model calls. pnpm synchronization warnings require recording and follow-up, not silent suppression.

## Upgrade, failure and rollback

First-install is intentionally not an upgrade command: a second invocation must stop. Upgrades require separate approval, verified new digest and prior digest record. Stop this project's service, take an access-restricted consistent backup of data/runtime.env/.env/compose.yml, then replace the digest and start. Never print resolved compose config containing secrets. Failed first install: docker compose stop from the target directory, retain all data/logs for diagnosis. Upgrade rollback: stop, restore the approved matching data/config backup and prior digest, start and repeat acceptance. No down -v, prune or broad deletion. A written procedure is not evidence of a rollback drill.

## Access and uninstall

Optional existing-image HTTPS dashboard: follow [DASHBOARD.md](DASHBOARD.md) and append `compose.dashboard.yml` to the instance's existing overrides. Use native password authentication, no Caddy Basic Auth, and retain Gateway `/health` and `/v1/*` routes. This requires explicit host/config-change approval and does not authorize image rebuilding.

## Explicit optional offline node

Only after approval for failed registry delivery, use offline_bundle.py pack with a verified delivery directory. Follow OFFLINE.md for outer/inner checksums and provenance checks, then install-offline.sh on the approved host. Do not invoke this automatically from build-image.sh, publish-image.sh or install-first.sh. Save/load image ID, registry digest and archive hash are different identities. Stop any prior pull/waiting installer before switching. The package excludes all runtime secrets/data; no global Docker changes. Offline transfer does not prove model connectivity or replace deployment/rollback acceptance.

API is private loopback; use an approved SSH tunnel for clients until HTTPS/domain exposure is approved. Model credentials must be separately injected securely before business acceptance. Uninstall requires explicit approval: stop/remove only this Compose project's containers/network, retain data and keys by default. Do not remove backups or other Docker assets.

Status: this file is versioned deployment guidance; actual Hermes discovery/loading, model tests and rollback exercise remain unverified until evidence is recorded.
