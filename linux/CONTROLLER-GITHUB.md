# 150 Hermes GitHub authentication bootstrap

Controller: 150.158.83.70; container: stevenzxs-hermes-gateway-1, UID1000.
Persistent CLI: `/opt/data/delivery-controller/gh`; isolated authentication:
`/opt/data/delivery-controller/auth` (700). Never reuse knowledgebase credentials.

Official CLI 2.105.0 download timed out during bootstrap. The explicitly selected
alternative is Ubuntu noble-updates gh 2.45.0-1ubuntu0.3, package SHA256
`200baf40742053089d945c83f9f1f5f57124b801d86af89da5ead9eeac90f4a0`.
`install-controller-gh-ubuntu.sh` downloads and verifies the package, extracts
only the CLI into the data volume, and does not rebuild/restart the controller.
The CLI is invoked by absolute path; global PATH is not changed.

## One-time human authorization

From an interactive terminal on 150:

```bash
sudo docker exec -it -u 1000 stevenzxs-hermes-gateway-1 \
  /opt/data/delivery-controller/gh auth login \
  --hostname github.com --git-protocol https --web \
  --scopes repo,workflow,read:packages
```

Log into the intended stevenzxs account in the browser. This OAuth login can
grant account-wide repository access, not a repository-scoped identity. If that
scope is unsuitable, stop and provision a separately approved limited credential.
No token is to be pasted into chat. The headless CLI may store the OAuth token
as plaintext in the restricted auth directory because no keyring is available;
do not commit/copy this directory into images, artifacts, or logs.

After login, inspect account identity and repository permissions without printing
the token. Configure Git credentials only for the reviewed project repositories;
do not run global auth setup that would replace knowledgebase authentication.
Do not use `gh auth token` in agent-visible output.

Actions uses its own minimal GITHUB_TOKEN for GHCR publication; no controller
write:packages token is required by default. Package Actions write access must
be verified for the actual hermes-config repository before publication.

## Status

CLI execution as UID1000 verified. GitHub authorization, workflow dispatch,
same-version release, task persistence, Android-origin execution and 115 runtime
acceptance are separate gates; bootstrap alone does not prove them.
