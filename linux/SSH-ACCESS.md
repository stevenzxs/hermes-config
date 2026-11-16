# Dedicated cloud Hermes SSH access

Authorized target: root@115.190.243.21, from Hermes host 150.158.83.70.
Command inside Hermes:

    /usr/bin/ssh -F /opt/data/ssh-access/config hermes-root-115 <command>

Dedicated Ed25519 key generated on the Hermes host, persisted in the existing data volume
under ssh-access (directory700, private key600, UID1000). No private material enters this repo.
Explicit config supports root or UID1000 callers without changing global SSH settings.
Host key pinned from the already authenticated target connection:
SHA256:FdKL7pcSAkJdJR52+Aa3z6MvtrMKhhoz4H+eDNiZ01w (Ed25519).

Target authorized_keys appends only this public key with restrict,from="150.158.83.70".
Existing entries retained with a pre-change backup; no sshd configuration changes/restart.
No forwarding/PTY. This is unrestricted root command execution, not a sandbox; possession
of this key from the allowed source grants root. Keep the API key restricted and approve
destructive/production work separately. Never print/read private-key values into model context.

Acceptance: execute id remotely from the running Hermes container as UID1000; expect uid0.
Revoke by removing only the matching public-key entry at the target, then archive/rotate the
dedicated key securely. Never restore the whole old authorized_keys over subsequent changes.
If source IP/host key changes, verify the new identity before updating; never use
StrictHostKeyChecking=no. Workspace AGENTS.md carries the command for new conversations;
preserve its SSH section when later updating the knowledgebase instruction fragment.
