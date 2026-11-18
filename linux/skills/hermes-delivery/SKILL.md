---
name: hermes-delivery
description: Android对话请求修改Hermes服务端、推送main、联合构建发布镜像和同版本APK、部署115或查询交付任务进度时使用。未完成的发布入口不得伪报可用。
---

# Android conversation driven delivery

## Current readiness gate

Bootstrap only. Joint release workflow and online deploy executor are NOT yet
implemented. Do not invoke upstream workflows or local builds as a substitute.
Explain this blocker if asked to release now. This Skill is not evidence that
the complete flow works or that it has been installed/loaded in the controller.

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
concrete change request, task ID, release version, Android versionCode, target,
and scope approval. Existing authorization is not permission for unrelated
changes, destructive operations, firewall/TLS changes or secret redistribution.

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
version policy, real APK checks, online deploy, runtime model/entrypoint and
Android API approval/reconnect behavior still require implementation/verification.
