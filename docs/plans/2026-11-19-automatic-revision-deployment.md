# Automatic joint revisions and explicit deployment selection

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allocate persistent automatic joint revisions, publish verified server/Android artifacts, then require the operator's server IP and first-install/upgrade choice before offline deployment.

**Architecture:** Retain the joint workflow. Allocate before product tests on a restricted, dedicated version-control runner using a pre-initialized SQLite append-only ledger outside Git; use an independent backup/high-water witness and fail closed on missing/stale state. Hosted runners build products using the parent's immutable allocation. Deployment selection is a separate persisted gate, never inferred from historical targets. Offline upgrades preserve the complete live Compose stack, data and secrets, with consistent backup and rollback.

**Tech Stack:** Python standard library, SQLite, GitHub Actions, Flutter/Gradle, Docker Compose, authenticated SSH.

## Contract

- Route: plan_first. Approved 2026-11-19 by user: confirm and execute.
- Server baseline 0.23.1; Android baseline 4.0.0/3049. Both share N.
- No manual per-batch revision/version inputs. Failed/cancelled allocations remain consumed; reruns reuse the run ID allocation and record attempts.
- New namespace initialization is explicit and requires historical inspection; missing state never resets to r1.
- Product source repair remains fa4818f31078f41f9876173fbeff7b6cb8814eec. Android input initially 83be01999c14c3e92a1ec6c56b045b6a16eb8a11; any necessary native identity changes require a new tested, committed SHA.
- No local/target product compilation. Local configuration/unit tests are not cloud delivery acceptance.
- Preserve signatures, package identity, Kimi settings, HTTPS, authentication, persistent data and unrelated services.
- Stop: unavailable signing identity/runner/backup/credentials; inconsistent runtime state; unexpected dirty files; invalid or unverified artifacts; absent deployment IP/mode approval.
- No subagents. Work sequentially with independent read-only tool calls in parallel.

## Task 1: Durable allocation and recovery tests

Files: `linux/revision_versions.py`, new `linux/revision_ledger.py`, `linux/test_revision_ledger.py`.

1. Add behavioral tests for explicit initialization, missing/stale/corrupt ledger refusal, input-bound reruns, attempts, concurrent allocations, append-only enforcement and independent backup recovery.
2. Run `python -B -m unittest discover -s linux -p 'test_revision_ledger.py'`; confirm failures describe absent behavior.
3. Implement transactional allocation, immutable policy/request binding, backup/high-water validation and CLI. Remove implicit initialization from the old helper CLI.
4. Run focused then complete `python -B -m unittest discover -s linux -p 'test_*.py'`.
5. Commit this tested boundary.

## Task 2: Native Android revision identity and joint workflow

Files: `android/` version-commit utility/tests; Android native verifier/tests if required; `.github/workflows/hermes-joint-release.yml`, `.github/workflows/hermes-android.yml`, `linux/release_contract.py`, orchestrator and tests.

1. Test derived identities, pinned input/derived publication commits, overflow and APK checks without accepting unsigned/wrong signer artifacts.
2. Implement committed revision metadata before Flutter build, propagate allocation to native Gradle and APK verification; no arbitrary workspace override.
3. Restrict reusable Android entry to parent allocation; remove standalone manual-version bypass.
4. Allocate first, propagate server install stamp/runtime version and image tags, retain smoke/identity evidence as files, publish only after verification. Bind all source/config/version identities in manifests.
5. Test workflow contracts, run actionlint/Bash checks and configuration unit tests; commit.

## Task 3: Explicit deployment gate

Files: `linux/delivery_task.py`, `linux/joint_release.py`, dedicated deployment-selection tests, maintained Skill.

1. Red tests: build task has no target; published task cannot deploy before recording a valid IP and explicit `first-install`/`upgrade` choice; choice cannot silently drift.
2. Persist selection separately from immutable build request. Reject target/mode mismatch with actual state, no default 115/150.
3. Exercise request/dispatch ambiguity recovery so uncertain dispatch is never repeated.
4. Run full configuration tests; commit.

## Task 4: Offline artifact and upgrade execution

Files: `linux/offline_bundle.py`, `linux/install-offline.sh`, new upgrade executor/tests, `linux/OFFLINE.md`, `linux/SKILL.md`.

1. Red tests for source identity derived from verified evidence, complete checksums, exported image identity, target/mode gate, existing-stack preservation and backup/rollback failures.
2. Keep first-install refusal to overwrite. New upgrade path must use the complete existing Compose files/project, stop gateway only, create root-only consistent backup outside data, update only image selection and restart gateway; do not replace runtime secrets.
3. Verify internal source/version/config identity before activation and health/auth/persistence afterward. Preserve failure evidence; rollback restores paired backup, never deletes broad paths.
4. Run fixture-based command execution tests, shell syntax/actionlint, sensitive diff review and full tests; commit.

## Task 5: Controlled delivery and audit

1. Verify dedicated runner isolation, ledger historical bootstrap, independent recovery and signing Secrets; infrastructure existence is not proof of acceptance.
2. Merge/push reviewed configuration, pin final SHAs. Run Hermes-controlled preflight and one joint Actions dispatch; wait for final result, retrieve artifacts, verify API/archive and content digests.
3. Report publication results, then ask user for server IP and deployment mode. Do not proceed before the new selection.
4. When selected, export verified digest without rebuilding, verify transport and install/upgrade, run separate business checks.
5. Update `D:/knowledgebase/audits/project-register.md` on a fresh knowledgebase task branch, preserve concurrent work, merge/push per knowledgebase policy.

## Verified starting point

- Isolated config worktree: `C:/Users/ZL/AppData/Local/Temp/opencode/hermes-delivery-revision-20261119`.
- Branch `feat/automatic-revision-deployment-gate`, base config `12fa49919cd080f49cc815de07899988102cfefb`.
- Baseline Linux configuration tests: 38 passed (2026-11-19). No build dispatched and no target mutation.

## Checkpoints

- Current: Task 1, test-first persistent allocator.
- Pending: workflow/native wiring, explicit deployment gate, offline upgrade, infrastructure acceptance, cloud build/publication, deployment question.
