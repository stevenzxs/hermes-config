# Cloud knowledgebase workspace

Shared authority: https://github.com/stevenzxs/knowledgebase (merged default branch).
Writable working copy: /opt/data/workspace/knowledgebase. Pending branch edits are proposals, not approved policy.

Before project development, builds, deployment or acceptance, read /opt/data/workspace/knowledgebase/README.md,
standards/project-delivery.md and the relevant project entry in audits/project-register.md.
Record the checkout commit and dirty state; read other documents only as needed. Report unavailable
or conflicting rules. Never self-approve governance exceptions or weaken policy to pass a gate.

Use a new conversation after changing governing context. Keep current conversation prompt stable.
Project operations still require the user's approval. Never treat a started process as acceptance.

For knowledgebase edits: git -C /opt/data/workspace/knowledgebase status; inspect differences; work only on
hermes/<task> branches. Do not checkout/reset over dirty changes. Do not push main/master, force
push, delete branches or auto-merge. Review the staged diff for credentials, personal data and
unsupported acceptance claims. Stage explicit paths, not git add -A.

The scoped publishing tool is /opt/knowledgebase-tools/knowledgebase_git.py:
  python3 /opt/knowledgebase-tools/knowledgebase_git.py status
  python3 /opt/knowledgebase-tools/knowledgebase_git.py submit "PR title"
Commit reviewed changes before submit. It pushes the current branch and creates/reuses a PR,
never merges. A missing token blocks submission. The owner declined GitHub branch rules on
2026-11-16: branch/PR restrictions are client policy, NOT server-enforced protection. Do not
read/display credential files or seek credentials belonging to another repository/account.

Store runtime evidence outside the repository until reviewed. Do not claim the unique audit
ledger is updated upstream until the PR is merged. Other working copies (including Windows)
must inspect their dirty state before normal synchronization; never overwrite them.
