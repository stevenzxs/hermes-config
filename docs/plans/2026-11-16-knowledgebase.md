# Cloud knowledgebase write access plan

Approved scope: stevenzxs/knowledgebase is the shared authoritative repository. Preserve local dirty files. Give Hermes a dedicated writable checkout, instructions and branch/PR delivery entrypoint. Do not borrow existing account/other-project credentials; do not alter other containers or Caddy.

1. Inspect remote HEAD, local changes, runtime and project-context loader. Verify tooling and scoped credential availability.
2. Add optional Compose mount and instruction fragment, credential helper and PR utility in config repo. Use only a repository-scoped token file, no credentials in Git URLs/env/logs. Reject main/master and unexpected origin on submission. Do not auto-merge.
3. Clone a fixed remote commit into a new dedicated host directory; checkout a hermes/ branch. Mount rw. Set terminal.cwd using the native config writer and verify native context loader finds workspace instructions.
4. Validate utilities with focused unit tests and missing-credential failure. Commit/push configuration. Deploy only Hermes using the existing offline/caddy/kimi extensions plus knowledgebase extension.
5. Verify file access as runtime UID, prompt loading, health/auth and model access. Exercise actual Hermes read on a new session. GitHub branch push/PR/protection checks remain blocked unless scoped authorization exists. Never claim documentation or client hooks are GitHub-enforced protection.
6. Record exact config/repository SHAs and results in the unique ledger. Cloud proposals are pending until merged; local D:/knowledgebase changes require normal review and synchronization, never forced reset.

Stop: missing authorization, foreign credentials, dirty-target overwrite, failed health. No builds or service changes beyond Hermes.
