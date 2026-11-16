# Cloud knowledgebase integration

Optional extension for Hermes v0.23.1 source 3b421578588243f920886e6fe79a6faa87ea026e.
No rebuild. GitHub stevenzxs/knowledgebase default branch is the shared authority. Cloud and
Windows checkouts are working copies; uncommitted/unmerged changes are not approved shared policy.

Run all five Compose files (compose.yml, compose.offline.yml, compose.caddy.yml,
compose.kimi.yml, compose.knowledgebase.yml). Dedicated host checkout /opt/stevenzxs-knowledgebase
mounts rw at /opt/data/workspace/knowledgebase (inside the native file-tool sandbox). Tools/auth directories mount ro separately. terminal.cwd is
/opt/data/workspace, containing the reviewed KNOWLEDGEBASE-AGENTS.md fragment as AGENTS.md;
preserve pre-existing instructions. Verify native prompt loader AND a new actual Hermes request.

## Authorization (owner action required)

Create an expiring fine-grained PAT restricted to stevenzxs/knowledgebase, Contents read/write
and Pull requests read/write. No other repositories, Actions, administration or bypass access.
Use a dedicated non-admin automation account if owner tokens can bypass rules. Never reuse a
general GitHub account token or CloudMeet credentials. Install its value out of band in
/opt/stevenzxs-hermes/knowledgebase-auth/token (UID1000, mode600, parent700). Do not pass via
command arguments, Git URLs, env or logs. Revoke/rotate in GitHub, replace atomically and recheck.

Owner decision, 2026-11-16: GitHub branch rules are not required for this integration.
No protection attestation is required or fabricated. Keep hermes/* branch-only submission,
PR review and no auto-merge as client policy. This is NOT server-enforced protection: a token
with Contents write can potentially write the default branch through other tools. Repository
scope must be configured by the owner; an API success cannot prove absence of broader access.
Missing token still blocks submission. Tools read secrets but never output their value.

Git uses the supplied credential helper only for this checkout; credentials go over HTTPS solely
to github.com/stevenzxs/knowledgebase. PR REST calls solely to api.github.com for that repository.
Set git user.name/email to an explicit automation attribution, never impersonate a human.

## Operation and rollback

Work on hermes/<task>, inspect/stage specific files, commit, then run knowledgebase_git.py submit
"title". No auto-merge. Readonly API status reports authentication presence only, not scope proof.
Secrets scans/review are operator responsibilities; never include runtime.env, auth files or model keys.
SSH/GitHub failure stops the operation; do not repeatedly retry or switch credentials/accounts.

Remove the knowledgebase Compose extension and restore the previous terminal.cwd/instruction backup
to disconnect. Retain checkout and pending commits. Revoke token separately. Do not delete data,
reset dirty checkouts or overwrite Windows changes. Acceptance includes read/write as UID1000,
native context load, actual agent read, health/auth and, only when authorized, branch push/PR checks.
