---
name: hermes-delivery
description: Android对话请求修改Hermes服务端、推送main、联合构建发布镜像和同版本APK、部署115或查询交付任务进度时使用。未完成的发布入口不得伪报可用。
---

# Android conversation driven delivery

## Current readiness gate

Joint release workflow (`.github/workflows/hermes-joint-release.yml`) now auto-allocates
joint revisions from the durable ledger (`linux/revision_ledger.py`) before building.
Manual version/android_code inputs are removed; only `source_sha`, `android_sha`, and
`task_id` are required. Deployment target and mode (first-install/upgrade) are recorded
separately via `delivery_task.py set-deployment` after publication, never inferred from
build inputs. The 150 orchestrator (`linux/joint_release.py`) tracks the Run; deployment
uses the offline bundle with explicit IP/mode selection.

Usage after explicit owner confirmation of fixed SHAs:
`python3 linux/joint_release.py prepare --task-id <id> --config-sha <main-sha>
--source-sha <sha> --android-sha <sha>`, then `dispatch --task-id <id>`, poll
`status --task-id <id>`, and only after artifact/digest verification record
`verify`. Deployment requires explicit target/mode: `python3 linux/delivery_task.py
set-deployment <id> --json '{"target":"<ip>","mode":"upgrade"}'` before any
deploy action. Reusing a task ID with the same request returns the record; never
dispatch twice for an uncertain outcome.

## Approved architecture

- Execute as the Hermes agent on 150; Android is the command and status UI.
- GitHub identity stevenzxs. CLI `/opt/data/delivery-controller/gh`.
- Git SSH config `/opt/data/delivery-controller/ssh/config`, alias github-hermes.
- Repositories `/opt/data/workspace/delivery/{hermes-agent,hermes-config,hermes-android}`.
- User permits reviewed ordinary main pushes, never force pushes/deletions.
- Build only through reviewed hermes-config Actions with fixed three-repository
  SHAs; publish service image and signed Android APK under one release version.
- Deploy only service image, by verified digest, to 115.190.243.21 using
  `/usr/bin/ssh -F /opt/data/ssh-access/config hermes-root-115`.
- Do not upgrade 150 controller or install Android APK automatically.
- Never print secrets, upload runtime data, borrow knowledgebase credentials,
  change signing identity, disable TLS/host checks, or build on 115.

## Task contract and recovery

Read knowledgebase standards/ledger and repository AGENTS before edits. Require
concrete change request, task ID, fixed source/config SHAs, and scope approval.
Deployment target and mode (first-install/upgrade) are explicitly recorded after
publication, not in the build request. Existing authorization is not permission for
unrelated changes, destructive operations, firewall/TLS changes or secret redistribution.

Use `linux/delivery_task.py` from the reviewed config checkout to save non-secret
checkpoints under `/opt/data/delivery-controller/tasks`. Reusing a task ID with
the same request returns the record; a different request is rejected. A task
lock fails closed; investigate owner process before recovering a stale lock.
This recorder validates evidence shape, not evidence truth, and does NOT make
external dispatch/publish/deploy atomic. On uncertain dispatch outcome query
existing runs first; never blindly repeat. Do not record tokens in request or
evidence, which may be displayed when querying status.

If Android HTTP connection closes, inspect recorded Run ID and remote state.
Do not infer cancellation/success, create a duplicate release, or restart 150.
Report separately source push, Actions final conclusion, artifact verification,
GHCR publication, 115 install, health/auth/persistence/business and rollback.
Require actual Android-origin and model-driven tool evidence for end-to-end
acceptance; OpenCode commands are preparation only.

## Known blockers

150 SSH443 authenticated and config cloned; source checkout blob download timed
out, left an incomplete worktree and index lock. Do not commit apparent deletion
entries. Android main 6a880cdb differs from signed independent source 187fc049;
preserve package/signing identity before planning main migration. Joint Actions,
real APK checks, online deploy, runtime model/entrypoint and Android API
approval/reconnect behavior still require implementation/verification. Revision
allocation ledger must be initialized on the controller before first real dispatch.
