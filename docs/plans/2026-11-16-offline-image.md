# Offline image delivery Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an explicitly invoked offline Docker bundle without changing normal registry delivery.

**Architecture:** Export the already verified image via docker save, package deployment files and a provenance manifest, and validate archive SHA256 plus image ID/source identity before startup. Registry digest and Docker image ID are separate identities. Runtime secrets are generated on the target, never bundled.

**Tech Stack:** Python standard library, Docker CLI, Bash, Compose.

## Approved design

User confirmed the optional node: registry pull remains normal; only explicitly approved network-blocked delivery uses offline packaging, SSH transfer, verification/load/install. Source remains 3b421578588243f920886e6fe79a6faa87ea026e. Include image.tar.gz, installer, Compose, instructions, manifest and SHA256SUMS. Keep original source/build config/packaging config SHAs, published digest and image ID. No credentials/data; no global Docker changes.

## Task 1: Verification contract

Create linux/offline_bundle.py and linux/test_offline_bundle.py. Test verification of complete bundles and rejection of modified files, missing checksum coverage, unsafe filenames and invalid image identities. Run `python -m unittest discover -s linux -p test_offline_bundle.py -v`; demonstrate failures before implementing verification.

## Task 2: Optional packaging and install

Implement `python linux/offline_bundle.py pack DELIVERY OUTPUT` using subprocess argument lists and docker save piped to gzip, never shell interpolation. Refuse existing output. Verify build identity and gateway evidence, compare registry digest to local RepoDigests and image labels before export. Generate manifest and checksums; package only an allowlisted set of files. Installer verifies bundle before docker load, then image ID/internal stamp, and refuses existing deployments. Compose uses a local verified tag with pull_policy never. Test missing/corrupt inputs and `bash -n`; no cloud rebuild.

## Task 3: Governance and execution

Update linux/SKILL.md and knowledgebase standards/README/ledger to describe the separately invoked node, approval, identity/secret/rollback boundaries. Commit/push configuration before creating the real package. Produce package and SHA256 in D:/hermes-delivery, verify after SSH transfer, stop old pull and waiter before installing. Test API auth/health, persistence and limits. Record deployment config SHA distinct from image build SHA. Report model and rollback tests as unverified unless actually executed.
