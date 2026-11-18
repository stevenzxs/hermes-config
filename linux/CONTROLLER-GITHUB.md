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

### Dedicated Git SSH transport (2026-11-18)

The owner approved an independent account authentication key for Git over
`ssh.github.com:443`. HTTPS Git transfer timed out while GitHub API calls worked.
The public key was added manually by the owner; no OAuth public-key admin scope
was granted. Private key remains only on 150 in
`/opt/data/delivery-controller/ssh/github_ed25519`.

Public fingerprint: `SHA256:8xTx9NHZt1p8rSSYxEWKKar1UVVGCO3rFeheBI3+hrg`.
The dedicated config is `/opt/data/delivery-controller/ssh/config`, host alias
`github-hermes`. Its known_hosts pins the Ed25519 host key obtained from GitHub's
HTTPS `/meta` API and matched against SSH443; strict host checking is enabled.
Existing SSH configurations and knowledgebase credentials are not changed.

Git checkout locations are `/opt/data/workspace/delivery/{hermes-agent,hermes-config,hermes-android}`.
Each Git repository uses its own `core.sshCommand` pointing at that config.
Do not print or copy the private key. Revoke by removing this public key in
GitHub settings; retain unrelated account keys and SSH settings.

SSH identity returned `Hi stevenzxs!`; configuration checkout succeeded. Source
and Android shallow blob-filtered fetches resolved the expected main SHAs, but
full source checkout timed out fetching blobs. A fetched HEAD does not prove
an editable working tree. Preserve incomplete directories and investigate
specific owned subprocesses/locks before retrying; do not delete broad paths.

Android main currently resolves the upstream baseline 6a880cdb, whereas the
existing signed workflow binds 187fc049. Do not switch the workflow to main
without preserving independent app identity and signing verification.

CLI execution as UID1000 verified. GitHub authorization, workflow dispatch,
same-version release, task persistence, Android-origin execution and 115 runtime
acceptance are separate gates; bootstrap alone does not prove them.
